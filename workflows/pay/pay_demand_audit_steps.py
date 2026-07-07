"""
审核生成付款单步骤（LK24）：

  audit_page → audit_execute → (loop until no more records)

LK24 = LK23 + 审核生成付款单。
链路复用 link23 产生的 bl_no，不生成新提单号。

流程：
  Step 1: audit_page  - 查询待审核列表（重试最多 3 次，等审批数据同步）
  Step 2-N: audit_execute - 循环审批通过，直至审批流结束
"""
from typing import Any, Dict, List

import allure

from api.pay.pay_demand_audit_api import PayDemandAuditApi


def audit_pay_demand(
    bl_no: str = None,
) -> Dict[str, Any]:
    """
    审核生成付款单（auditPage → auditExecute）

    该步骤复用 link23 产生的 bl_no，不生成新提单号。

    流程：
      1. auditPage       - 查询待审核列表（重试 3 次）
      2. auditExecute - 执行审批（通过）

    Args:
        bl_no: 提单号（可选，用于日志标识）

    Returns:
        {
            'bl_no': str,
            'audit_page_resp': Response,
            'audit_page_data': dict,
            'audit_records': [...],
            'audit_id': str,
            'audit_execute_resp': Response,
            'audit_execute_data': dict,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: auditPage - 查询待审核列表（重试 3 次，等审批数据同步）
    with allure.step('查询待审核列表（auditPage，重试最多 3 次）'):
        for attempt in range(1, 4):
            audit_page_resp = PayDemandAuditApi.audit_page()
            audit_page_data = audit_page_resp.json()
            result['audit_page_resp'] = audit_page_resp
            result['audit_page_data'] = audit_page_data
            result['steps'].append({
                'name': '查询待审核列表',
                'code': audit_page_data.get('code'),
                'msg': audit_page_data.get('msg'),
            })

            assert audit_page_resp.status_code == 200, (
                f'HTTP 状态码异常: {audit_page_resp.status_code}'
            )
            assert audit_page_data.get('code') == 200, (
                f'auditPage 查询失败: {audit_page_data}'
            )

            records = audit_page_data.get('data', {}).get('data', [])
            if records:
                break
            if attempt < 3:
                import time as _time
                _time.sleep(2)
                result['steps'].pop()

    records = audit_page_data.get('data', {}).get('data', [])
    if not records:
        raise AssertionError(
            f'auditPage 查询到 data=[]（重试 3 次后仍为空），'
            f'可能付款需求审批数据尚未同步: {audit_page_data}'
        )

    result['audit_records'] = records

    # 提取第一个审批记录（按 sort_field=expedite_num 排序后）
    first_record = records[0]
    audit_id = str(first_record.get('audit_id', ''))
    audit_type = first_record.get('audit_type', '')

    if not audit_id:
        raise AssertionError(
            f'auditPage 响应中无法提取 audit_id: {first_record}'
        )

    result['audit_id'] = audit_id
    result['audit_type'] = audit_type

    # 验证审批类型为 payDemand
    if audit_type != 'payDemand':
        raise AssertionError(
            f'审批类型应为 payDemand，实际为: {audit_type}'
        )

    # Step 2-N: audit_execute - 循环审批通过，直至审批流结束
    with allure.step('循环审批通过: payDemand'):
        approve_results: List[Dict[str, Any]] = []
        for i in range(1, 21):
            # 每次审批前重新查询，确保拿到最新待审批记录
            for attempt in range(1, 4):
                audit_page_resp = PayDemandAuditApi.audit_page()
                audit_page_data = audit_page_resp.json()
                records = audit_page_data.get('data', {}).get('data', [])
                if records:
                    break
                if attempt < 3:
                    import time as _time
                    _time.sleep(2)

            if not records:
                break  # 审批流已结束

            first = records[0]
            audit_id = str(first.get('audit_id', ''))
            if not audit_id:
                break

            with allure.step(f'审批通过(节点 {i}): payDemand'):
                audit_execute_resp = PayDemandAuditApi.audit_execute(
                    audit_ids=[audit_id],
                )
                audit_execute_data = audit_execute_resp.json()
                approve_results.append({
                    'node_index': i,
                    'audit_id': audit_id,
                    'approve_resp': audit_execute_resp,
                    'approve_data': audit_execute_data,
                    'audit_execute_resp': audit_execute_resp,
                    'audit_execute_data': audit_execute_data,
                })

        result['approve_results'] = approve_results
        for ar in approve_results:
            result['steps'].append({
                'name': f"审批通过({ar['node_index']})",
                'code': ar['audit_execute_data'].get('code'),
                'msg': ar['audit_execute_data'].get('msg'),
                'audit_id': ar['audit_id'],
            })

    return result
