"""
付款单核销步骤（LK25）：

  formPage → writeoffPayFormList → orderFeePage → writeoffBatch

LK25 = LK24 + 付款单核销。
链路复用 link24 产生的 bl_no，不生成新提单号。

流程：
  Step 1: formPage            - 查询付款单列表（重试 3 次，等数据同步）
  Step 2: writeoffPayFormList - 核销付款单列表
  Step 3: orderFeePage        - 查询可核销费用列表
  Step 4: writeoffBatch       - 执行核销
"""
from typing import Any, Dict, List

import allure

from api.pay.pay_writeoff_api import PayWriteoffApi


def writeoff_pay_demand(
    bl_no: str = None,
) -> Dict[str, Any]:
    """
    付款单核销（formPage → writeoffPayFormList → orderFeePage → writeoffBatch）

    该步骤复用 link24 产生的 bl_no，不生成新提单号。

    流程：
      1. formPage            - 查询付款单列表（重试 3 次）
      2. writeoffPayFormList - 核销付款单列表
      3. orderFeePage        - 查询可核销费用列表
      4. writeoffBatch       - 执行核销

    Args:
        bl_no: 提单号（可选，用于日志标识）

    Returns:
        {
            'bl_no': str,
            'form_page_resp': Response,
            'form_page_data': dict,
            'pay_form_records': [...],
            'pay_form_id': str,
            'writeoff_pay_form_list_resp': Response,
            'writeoff_pay_form_list_data': dict,
            'order_fee_real_ids': [...],
            'order_fee_page_resp': Response,
            'order_fee_page_data': dict,
            'writeoff_batch_resp': Response,
            'writeoff_batch_data': dict,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: formPage - 查询付款单列表（重试 3 次，等数据同步）
    with allure.step('查询付款单列表（formPage，重试最多 3 次）'):
        for attempt in range(1, 4):
            form_page_resp = PayWriteoffApi.form_page()
            form_page_data = form_page_resp.json()
            result['form_page_resp'] = form_page_resp
            result['form_page_data'] = form_page_data
            result['steps'].append({
                'name': '查询付款单列表',
                'code': form_page_data.get('code'),
                'msg': form_page_data.get('msg'),
            })

            assert form_page_resp.status_code == 200, (
                f'HTTP 状态码异常: {form_page_resp.status_code}'
            )
            assert form_page_data.get('code') == 200, (
                f'formPage 查询失败: {form_page_data}'
            )

            records = form_page_data.get('data', {}).get('data', [])
            if records:
                break
            if attempt < 3:
                import time as _time
                _time.sleep(2)
                result['steps'].pop()

    records = form_page_data.get('data', {}).get('data', [])
    if not records:
        raise AssertionError(
            f'formPage 查询到 data=[]（重试 3 次后仍为空），'
            f'可能付款单数据尚未同步: {form_page_data}'
        )

    result['pay_form_records'] = records

    # 筛选 status=2 且 writeoff_status=1 的付款单
    unwriteoff_records = [
        r for r in records
        if r.get('status') == '2' and r.get('writeoff_status') == '1'
    ]
    if not unwriteoff_records:
        raise AssertionError(
            f'formPage 查询结果中无 status=2 且 writeoff_status=1 的付款单: {records}'
        )

    first_record = unwriteoff_records[0]
    pay_form_id = str(first_record.get('pay_form_id', ''))
    pay_demand_id = str(first_record.get('pay_demand_id', ''))
    order_fee_real_ids = first_record.get('order_fee_real_ids', [])
    currency = first_record.get('currency', 'USD')
    un_writeoff_amount = first_record.get('un_writeoff_amount', '0.00')
    main_id = str(first_record.get('main_id', ''))
    main_name = first_record.get('main_name', '')

    if not pay_form_id:
        raise AssertionError(
            f'formPage 响应中无法提取 pay_form_id: {first_record}'
        )

    result['pay_form_id'] = pay_form_id
    result['pay_demand_id'] = pay_demand_id
    result['order_fee_real_ids'] = order_fee_real_ids
    result['currency'] = currency
    result['un_writeoff_amount'] = un_writeoff_amount
    result['main_id'] = main_id
    result['main_name'] = main_name

    # Step 2: writeoffPayFormList - 核销付款单列表
    with allure.step('核销付款单列表（writeoffPayFormList）'):
        writeoff_pay_form_list_resp = PayWriteoffApi.writeoff_pay_form_list(
            pay_form_ids=[pay_form_id],
        )
        writeoff_pay_form_list_data = writeoff_pay_form_list_resp.json()
        result['writeoff_pay_form_list_resp'] = writeoff_pay_form_list_resp
        result['writeoff_pay_form_list_data'] = writeoff_pay_form_list_data
        result['steps'].append({
            'name': '核销付款单列表',
            'code': writeoff_pay_form_list_data.get('code'),
            'msg': writeoff_pay_form_list_data.get('msg'),
        })

        assert writeoff_pay_form_list_resp.status_code == 200, (
            f'HTTP 状态码异常: {writeoff_pay_form_list_resp.status_code}'
        )
        assert writeoff_pay_form_list_data.get('code') == 200, (
            f'writeoffPayFormList 失败: {writeoff_pay_form_list_data}'
        )

    # Step 3: orderFeePage - 查询可核销费用列表
    with allure.step('查询可核销费用列表（orderFeePage）'):
        order_fee_page_resp = PayWriteoffApi.order_fee_page(
            order_fee_real_ids=order_fee_real_ids,
        )
        order_fee_page_data = order_fee_page_resp.json()
        result['order_fee_page_resp'] = order_fee_page_resp
        result['order_fee_page_data'] = order_fee_page_data
        result['steps'].append({
            'name': '查询可核销费用列表',
            'code': order_fee_page_data.get('code'),
            'msg': order_fee_page_data.get('msg'),
        })

        assert order_fee_page_resp.status_code == 200, (
            f'HTTP 状态码异常: {order_fee_page_resp.status_code}'
        )
        assert order_fee_page_data.get('code') == 200, (
            f'orderFeePage 失败: {order_fee_page_data}'
        )

    # Step 4: writeoffBatch - 执行核销
    with allure.step('执行核销（writeoffBatch）'):
        writeoff_batch_resp = PayWriteoffApi.writeoff_batch(
            writeoff_object=[{
                'pay_form_id': pay_form_id,
                'un_writeoff_amount': un_writeoff_amount,
            }],
            main_id=main_id,
            main_name=main_name,
            currency=currency,
            use_writeoff_amount_usd_total=un_writeoff_amount if currency == 'USD' else '0.00',
            use_writeoff_amount_cny_total=un_writeoff_amount if currency == 'CNY' else '0.00',
        )
        writeoff_batch_data = writeoff_batch_resp.json()
        result['writeoff_batch_resp'] = writeoff_batch_resp
        result['writeoff_batch_data'] = writeoff_batch_data
        result['steps'].append({
            'name': '执行核销',
            'code': writeoff_batch_data.get('code'),
            'msg': writeoff_batch_data.get('msg'),
            'pay_form_id': pay_form_id,
        })

        assert writeoff_batch_resp.status_code == 200, (
            f'HTTP 状态码异常: {writeoff_batch_resp.status_code}'
        )
        assert writeoff_batch_data.get('code') == 200, (
            f'writeoffBatch 失败: {writeoff_batch_data}'
        )

    return result
