"""
Workflows 层 - 应收开票申请步骤（LK15 ~ LK16）

  record_invoice_batch       发起应收开票批次审批（多步复合）
  record_invoice_batch_audit 审核生成开票申请

LK15 = LK14 + 发起应收开票批次审批。
LK16 = LK15 + 审核生成开票申请。
"""
import json
import time as _time
from typing import Any, Dict, List

import allure

from api.order import AuditApi
from api.receive.receive_apply_api import InvoiceBatchApi
from data.receive import (
    INVOICE_USD_TURN_ON,
    INVOICE_MERGE_CNY_NO,
    INVOICE_RATE_TYPE_SPECIFY,
    INVOICE_DEFAULT_RATE,
    INVOICE_DEFAULT_FORM,
    INVOICE_DEFAULT_TYPE,
    INVOICE_DEFAULT_ITEM,
    INVOICE_FAST_REMARK,
    INVOICE_APPLY_SIMPLE,
    INVOICE_PURCHASER_TAX_NUMBER,
    INVOICE_REQUIRE_OTHER,
    INVOICE_DEFAULT_REMARK,
)
from workflows.order.audit_steps import _loop_approve_until_done


def record_invoice_batch(
    bl_no: str,
    put_settle_object_id: str,
    main_id: str,
    put_settle_object: str,
    main_name: str,
    order_fee_real_ids: List[str],
    order_sub_ids: List[str],
    order_sub_customer_ids: List[str],
) -> Dict[str, Any]:
    """
    发起应收开票批次审批

    流程：financePutList → monthExchangeRate → getSellInfo → batchOrderEdit(submit) → batchpage(verify)

    Args:
        bl_no                   : 提单号
        put_settle_object_id    : 托单结算对象ID
        main_id                : 主体ID
        put_settle_object      : 托单结算对象名称
        main_name              : 主体名称
        order_fee_real_ids     : 费用ID列表（来自 financePutList amount_list）
        order_sub_ids          : 子订单ID列表
        order_sub_customer_ids : 子订单客户ID列表

    Returns:
        {
            'put_list_resp' / 'put_list_data' / 'put_list_data_records': ...,
            'rate_resp' / 'rate_data' / 'exchange_rate': ...,
            'sell_info_resp' / 'sell_info_data' / 'seller_list': ...,
            'submit_resp' / 'submit_data' / 'batch_id' / 'batch_no': ...,
            'page_resp' / 'page_data': ...,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {"bl_no": bl_no, "steps": [], "main_id": main_id, "put_settle_object": put_settle_object}

    # Step 1: financePutList（开票模式）查询应收款项
    with allure.step('查询应收款项列表（financePutList 开票模式）'):
        put_list_resp = InvoiceBatchApi.query_finance_put_list_for_invoice(
            bl_no=bl_no,
            put_settle_object_id=put_settle_object_id,
            main_id=main_id,
        )
        put_list_data = put_list_resp.json()
        result['put_list_resp'] = put_list_resp
        result['put_list_data'] = put_list_data
        result['steps'].append({
            'name': '查询应收款项列表（开票）',
            'code': put_list_data.get('code'),
            'msg': put_list_data.get('msg'),
        })

    # Step 2: monthExchangeRate 获取汇率
    with allure.step('获取汇率（monthExchangeRate）'):
        rate_resp = InvoiceBatchApi.get_month_exchange_rate(main_id=main_id)
        rate_data = rate_resp.json()
        result['rate_resp'] = rate_resp
        result['rate_data'] = rate_data
        exchange_rate = rate_data.get('data', {}).get('rate', '7')
        if not exchange_rate:
            exchange_rate = str(INVOICE_DEFAULT_RATE)
        result['exchange_rate'] = exchange_rate
        result['steps'].append({
            'name': '获取汇率',
            'code': rate_data.get('code'),
            'msg': rate_data.get('msg'),
            'rate': exchange_rate,
        })

    # Step 3: getSellInfo 获取开票方信息（需要先有 purchaser 信息）
    # 从 put_list_data 中提取 amount_list 构建 fee_usd_total 和 order_fee_real_ids
    put_records = put_list_data.get('data', {}).get('data', []) or []
    fee_usd_total = "0.00"
    real_fee_ids = []
    real_order_sub_ids = []
    real_order_sub_customer_ids = []
    if put_records:
        record = put_records[0]
        amount_list = record.get('amount_list', []) or []
        total = sum(float(item.get('real_amount', 0)) for item in amount_list)
        fee_usd_total = f"{total:.2f}"
        real_fee_ids = [str(item.get('order_fee_real_id', '')) for item in amount_list if item.get('order_fee_real_id')]
        real_order_sub_id = str(record.get('order_sub_id', ''))
        real_order_sub_ids = [real_order_sub_id] if real_order_sub_id else order_sub_ids
        real_order_sub_customer_id = str(record.get('customer_id', ''))
        real_order_sub_customer_ids = [real_order_sub_customer_id] if real_order_sub_customer_id else order_sub_customer_ids
        # 确保 put_settle_object 和 main_name 与查询结果一致
        if record.get('put_settle_object'):
            put_settle_object = record.get('put_settle_object', put_settle_object)
        if record.get('main_name'):
            main_name = record.get('main_name', main_name)

    if not real_fee_ids:
        raise AssertionError(f'financePutList 响应中 amount_list 为空，无法发起应收开票批次: {put_list_data}')

    result['order_info_records'] = [
        {
            'order_fee_real_id': item.get('order_fee_real_id'),
            'book_customer_id': item.get('book_customer_id'),
            'real_amount': item.get('real_amount'),
        }
        for item in amount_list
    ]

    with allure.step('获取开票方信息（getSellInfo）'):
        sell_info_resp = InvoiceBatchApi.get_sell_info(
            put_settle_object_id=put_settle_object_id,
            put_settle_object=put_settle_object,
            main_id=main_id,
            main_name_cn=main_name,
            order_fee_real_ids=real_fee_ids,
            order_sub_ids=real_order_sub_ids,
            sys_rate=exchange_rate,
            usd_is_turn=INVOICE_USD_TURN_ON,
        )
        sell_info_data = sell_info_resp.json()
        result['sell_info_resp'] = sell_info_resp
        result['sell_info_data'] = sell_info_data
        seller_list = sell_info_data.get('data', []) or []
        result['seller_list'] = seller_list
        result['steps'].append({
            'name': '获取开票方信息',
            'code': sell_info_data.get('code'),
            'msg': sell_info_data.get('msg'),
            'seller_count': len(seller_list),
        })

    # Step 4: batchOrderEdit(submit) 正式提交开票批次
    # 构建 usd_require：使用卖家信息（seller_id）和 purchaser 信息
    usd_seller = seller_list[0] if seller_list else {}
    usd_purchaser = seller_list[1] if len(seller_list) > 1 else seller_list[0] if seller_list else {}

    usd_require = {
        "fast_remark": INVOICE_FAST_REMARK,
        "currency": "CNY",
        "amount_total_usd": float(fee_usd_total) if fee_usd_total else 0,
        "amount_total_cny": "",
        "rate": float(exchange_rate) if exchange_rate else 0,
        "turn_amount_total_cny": f"{float(fee_usd_total) * float(exchange_rate):.2f}" if fee_usd_total and exchange_rate else "0.00",
        "turn_amount_total_usd": "",
        "turn_amount_total": f"{float(fee_usd_total) * float(exchange_rate):.2f}" if fee_usd_total and exchange_rate else "0.00",
        "invoice_apply_name": f"{main_name} + {put_settle_object} + 2026-05 + USD {fee_usd_total}",
        "invoice_apply_simple": INVOICE_APPLY_SIMPLE,
        "invoice_form": INVOICE_DEFAULT_FORM,
        "invoice_type": INVOICE_DEFAULT_TYPE,
        "purchaser_id": str(put_settle_object_id),
        "purchaser_head_cn": put_settle_object,
        "purchaser_tax_number": usd_purchaser.get('identifier_no', ''),
        "seller_id": usd_seller.get('order_main_finance_id', ''),
        "seller_name": usd_seller.get('bank_account', ''),
        "bank_account": "",
        "seller_info": json.dumps(usd_seller),
        "invoice_items": "",
        "invoice_rate_type": "",
        "invoice_rate": "",
        "require_other": INVOICE_REQUIRE_OTHER,
        "remark": INVOICE_DEFAULT_REMARK,
        "rate_list": [
            {
                "cost_name": item.get('fee_real_name', ''),
                "fee_real_no": item.get('fee_real_no', ''),
                "cost_no": item.get('cost_no', ''),
                "invoice_rate": str(INVOICE_DEFAULT_RATE),
                "real_amount": item.get('real_amount', '0.00'),
                "currency": item.get('currency', 'USD'),
                "invoice_item": INVOICE_DEFAULT_ITEM,
                "amount_error_flag": False,
                "rowIndex": idx,
                "invoice_item_name": "国际货物运输代理海运费",
            }
            for idx, item in enumerate(put_records[0].get('amount_list', []) or [])
        ] if put_records and put_records[0].get('amount_list') else [],
        "purchaser_name": put_settle_object,
        "fund_name": usd_seller.get('fund_name', ''),
    }
    cny_require = {
        "fast_remark": INVOICE_FAST_REMARK,
        "currency": "",
        "amount_total_usd": "",
        "amount_total_cny": "",
        "rate": "",
        "turn_amount_total_cny": "",
        "turn_amount_total_usd": "",
        "turn_amount_total": "",
        "invoice_apply_name": "",
        "invoice_apply_simple": INVOICE_APPLY_SIMPLE,
        "invoice_form": "",
        "invoice_type": "",
        "purchaser_id": "",
        "purchaser_head_cn": "",
        "purchaser_tax_number": "",
        "seller_id": "",
        "seller_name": "",
        "bank_account": "",
        "seller_info": "",
        "invoice_items": "",
        "invoice_rate_type": "",
        "invoice_rate": "",
        "require_other": "",
        "remark": INVOICE_DEFAULT_REMARK,
        "rate_list": [],
    }

    with allure.step('提交应收开票批次申请（batchOrderEdit submit）'):
        submit_resp = InvoiceBatchApi.batch_order_edit(
            action="submit",
            put_settle_object_id=put_settle_object_id,
            put_settle_object=put_settle_object,
            main_id=main_id,
            main_name_cn=main_name,
            order_fee_real_ids=real_fee_ids,
            order_sub_ids=real_order_sub_ids,
            order_sub_customer_ids=real_order_sub_customer_ids,
            usd_require=usd_require,
            cny_require=cny_require,
            sys_rate=exchange_rate,
            appoint_rate=str(INVOICE_DEFAULT_RATE),
            cost_usd=fee_usd_total,
            cost_cny="0.00",
            rate_type=INVOICE_RATE_TYPE_SPECIFY,
            audit_msg={"title": "开票批次ID", "code": None, "msgs": ["应收开票批次申请"]},
            select_node_user=[],
            fee_currency="USD",
        )
        invoice_submit_data = submit_resp.json()
        result['invoice_submit_resp'] = submit_resp
        result['invoice_submit_data'] = invoice_submit_data
        result['steps'].append({
            'name': '提交应收开票批次申请',
            'code': invoice_submit_data.get('code'),
            'msg': invoice_submit_data.get('msg'),
        })

    # Step 5: batchpage 验证批次创建
    with allure.step('验证应收开票批次（batchpage）'):
        page_resp = InvoiceBatchApi.query_batch_page(bl_no=bl_no)
        page_data = page_resp.json()
        result['page_resp'] = page_resp
        result['page_data'] = page_data
        result['steps'].append({
            'name': '验证应收开票批次',
            'code': page_data.get('code'),
            'msg': page_data.get('msg'),
        })

        # 从批次列表中提取最新一条的 batch_id
        records = page_data.get("data", {}).get("data", []) or []
        result['batch_id'] = records[0].get("receive_invoice_batch_id", "") if records else ""

    return result


def record_invoice_batch_audit(
    batch_id: str,
) -> Dict[str, Any]:
    """
    审核生成开票申请（循环审批通过，直至审批流结束）

    Args:
        batch_id: 开票批次ID（来自 record_invoice_batch 响应中的 batch_id）

    Returns:
        {
            'batch_id': str,
            'approve_results': [...],
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "batch_id": batch_id,
        "steps": [],
    }

    # 循环审批直到结束
    with allure.step('循环审批通过: invoiceBatchApplication'):
        approve_results = _loop_approve_until_done(
            audit_type='invoiceBatchApplication',
            relation_id=batch_id,
            active_tab='examine_wait',
            query_step_name='查询应收开票批次审批ID',
            approve_step_name='审批通过应收开票批次',
        )
        result['approve_results'] = approve_results

        if not approve_results:
            raise AssertionError(
                f'未查到开票批次审批记录，batch_id={batch_id}'
            )

        first = approve_results[0]
        result['audit_query_resp'] = first.get('query_resp')  # 旧兼容（可能为 None）
        result['audit_query_data'] = first['query_data']
        result['audit_id'] = first['audit_id']
        result['audit_execute_resp'] = first['approve_resp']
        result['audit_execute_data'] = first['approve_data']

        for ar in approve_results:
            result['steps'].append(ar['query_step'])
            result['steps'].append(ar['approve_step'])

    return result
