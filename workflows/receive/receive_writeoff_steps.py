"""
应收核销步骤：
- record_receive_writeoff   feeTakePage（取 order_fee_real_id）→ writeoffBatch（核销）
"""
from typing import Any, Dict

import allure

from api.receive.receive_writeoff_api import ReceiveWriteoffApi
from data.receive import ReceiveWriteoffData


def record_receive_writeoff(
    bl_no: str,
    main_id: str = None,
    main_name: str = None,
    writeoff_name: str = None,
    audit_note: str = None,
    statement_currency: str = None,
) -> Dict[str, Any]:
    """
    应收核销（feeTakePage → writeoffBatch）

    流程：
      1. feeTakePage - 按提单号分页查询费用实付 ID 列表（order_fee_real_id）
      2. writeoffBatch - 应收核销（依赖 step1 的 order_fee_real_id + un_writeoff_amount）

    Args:
        bl_no              : 提单号（链路中传递）
        main_id            : 主体ID（默认从 receive_writeoff.yaml 读取）
        main_name          : 主体名称（默认从 receive_writeoff.yaml 读取）
        writeoff_name      : 核销批次名称（默认从 YAML 读取，示例值）
        audit_note         : 审批备注（默认空，走常规核销）
        statement_currency : 账单币种（默认 USD）

    Returns:
        {
            'bl_no': str,
            'fee_take_page_resp': Response,
            'fee_take_page_data': dict,
            'order_fee_real_id_list': [...],   # 原始响应中的订单费用实付 ID 列表
            'writeoff_object': [...],          # 构建的核销对象列表
            'writeoff_batch_resp': Response,
            'writeoff_batch_data': dict,
            'steps': [...],
        }
    """
    from data.receive import (
        RECEIVE_WRITEOFF_MAIN_ID,
        RECEIVE_WRITEOFF_MAIN_NAME,
    )

    if main_id is None:
        main_id = RECEIVE_WRITEOFF_MAIN_ID
    if main_name is None:
        main_name = RECEIVE_WRITEOFF_MAIN_NAME

    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "main_id": main_id,
        "main_name": main_name,
        "steps": [],
    }

    # Step 1: feeTakePage - 查询费用实付 ID 列表
    with allure.step('查询应收核销费用列表（feeTakePage）'):
        fee_take_page_resp = ReceiveWriteoffApi.query_order_fee_real_id_list(bl_no=bl_no)
        fee_take_page_data = fee_take_page_resp.json()
        result['fee_take_page_resp'] = fee_take_page_resp
        result['fee_take_page_data'] = fee_take_page_data
        result['steps'].append({
            'name': '查询应收核销费用列表',
            'code': fee_take_page_data.get('code'),
            'msg': fee_take_page_data.get('msg'),
        })

        assert fee_take_page_resp.status_code == 200, (
            f'HTTP 状态码异常: {fee_take_page_resp.status_code}'
        )
        assert fee_take_page_data.get('code') == 200, (
            f'feeTakePage 失败: {fee_take_page_data}'
        )

    fee_take_page_records = (
        fee_take_page_data.get('data', {}).get('data', []) or []
    )
    result['order_fee_real_id_list'] = fee_take_page_records

    # 从响应中构建 writeoff_object
    writeoff_object = ReceiveWriteoffData.build_writeoff_object_from_fee_take_page(
        fee_take_page_data.get('data', {})
    )
    result['writeoff_object'] = writeoff_object

    if not writeoff_object:
        raise AssertionError(
            f'feeTakePage 响应中未提取到 order_fee_real_id，无法继续应收核销: {fee_take_page_data}'
        )

    # Step 2: writeoffBatch - 应收核销
    with allure.step('应收核销（writeoffBatch）'):
        writeoff_batch_resp = ReceiveWriteoffApi.submit_writeoff_batch(
            writeoff_object=writeoff_object,
            main_id=main_id,
            main_name=main_name,
            writeoff_name=writeoff_name,
            audit_note=audit_note,
            statement_currency=statement_currency,
        )
        writeoff_batch_data = writeoff_batch_resp.json()
        result['writeoff_batch_resp'] = writeoff_batch_resp
        result['writeoff_batch_data'] = writeoff_batch_data
        result['steps'].append({
            'name': '应收核销',
            'code': writeoff_batch_data.get('code'),
            'msg': writeoff_batch_data.get('msg'),
            'writeoff_count': len(writeoff_object),
        })

        assert writeoff_batch_resp.status_code == 200, (
            f'HTTP 状态码异常: {writeoff_batch_resp.status_code}'
        )
        assert writeoff_batch_data.get('code') == 200, (
            f'writeoffBatch 失败: {writeoff_batch_data}'
        )

    return result
