"""
Workflows 层 - 应付开票申请步骤（LK21）

  record_payable_invoice_apply
      financePayList(开票) → getOrderInfoByFeeId → batchOrderEdit(submit)

LK21 = LK20 + 发起应付开票批次申请（apply_type=2，submit 即生效，无需审批）。
"""
from typing import Any, Dict, List

import allure

from api.pay.pay_apply_api import PayInvoiceApi
from data.pay import PayableInvoiceData


def record_payable_invoice_apply(
    bl_no: str,
    main_id: str = None,
    main_name: str = None,
    pay_settle_object: str = None,
    pay_settle_object_id: str = None,
) -> Dict[str, Any]:
    """
    发起应付开票批次申请（financePayList 开票模式 → getOrderInfoByFeeId → batchOrderEdit submit）

    该步骤复用 link20 产生的 bl_no。

    流程：
      1. financePayList（开票模式）  - 按 bl_no 查询应付开票项（提取 order_fee_real_id / amount_list）
      2. getOrderInfoByFeeId         - 按 order_fee_real_id 列表查询开票订单详情
      3. batchOrderEdit(submit)      - 提交应付开票批次申请（apply_type=2，submit 即生效）

    与 link15 发起应收开票批次的区别：
      - 应付方向 submit 后直接生效，无 link16 等价审核步骤
      - seller 是 book_supplier（应付方），purchaser 是 main（应收方主体）
      - 提交成功即可用于 link22 应付开票登记

    Args:
        bl_no               : 提单号（来自上游 link20 结果）
        main_id             : 主体ID（优先取上游 confirm_payable_result / payable_account_result，
                             兜底使用 confirm_payable_account.yaml 配置）
        main_name           : 主体名称
        pay_settle_object   : 付款结算对象名称
        pay_settle_object_id: 付款结算对象ID

    Returns:
        {
            'bl_no': str,
            'pay_list_invoice_resp': Response,
            'pay_list_invoice_data': dict,
            'order_info_resp': Response,
            'order_info_data': dict,
            'order_info_records': [...],
            'submit_resp': Response,
            'submit_data': dict,
            'cost_usd': str,
            'pay_settle_object': str,
            'pay_settle_object_id': str,
            'main_id': str,
            'main_name': str,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: financePayList（开票模式） - 查询应付开票项列表
    # main_id / pay_settle_object_id / pay_settle_object 优先从上游拿，
    # 拿不到时由 data 层从 YAML 默认值兜底（都没有则抛 AssertionError）

    # main_id / main_name / pay_settle_object(_id) 解析：
    #   优先级：入参 > 上游 confirm_payable_result > 上游 payable_account_result > YAML 默认值
    resolved_main_id = main_id
    resolved_main_name = main_name
    resolved_pay_settle_object = pay_settle_object
    resolved_pay_settle_object_id = pay_settle_object_id

    with allure.step('查询应付开票项列表（financePayList 开票模式）'):
        pay_list_resp = PayInvoiceApi.query_finance_pay_list_for_invoice(
            bl_no=bl_no,
            main_id=resolved_main_id,
            pay_settle_object_id=resolved_pay_settle_object_id,
            pay_settle_object=resolved_pay_settle_object,
        )
        pay_list_data = pay_list_resp.json()
        result['pay_list_invoice_resp'] = pay_list_resp
        result['pay_list_invoice_data'] = pay_list_data
        result['steps'].append({
            'name': '查询应付开票项列表',
            'code': pay_list_data.get('code'),
            'msg': pay_list_data.get('msg'),
        })

        assert pay_list_resp.status_code == 200, (
            f'HTTP 状态码异常: {pay_list_resp.status_code}'
        )
        assert pay_list_data.get('code') == 200, (
            f'financePayList（开票模式）查询失败: {pay_list_data}'
        )
        assert pay_list_data.get('msg') == '成功', (
            f'financePayList（开票模式）msg 不为"成功": {pay_list_data.get("msg")}'
        )

    pay_records = pay_list_data.get('data', {}).get('data', []) or []
    if not pay_records:
        raise AssertionError(
            f'financePayList（开票模式）未找到 bl_no={bl_no} 的应付开票项: {pay_list_data}'
        )

    # 提取 amount_list，扁平化得到 order_fee_real_id 列表
    amount_list_flat: List[Dict[str, Any]] = []
    for record in pay_records:
        amount_list_flat.extend(record.get('amount_list', []) or [])

    order_fee_real_ids = [
        str(item.get('order_fee_real_id', ''))
        for item in amount_list_flat
        if item.get('order_fee_real_id')
    ]
    if not order_fee_real_ids:
        raise AssertionError(
            f'financePayList（开票模式）响应中 amount_list 为空，'
            f'无法提取 order_fee_real_id: {pay_list_data}'
        )

    # 兜底 main_id / main_name / pay_settle_object(_id)
    first_record = pay_records[0]
    if not resolved_main_id:
        resolved_main_id = str(first_record.get('main_id', ''))
    if not resolved_main_name:
        resolved_main_name = first_record.get('main_name', '')
    if not resolved_pay_settle_object:
        resolved_pay_settle_object = first_record.get('pay_settle_object', '')
    if not resolved_pay_settle_object_id:
        resolved_pay_settle_object_id = str(first_record.get('pay_settle_object_id', ''))

    if not resolved_main_id:
        raise AssertionError(
            f'无法从 financePayList 响应中提取 main_id，无法发起应付开票: {pay_list_data}'
        )

    result['main_id'] = resolved_main_id
    result['main_name'] = resolved_main_name
    result['pay_settle_object'] = resolved_pay_settle_object
    result['pay_settle_object_id'] = resolved_pay_settle_object_id

    # 检查 amount_list 规模：开票模式理应只返回单个 sup/sub 对应的费用，
    # 若返回多个 fee 极可能是 main_id / pay_settle_object_id 未传入导致的全量返回
    fee_count = len(order_fee_real_ids)
    if fee_count > 1:
        import logging as _logging
        _logging.warning(
            f'financePayList（开票模式）返回了 {fee_count} 个 order_fee_real_id，'
            f'建议检查 main_id={resolved_main_id} / '
            f'pay_settle_object_id={resolved_pay_settle_object_id} 是否正确传递，'
            f'避免后续 batchOrderEdit 406。'
        )

    # Step 2: getOrderInfoByFeeId - 查询开票订单详情
    with allure.step('查询开票订单详情（getOrderInfoByFeeId）'):
        order_info_resp = PayInvoiceApi.get_order_info_by_fee_id(
            order_fee_real_ids=order_fee_real_ids,
        )
        order_info_data = order_info_resp.json()
        result['order_info_resp'] = order_info_resp
        result['order_info_data'] = order_info_data
        result['order_info_records'] = order_info_data.get('data', []) or []
        result['steps'].append({
            'name': '查询开票订单详情',
            'code': order_info_data.get('code'),
            'msg': order_info_data.get('msg'),
            'record_count': len(result['order_info_records']),
        })

        assert order_info_resp.status_code == 200, (
            f'HTTP 状态码异常: {order_info_resp.status_code}'
        )
        assert order_info_data.get('code') == 200, (
            f'getOrderInfoByFeeId 失败: {order_info_data}'
        )
        assert order_info_data.get('msg') == '成功', (
            f'getOrderInfoByFeeId msg 不为"成功": {order_info_data.get("msg")}'
        )

    if not result['order_info_records']:
        raise AssertionError(
            f'getOrderInfoByFeeId 返回 data=[]，无法发起应付开票: {order_info_data}'
        )

    # 总额合计（USD）
    amount_total_usd = 0.0
    for item in result['order_info_records']:
        try:
            amount_total_usd += float(item.get('real_amount', 0) or 0)
        except (TypeError, ValueError):
            pass
    amount_total_usd = round(amount_total_usd, 2)
    result['cost_usd'] = f"{amount_total_usd:.2f}"

    # Step 3: batchOrderEdit(submit) - 发起应付开票批次申请
    # 服务端校验时可能发现费用状态发生变化（其他批次已占用/核销），
    # 此时会返回 code=406 + data[] 内含 useAction='change' 的最新 amount_list，
    # 采用最新 amount_list 重试提交可成功。
    last_submit_data: Dict[str, Any] = {}
    for attempt in range(1, 4):
        with allure.step(f'发起应付开票批次申请（batchOrderEdit submit，第 {attempt} 次）'):
            submit_resp = PayInvoiceApi.submit_pay_invoice_batch(
                order_info_data_list=result['order_info_records'],
                finance_pay_records=pay_records,
                main_id=resolved_main_id,
                main_name=resolved_main_name,
                pay_settle_object=resolved_pay_settle_object,
                pay_settle_object_id=resolved_pay_settle_object_id,
            )
            submit_data = submit_resp.json()
            result['submit_resp'] = submit_resp
            result['submit_data'] = submit_data
            result['steps'].append({
                'name': '发起应付开票批次申请',
                'code': submit_data.get('code'),
                'msg': submit_data.get('msg'),
                'main_id': resolved_main_id,
                'pay_settle_object': resolved_pay_settle_object,
                'cost_usd': result['cost_usd'],
                'attempt': attempt,
            })

            assert submit_resp.status_code == 200, (
                f'HTTP 状态码异常: {submit_resp.status_code}'
            )

            # 成功：跳出重试循环
            if submit_data.get('code') == 200:
                assert submit_data.get('msg') == '成功', (
                    f'batchOrderEdit（应付开票）msg 不为"成功": {submit_data.get("msg")}'
                )
                last_submit_data = submit_data
                break

            # 失败：尝试从 406 响应中提取最新 amount_list 重试
            if submit_data.get('code') == 406:
                data_list = submit_data.get('data', []) or []
                change_items = [d for d in data_list if d.get('useAction') == 'change']
                if change_items:
                    import time as _time
                    _time.sleep(1)
                    new_fee_records: List[Dict[str, Any]] = []
                    for item in change_items:
                        new_fee_records.extend(item.get('amount_list', []) or [])
                    if new_fee_records:
                        result['order_info_records'] = new_fee_records
                        result['cost_usd'] = f"{sum(float(r.get('real_amount', 0) or 0) for r in new_fee_records):.2f}"
                        continue
                raise AssertionError(
                    f'batchOrderEdit（应付开票）406 错误且无可用 change 数据: {submit_data}'
                )

            # 其他错误：直接断言失败
            raise AssertionError(
                f'batchOrderEdit（应付开票）失败: {submit_data}'
            )
    else:
        raise AssertionError(
            f'batchOrderEdit（应付开票）3 次重试后仍未成功: {last_submit_data}'
        )

    return result
