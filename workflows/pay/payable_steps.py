"""
应付对账批次步骤：
- record_payable_account   financePayList（取 amount_list）→ orderPayAccountEdit（发起对账批次）

LK19 = LK18 + 发起应付对账批次。
"""
from typing import Any, Dict

import allure

from api.pay.payable_api import PayableApi
from data.pay import PayableAccountData


def record_payable_account(
    bl_no: str,
) -> Dict[str, Any]:
    """
    发起应付对账批次（financePayList → orderPayAccountEdit）

    该步骤复用 link18 产生的 bl_no，不生成新提单号。

    流程：
      1. financePayList - 按提单号查询应付项列表（提取 amount_list，含 order_fee_real_id）
      2. orderPayAccountEdit - 发起应付对账批次（提交 select_list）

    Args:
        bl_no: 提单号（来自上游 link18 结果）

    Returns:
        {
            'bl_no': str,
            'pay_list_resp': Response,
            'pay_list_data': dict,
            'select_list': [...],           # 来自 financePayList.data.data
            'amount_list_flat': [...],     # 扁平化的 amount_list（含 order_fee_real_id）
            'submit_resp': Response,
            'submit_data': dict,
            'pay_account_id': str,
            'pay_account_no': str,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: financePayList - 查询应付项列表（重试 3 次，等后端同步应付数据）
    with allure.step('查询应付项列表（financePayList，重试最多 3 次）'):
        for attempt in range(1, 4):
            pay_list_resp = PayableApi.query_finance_pay_list(bl_no=bl_no)
            pay_list_data = pay_list_resp.json()
            result['pay_list_resp'] = pay_list_resp
            result['pay_list_data'] = pay_list_data
            result['steps'].append({
                'name': '查询应付项列表',
                'code': pay_list_data.get('code'),
                'msg': pay_list_data.get('msg'),
            })

            assert pay_list_resp.status_code == 200, (
                f'HTTP 状态码异常: {pay_list_resp.status_code}'
            )
            assert pay_list_data.get('code') == 200, (
                f'financePayList 查询失败: {pay_list_data}'
            )

            records = pay_list_data.get('data', {}).get('data', [])
            if records:
                break
            if attempt < 3:
                import time as _time
                _time.sleep(2)
                result['steps'].pop()

    # 从响应构建 select_list（与应收对账 build_select_list 逻辑一致）
    records = pay_list_data.get('data', {}).get('data', [])
    if not records:
        raise AssertionError(
            f'financePayList 查询到 bl_no={bl_no} 但 data=[]（重试 3 次后仍为空），'
            f'可能应付数据尚未同步: {pay_list_data}'
        )
    select_list = PayableAccountData.build_select_list_from_pay_list(
        pay_list_data.get('data', {})
    )
    result['select_list'] = select_list

    # 扁平化 amount_list，提取所有 order_fee_real_id 用于断言
    amount_list_flat = []
    for record in select_list:
        amount_list_flat.extend(record.get("amount_list", []))
    result['amount_list_flat'] = amount_list_flat

    if not select_list:
        raise AssertionError(
            f'financePayList 响应中未提取到 select_list，无法发起应付对账: {pay_list_data}'
        )

    # Step 2: orderPayAccountEdit - 发起应付对账批次
    with allure.step('发起应付对账批次（orderPayAccountEdit）'):
        submit_resp = PayableApi.submit_pay_account(
            select_list=select_list,
        )
        submit_data = submit_resp.json()
        result['submit_resp'] = submit_resp
        result['submit_data'] = submit_data

        submit_data_inner = submit_data.get('data', {})
        result['pay_account_id'] = submit_data_inner.get('pay_account_id', '')
        result['pay_account_no'] = submit_data_inner.get('pay_account_no', '')

        result['steps'].append({
            'name': '发起应付对账批次',
            'code': submit_data.get('code'),
            'msg': submit_data.get('msg'),
            'pay_account_id': result['pay_account_id'],
            'pay_account_no': result['pay_account_no'],
        })

        assert submit_resp.status_code == 200, (
            f'HTTP 状态码异常: {submit_resp.status_code}'
        )
        assert submit_data.get('code') == 200, (
            f'orderPayAccountEdit 失败: {submit_data}'
        )

    return result
