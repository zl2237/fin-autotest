"""
发票相关步骤：
- record_invoice_batch         发起应收开票批次审批（多步复合）
- record_invoice_batch_audit   审核生成开票申请
- record_invoice_upload        发票上传与登记（含异步轮询）
"""
import json
import time as _time
from typing import Any, Dict, List

import allure

from api.audit_api import AuditApi


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
    from api.invoice_batch_api import InvoiceBatchApi
    from data.order_data import (
        INVOICE_USD_TURN_ON,
        INVOICE_MERGE_CNY_NO,
        INVOICE_RATE_TYPE_SPECIFY,
        INVOICE_DEFAULT_RATE,
        INVOICE_DEFAULT_FORM,
        INVOICE_DEFAULT_TYPE,
        INVOICE_DEFAULT_ITEM,
    )

    result: Dict[str, Any] = {"bl_no": bl_no, "steps": []}

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
        "fast_remark": "[]",
        "currency": "CNY",
        "amount_total_usd": float(fee_usd_total) if fee_usd_total else 0,
        "amount_total_cny": "",
        "rate": float(exchange_rate) if exchange_rate else 0,
        "turn_amount_total_cny": f"{float(fee_usd_total) * float(exchange_rate):.2f}" if fee_usd_total and exchange_rate else "0.00",
        "turn_amount_total_usd": "",
        "turn_amount_total": f"{float(fee_usd_total) * float(exchange_rate):.2f}" if fee_usd_total and exchange_rate else "0.00",
        "invoice_apply_name": f"{main_name} + {put_settle_object} + 2026-05 + USD {fee_usd_total}",
        "invoice_apply_simple": "",
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
        "require_other": "暂无要求",
        "remark": "—",
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
        "fast_remark": "[]",
        "currency": "",
        "amount_total_usd": "",
        "amount_total_cny": "",
        "rate": "",
        "turn_amount_total_cny": "",
        "turn_amount_total_usd": "",
        "turn_amount_total": "",
        "invoice_apply_name": "",
        "invoice_apply_simple": "",
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
        "remark": "—",
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
    审核生成开票申请（查询审批ID → 审批通过）

    Args:
        batch_id: 开票批次ID（来自 record_invoice_batch 响应中的 batch_id）

    Returns:
        {
            'batch_id': str,
            'audit_query_resp': Response,
            'audit_query_data': dict,
            'audit_id': str,
            'audit_execute_resp': Response,
            'audit_execute_data': dict,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "batch_id": batch_id,
        "steps": [],
    }

    # Step 1: auditPage - 查询开票批次审批ID
    with allure.step('查询应收开票批次审批ID（auditPage）'):
        query_resp = AuditApi.query_invoice_batch_audit(
            relation_id=batch_id,
            audit_status=["1"],
            page_no=1,
            page_size=1,
            active_tab="examine_wait",
        )
        query_data = query_resp.json()
        result['audit_query_resp'] = query_resp
        result['audit_query_data'] = query_data

        records = query_data.get("data", {}).get("data", []) or []
        first = records[0] if records else {}
        audit_id = first.get("audit_id", "")
        result['audit_id'] = audit_id
        result['steps'].append({
            'name': '查询应收开票批次审批ID',
            'code': query_data.get('code'),
            'msg': query_data.get('msg'),
            'audit_id': audit_id,
            'audit_count': len(records),
        })

        if not audit_id:
            raise AssertionError(f'未查到开票批次审批记录，batch_id={batch_id}，响应: {query_data}')

    # Step 2: auditExecute - 审批通过
    with allure.step('审批通过应收开票批次（auditExecute）'):
        execute_resp = AuditApi.audit_execute(
            audit_ids=[audit_id],
            audit_status=2,
        )
        execute_data = execute_resp.json()
        result['audit_execute_resp'] = execute_resp
        result['audit_execute_data'] = execute_data
        result['steps'].append({
            'name': '审批通过应收开票批次',
            'code': execute_data.get('code'),
            'msg': execute_data.get('msg'),
            'audit_id': audit_id,
        })

    return result


def record_invoice_upload(
    bl_no: str,
    receive_invoice_batch_id: str = None,
    file_id: str = None,
    file_name: str = None,
    file_url: str = None,
    original_name: str = None,
    invoice_amount: str = None,
    invoice_number: str = None,
    buyer_chinese_header: str = None,
    buyer_identifier_no: str = None,
    seller_chinese_header: str = None,
    seller_identifier_no: str = None,
    fee_file_info: Dict[str, Any] = None,
    invoice_file_path: str = None,
) -> Dict[str, Any]:
    """
    发票上传与登记

    流程：uploadFile（Step 0）→ invoiceAdd（Step 1）→ applyPage（Step 2）→ allocationInvoiceFee（Step 3）

    Args:
        bl_no                    : 提单号
        receive_invoice_batch_id : 开票批次ID（来自 record_invoice_batch，可选）
        file_id                  : 发票文件ID（已废弃，推荐用 invoice_file_path）
        file_name                : 发票文件名（已废弃，推荐用 invoice_file_path）
        file_url                 : 发票文件URL（已废弃，推荐用 invoice_file_path）
        original_name            : 原始文件名（已废弃，推荐用 invoice_file_path）
        invoice_amount           : 发票金额
        invoice_number           : 发票号码（自动生成唯一值）
        buyer_chinese_header    : 购买方名称
        buyer_identifier_no     : 购买方税号
        seller_chinese_header   : 销售方名称
        seller_identifier_no    : 销售方税号
        fee_file_info           : 费用通知单的文件信息 dict（file_id/file_name/file_url/original_name）
        invoice_file_path        : 本地发票文件路径，传入则自动执行 Step 0 上传并提取 file 信息

    Returns:
        {
            'add_resp' / 'add_data' / 'receive_invoice_id' / 'invoice_number': ...,
            'apply_page_resp' / 'apply_page_data' / 'receive_invoice_apply_id': ...,
            'alloc_resp' / 'alloc_data': ...,
            'steps': [...],
        }
    """
    from api.invoice_upload_api import InvoiceUploadApi
    from data.order_data import _RECEIVE_INVOICE_UPLOAD_CFG

    result: Dict[str, Any] = {"bl_no": bl_no, "steps": []}

    # Step 0: uploadFile - 上传发票文件，获取真实的 file 信息
    uploaded_file_info: Dict[str, Any] = {}
    if invoice_file_path:
        with allure.step('上传发票文件（uploadFile）'):
            upload_resp = InvoiceUploadApi.upload_file(file_path=invoice_file_path)
            upload_data = upload_resp.json()
            result['upload_resp'] = upload_resp
            result['upload_data'] = upload_data
            uploaded_file_info = upload_data.get("data", {}) or {}
            result['uploaded_file_info'] = uploaded_file_info
            result['steps'].append({
                'name': '上传发票文件',
                'code': upload_data.get('code'),
                'msg': upload_data.get('msg'),
                'file_id': uploaded_file_info.get('file_id'),
                'file_name': uploaded_file_info.get('file_name'),
                'file_url': uploaded_file_info.get('file_url'),
                'file_type': uploaded_file_info.get('file_type'),
                'original_name': uploaded_file_info.get('original_name'),
            })
            if not uploaded_file_info.get('file_id'):
                raise AssertionError(f'uploadFile 响应中未找到 file_id: {upload_data}')

    # 从 YAML 读取默认值
    cfg = _RECEIVE_INVOICE_UPLOAD_CFG or {}
    buyer_cfg = cfg.get("buyer", {})
    seller_cfg = cfg.get("seller", {})
    file_cfg = cfg.get("invoice_file", {})
    buyer_chinese_header = buyer_chinese_header or buyer_cfg.get("chinese_header", "")
    buyer_identifier_no = buyer_identifier_no or buyer_cfg.get("identifier_no", "")
    seller_chinese_header = seller_chinese_header or seller_cfg.get("chinese_header", "")
    seller_identifier_no = seller_identifier_no or seller_cfg.get("identifier_no", "")
    # 填充文件字段：Step 0 最高 > fee_file_info > 显式参数 > file_cfg
    if uploaded_file_info:
        file_id = uploaded_file_info.get('file_id', '') or "9999999999"
        file_name = uploaded_file_info.get('file_name', '') or ""
        file_url = uploaded_file_info.get('file_url', '') or ""
        original_name = uploaded_file_info.get('original_name', '') or ""
    elif fee_file_info:
        file_id = file_id or fee_file_info.get('file_id', '') or "9999999999"
        file_name = file_name or fee_file_info.get('file_name', '') or ""
        file_url = file_url or fee_file_info.get('file_url', '') or ""
        original_name = original_name or fee_file_info.get('original_name', '') or ""
    else:
        file_id = file_id or file_cfg.get("file_id", "") or "9999999999"
        file_name = file_name or file_cfg.get("file_name", "") or ""
        file_url = file_url or file_cfg.get("file_url", "") or ""
        original_name = original_name or file_cfg.get("original_name", "") or ""

    # Step 1: invoiceAdd - 上传应收发票
    if invoice_number is None:
        invoice_number = InvoiceUploadApi.generate_unique_invoice_number(prefix="API_INV")
    if invoice_amount is None:
        invoice_amount = "1500"

    invoice_original = {
        "file_id": file_id,
        "file_name": file_name,
        "file_type": "pdf",
        "original_name": original_name,
        "file_url": file_url,
    }

    with allure.step('上传应收发票（invoiceAdd）'):
        add_resp = InvoiceUploadApi.invoice_add(
            invoice_number=invoice_number,
            invoice_amount=invoice_amount,
            invoice_original=invoice_original,
            buyer_chinese_header=buyer_chinese_header,
            buyer_identifier_no=buyer_identifier_no,
            seller_chinese_header=seller_chinese_header,
            seller_identifier_no=seller_identifier_no,
            invoice_image_name=file_name or "",
            file_path=file_url or "",
        )
        add_data = add_resp.json()
        result['add_resp'] = add_resp
        result['add_data'] = add_data
        result['invoice_number'] = invoice_number

        add_data_records = add_data.get("data", {}) or {}
        receive_invoice_id = add_data_records.get(invoice_number, "")
        result['receive_invoice_id'] = receive_invoice_id
        result['steps'].append({
            'name': '上传应收发票',
            'code': add_data.get('code'),
            'msg': add_data.get('msg'),
            'invoice_number': invoice_number,
            'receive_invoice_id': receive_invoice_id,
        })

        if not receive_invoice_id:
            raise AssertionError(f'invoiceAdd 响应中未找到 receive_invoice_id: {add_data}')

    # Step 2: applyPage - 按提单号查询发票申请ID
    with allure.step('获取发票申请ID（applyPage）'):
        apply_page_resp = InvoiceUploadApi.apply_page(bl_no=bl_no)
        apply_page_data = apply_page_resp.json()
        result['apply_page_resp'] = apply_page_resp
        result['apply_page_data'] = apply_page_data

        records = apply_page_data.get("data", {}).get("data", []) or []
        first = records[0] if records else {}
        receive_invoice_apply_id = first.get("receive_invoice_apply_id", "")
        result['receive_invoice_apply_id'] = receive_invoice_apply_id
        result['steps'].append({
            'name': '获取发票申请ID',
            'code': apply_page_data.get('code'),
            'msg': apply_page_data.get('msg'),
            'receive_invoice_apply_id': receive_invoice_apply_id,
            'record_count': len(records),
        })

        if not receive_invoice_apply_id:
            raise AssertionError(f'applyPage 响应中未找到 receive_invoice_apply_id: {apply_page_data}')

    # Step 3: allocationInvoiceFee - 登记发票到申请
    with allure.step('登记发票到申请（allocationInvoiceFee）'):
        # un_amount 来自 applyPage 第一条记录的 invoice_unused_amount
        un_amount = first.get("invoice_unused_amount") or first.get("turn_cost_cny") or invoice_amount
        invoice_arr = [{
            "receive_invoice_id": str(receive_invoice_id),
            "invoice_amount_use": str(un_amount),
        }]
        alloc_resp = InvoiceUploadApi.allocation_invoice_fee(
            receive_invoice_apply_id=receive_invoice_apply_id,
            invoice_arr=invoice_arr,
        )
        alloc_data = alloc_resp.json()
        result['alloc_resp'] = alloc_resp
        result['alloc_data'] = alloc_data
        result['steps'].append({
            'name': '登记发票到申请',
            'code': alloc_data.get('code'),
            'msg': alloc_data.get('msg'),
            'receive_invoice_apply_id': receive_invoice_apply_id,
        })

    # Step 3.5: 等待服务端把 receive_invoice_id 关联到 fee 行（invoice_status 1）
    # 后端异步处理需要几秒时间，writeoffBatch 依赖 fee.invoice_status = "1"
    from api.receive_writeoff_api import ReceiveWriteoffApi as _RWA
    for _attempt in range(1, 6):
        _time.sleep(2)
        _fee_resp = _RWA.query_order_fee_real_id_list(bl_no=bl_no)
        _fee_data = _fee_resp.json().get("data", {}).get("data", []) or []
        _all_invoiced = bool(_fee_data) and all(
            str((f.get("invoice_status") or "")) in ("1", "2") and (f.get("invoice_ids") or "")
            for f in _fee_data
        )
        if _all_invoiced:
            result['fee_status_after_upload'] = {
                'attempt': _attempt,
                'invoice_ids': [f.get("invoice_ids") for f in _fee_data],
            }
            break
    else:
        result['fee_status_after_upload'] = {
            'attempt': 5,
            'pending': [f.get("order_fee_real_id") for f in _fee_data],
        }
        raise AssertionError(
            f'登记发票后 5 次轮询（每次 2s）fee.invoice_status 仍非已开票，无法继续核销: '
            f'{[{"order_fee_real_id": f.get("order_fee_real_id"), "invoice_status": f.get("invoice_status"), "invoice_ids": f.get("invoice_ids")} for f in _fee_data]}'
        )

    return result
