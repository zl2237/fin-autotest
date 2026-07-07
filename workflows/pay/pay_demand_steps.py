"""
发起付款需求步骤（LK23）：

  record_pay_demand:
    financePayList → paymentList → demandEditByOrder

LK23 = LK22 + 发起付款需求。
链路复用 link22 产生的 bl_no，不生成新提单号。

流程：
  Step 1: financePayList       - 查询应付费用列表（重试 3 次，等后端同步应付数据）
  Step 2: paymentList         - 付款需求预览（获取汇总数据）
  Step 3: demandEditByOrder - 提交付款需求（action=submit）
"""
from typing import Any, Dict, List

import allure

from api.pay.pay_demand_api import PayDemandApi
from data.pay import PayDemandData


def record_pay_demand(
    bl_no: str,
    main_id: str = None,
    main_name: str = None,
    pay_settle_object_id: str = None,
    pay_settle_object: str = None,
    split_dimension: List[str] = None,
) -> Dict[str, Any]:
    """
    发起付款需求（financePayList → paymentList → demandEditByOrder）

    该步骤复用 link22 产生的 bl_no，不生成新提单号。

    流程：
      1. financePayList       - 查询应付费用列表（重试 3 次）
      2. paymentList         - 付款需求预览（获取汇总数据）
      3. demandEditByOrder - 提交付款需求

    Args:
        bl_no               : 提单号（来自上游链路）
        main_id             : 主体ID（可选，缺省时从 financePayList 响应提取）
        main_name           : 主体名称（可选）
        pay_settle_object_id: 付款结算对象ID（可选，缺省时从 financePayList 响应提取）
        pay_settle_object   : 付款结算对象名称（可选）
        split_dimension     : 拆分维度列表（默认从 YAML 读取）

    Returns:
        {
            'bl_no': str,
            'pay_list_resp': Response,
            'pay_list_data': dict,
            'select_list': [...],
            'payment_list_resp': Response,
            'payment_list_data': dict,
            'payment_list': [...],
            'submit_resp': Response,
            'submit_data': dict,
            'main_id': str,
            'main_name': str,
            'pay_settle_object_id': str,
            'pay_settle_object': str,
            'cost_usd': str,
            'cost_cny': str,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: financePayList - 查询应付费用列表（付款需求模式）
    with allure.step('查询应付费用列表（financePayList，付款需求模式，重试最多 3 次）'):
        for attempt in range(1, 4):
            pay_list_resp = PayDemandApi.query_finance_pay_list(
                bl_no=bl_no,
                main_id=main_id,
                pay_settle_object_id=pay_settle_object_id,
            )
            pay_list_data = pay_list_resp.json()
            result['pay_list_resp'] = pay_list_resp
            result['pay_list_data'] = pay_list_data
            result['steps'].append({
                'name': '查询应付费用列表',
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

    records = pay_list_data.get('data', {}).get('data', [])
    if not records:
        raise AssertionError(
            f'financePayList 查询到 bl_no={bl_no} 但 data=[]（重试 3 次后仍为空），'
            f'可能应付数据尚未同步: {pay_list_data}'
        )

    pay_list_inner_data = pay_list_data.get('data', {})

    # 构建 select_list 并提取 main_id / pay_settle_object_id
    select_list = PayDemandData._build_select_list(pay_list_inner_data)
    result['select_list'] = select_list

    # 兜底 main_id / pay_settle_object_id / main_name / pay_settle_object
    if not main_id and select_list:
        first_record = select_list[0]
        main_id = str(first_record.get('main_id', '')) if first_record.get('main_id') else None
    if not pay_settle_object_id and select_list:
        first_record = select_list[0]
        pay_settle_object_id = str(first_record.get('pay_settle_object_id', '')) if first_record.get('pay_settle_object_id') else None
    if not main_name and select_list:
        first_record = select_list[0]
        main_name = first_record.get('main_name', '')
    if not pay_settle_object and select_list:
        first_record = select_list[0]
        pay_settle_object = first_record.get('pay_settle_object', '')

    # 计算 cost_usd / cost_cny
    select_amount, cost_usd, cost_cny = PayDemandData._calc_cost_totals(select_list)
    result['select_amount'] = select_amount
    result['cost_usd'] = cost_usd
    result['cost_cny'] = cost_cny
    result['main_id'] = main_id
    result['main_name'] = main_name
    result['pay_settle_object_id'] = pay_settle_object_id
    result['pay_settle_object'] = pay_settle_object

    if not select_list:
        raise AssertionError(
            f'financePayList 响应中未提取到 select_list，无法发起付款需求: {pay_list_data}'
        )

    # Step 2: paymentList - 付款需求预览
    with allure.step('付款需求预览（paymentList）'):
        payment_resp = PayDemandApi.payment_list(
            pay_list_data=pay_list_inner_data,
            select_amount=select_amount,
            cost_usd=cost_usd,
            cost_cny=cost_cny,
            split_dimension=split_dimension,
        )
        payment_data = payment_resp.json()
        result['payment_list_resp'] = payment_resp
        result['payment_list_data'] = payment_data
        result['steps'].append({
            'name': '付款需求预览',
            'code': payment_data.get('code'),
            'msg': payment_data.get('msg'),
        })

        assert payment_resp.status_code == 200, (
            f'HTTP 状态码异常: {payment_resp.status_code}'
        )
        assert payment_data.get('code') == 200, (
            f'paymentList 失败: {payment_data}'
        )

    payment_inner_data = payment_data.get('data', {})
    payment_list = payment_inner_data.get('payment_list', []) or []
    result['payment_list'] = payment_list

    if not payment_list:
        raise AssertionError(
            f'paymentList 响应中 payment_list 为空，无法提交付款需求: {payment_data}'
        )

    # Step 3: demandEditByOrder - 提交付款需求
    with allure.step('提交付款需求（demandEditByOrder）'):
        submit_resp = PayDemandApi.submit_demand(
            pay_list_data=pay_list_inner_data,
            payment_list_data=payment_inner_data,
            split_dimension=split_dimension,
            bl_nos=[bl_no],
        )
        submit_data = submit_resp.json()
        result['submit_resp'] = submit_resp
        result['submit_data'] = submit_data
        result['steps'].append({
            'name': '提交付款需求',
            'code': submit_data.get('code'),
            'msg': submit_data.get('msg'),
        })

        assert submit_resp.status_code == 200, (
            f'HTTP 状态码异常: {submit_resp.status_code}'
        )
        assert submit_data.get('code') == 200, (
            f'demandEditByOrder 失败: {submit_data}'
        )
        assert submit_data.get('msg') == '成功', (
            f'demandEditByOrder msg 不为"成功": {submit_data.get("msg")}'
        )

    return result
