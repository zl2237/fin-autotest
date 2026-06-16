"""
审批相关步骤：
- record_audit                通用审批（按 audit_configs 逐条执行）
- record_order_lock           订单锁定审批
- record_invoice_apply        未放款开票申请审批
- record_supplier_advance     供应商垫付申请审批
"""
from typing import Any, Dict, List

import allure

from api.audit_api import AuditApi
from api.order import OrderApi


def record_audit(
    order_id: str,
    audit_configs: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    录审批（发起审批 → 查询审批ID → 审批通过），按配置列表逐条执行

    audit_configs 每条配置格式：
        {
            'audit_type': 'assetPush',   # 审批类型
            'audit_status': 2,           # 审批状态，2=通过（默认）
        }
    返回值与 record_fee 结构一致
    """
    if audit_configs is None:
        audit_configs = []

    result = {
        'order_id': order_id,
        'results': [],
        'steps': [],
    }

    for i, cfg in enumerate(audit_configs):
        audit_type = cfg.get('audit_type', 'assetPush')

        # 1) 发起审批
        with allure.step(f'发起审批({i + 1}): {audit_type}'):
            send_resp = AuditApi.send_audit(audit_type, order_id)
            send_data = send_resp.json()
            result['steps'].append({
                'name': f'发起审批({i + 1})',
                'code': send_data.get('code'),
                'msg': send_data.get('msg'),
            })

        # 2) 查最新审批ID
        with allure.step(f'查询审批ID({i + 1}): {audit_type}'):
            query_resp = AuditApi.query_pending_audits(
                audit_type=audit_type,
                audit_status=['1'],
                page_no=1,
                page_size=1,
            )
            query_data = query_resp.json()
            records = query_data.get('data', {}).get('data', [])
            first = records[0] if records else {}
            audit_id = first.get('audit_id', '')

        # 3) 审批通过
        with allure.step(f'审批通过({i + 1}): {audit_type}'):
            approve_resp = AuditApi.audit_execute(
                audit_ids=[audit_id] if audit_id else [],
                audit_status=cfg.get('audit_status', 2),
            )
            approve_data = approve_resp.json()

        result['results'].append({
            'index': i,
            'config': cfg,
            'send_resp': send_resp,
            'send_data': send_data,
            'query_resp': query_resp,
            'query_data': query_data,
            'audit_id': audit_id,
            'approve_resp': approve_resp,
            'approve_data': approve_data,
        })
        result['steps'].append({
            'name': f'查询审批ID({i + 1})',
            'code': query_data.get('code'),
            'msg': query_data.get('msg'),
            'audit_id': audit_id,
        })
        result['steps'].append({
            'name': f'审批通过({i + 1})',
            'code': approve_data.get('code'),
            'msg': approve_data.get('msg'),
        })

    return result


def record_order_lock(
    order_id: str,
    bl_no: str = None,
) -> Dict[str, Any]:
    """
    录订单锁定审批（发起审批 → 查询审批ID → 审批通过）

    Args:
        order_id: 业务订单ID
        bl_no   : 提单号（用于查询 container）

    Returns:
        {
            'order_id': str,
            'container': [...],
            'send_resp': Response,
            'send_data': dict,
            'query_resp': Response,
            'query_data': dict,
            'audit_id': str,
            'approve_resp': Response,
            'approve_data': dict,
            'steps': [...],
        }
    """
    result = {
        'order_id': order_id,
        'steps': [],
    }

    # 1) 从订单详情获取 container
    with allure.step('获取箱型信息（用于订单锁定审批）'):
        container = OrderApi.get_container_from_order(bl_no=bl_no)
        if not container:
            from data.order_data import SubmitRequiredFields
            container = SubmitRequiredFields.DEFAULT_CONTAINER.copy()
        result['container'] = container
        result['steps'].append({
            'name': '获取箱型信息',
            'container_count': len(container),
            'from_order': bool(OrderApi.get_container_from_order(bl_no=bl_no)),
        })

    # 2) 发起订单锁定审批
    with allure.step('发起订单锁定审批'):
        send_resp = AuditApi.send_actual_cost_lock(
            order_id=order_id,
            container=container,
        )
        send_data = send_resp.json()
        result['send_resp'] = send_resp
        result['send_data'] = send_data
        result['steps'].append({
            'name': '发起订单锁定审批',
            'code': send_data.get('code'),
            'msg': send_data.get('msg'),
        })

    # 3) 查询审批ID
    with allure.step('查询订单锁定审批ID'):
        query_resp = AuditApi.query_pending_audits(
            audit_type='actualCostLockApplication',
            audit_status=['1'],
            page_no=1,
            page_size=1,
            active_tab='examine_wait',
        )
        query_data = query_resp.json()
        records = query_data.get('data', {}).get('data', [])
        first = records[0] if records else {}
        audit_id = first.get('audit_id', '')
        result['query_resp'] = query_resp
        result['query_data'] = query_data
        result['audit_id'] = audit_id
        result['steps'].append({
            'name': '查询订单锁定审批ID',
            'code': query_data.get('code'),
            'msg': query_data.get('msg'),
            'audit_id': audit_id,
        })

    # 4) 审批通过
    with allure.step('订单锁定审批通过'):
        approve_resp = AuditApi.audit_execute(
            audit_ids=[audit_id] if audit_id else [],
            audit_status=2,
        )
        approve_data = approve_resp.json()
        result['approve_resp'] = approve_resp
        result['approve_data'] = approve_data
        result['steps'].append({
            'name': '订单锁定审批通过',
            'code': approve_data.get('code'),
            'msg': approve_data.get('msg'),
        })

    return result


def record_invoice_apply(
    order_id: str,
    bl_no: str,
) -> Dict[str, Any]:
    """
    录未放款开票申请审批（发起审批 → 查询审批ID → 审批通过）

    Args:
        order_id: 业务订单ID
        bl_no   : 提单号（用于查询筛选）

    Returns:
        {
            'order_id': str,
            'send_resp': Response,
            'send_data': dict,
            'query_resp': Response,
            'query_data': dict,
            'audit_id': str,
            'approve_resp': Response,
            'approve_data': dict,
            'steps': [...],
        }
    """
    result = {
        'order_id': order_id,
        'steps': [],
    }

    # 1) 发起未放款开票申请审批
    with allure.step('发起未放款开票申请审批'):
        send_resp = AuditApi.send_add_loan_before_invoice(order_id=order_id)
        send_data = send_resp.json()
        result['send_resp'] = send_resp
        result['send_data'] = send_data
        result['steps'].append({
            'name': '发起未放款开票申请审批',
            'code': send_data.get('code'),
            'msg': send_data.get('msg'),
        })

    # 2) 查询审批ID
    with allure.step('查询未放款开票申请审批ID'):
        query_resp = AuditApi.query_pending_audits(
            audit_type='addLoanBeforeInvoiceApply',
            audit_status=['1'],
            page_no=1,
            page_size=1,
            active_tab='examine_wait',
            bl_no=bl_no,
            sort_field='expedite_num',
            sort_order='desc',
        )
        query_data = query_resp.json()
        records = query_data.get('data', {}).get('data', [])
        first = records[0] if records else {}
        audit_id = first.get('audit_id', '')
        result['query_resp'] = query_resp
        result['query_data'] = query_data
        result['audit_id'] = audit_id
        result['steps'].append({
            'name': '查询未放款开票申请审批ID',
            'code': query_data.get('code'),
            'msg': query_data.get('msg'),
            'audit_id': audit_id,
        })

    # 3) 审批通过
    with allure.step('未放款开票申请审批通过'):
        approve_resp = AuditApi.audit_execute(
            audit_ids=[audit_id] if audit_id else [],
            audit_status=2,
        )
        approve_data = approve_resp.json()
        result['approve_resp'] = approve_resp
        result['approve_data'] = approve_data
        result['steps'].append({
            'name': '未放款开票申请审批通过',
            'code': approve_data.get('code'),
            'msg': approve_data.get('msg'),
        })

    return result


def record_supplier_advance(
    order_id: str,
    bl_no: str,
) -> Dict[str, Any]:
    """
    录供应商垫付申请审批（发起审批 → 查询审批ID → 审批通过）

    Args:
        order_id: 业务订单ID
        bl_no   : 提单号（用于查询筛选）

    Returns:
        {
            'order_id': str,
            'send_resp': Response,
            'send_data': dict,
            'query_resp': Response,
            'query_data': dict,
            'audit_id': str,
            'approve_resp': Response,
            'approve_data': dict,
            'steps': [...],
        }
    """
    result = {
        'order_id': order_id,
        'steps': [],
    }

    # 1) 发起供应商垫付申请审批
    with allure.step('发起供应商垫付申请审批'):
        send_resp = AuditApi.send_add_special_payment_flag(order_id=order_id)
        send_data = send_resp.json()
        result['send_resp'] = send_resp
        result['send_data'] = send_data
        result['steps'].append({
            'name': '发起供应商垫付申请审批',
            'code': send_data.get('code'),
            'msg': send_data.get('msg'),
        })

    # 2) 查询审批ID
    with allure.step('查询供应商垫付申请审批ID'):
        query_resp = AuditApi.query_pending_audits(
            audit_type='addSpecialPaymentFlag',
            audit_status=['1'],
            page_no=1,
            page_size=1,
            active_tab='examine_wait',
            bl_no=bl_no,
            sort_field='expedite_num',
            sort_order='desc',
        )
        query_data = query_resp.json()
        records = query_data.get('data', {}).get('data', [])
        first = records[0] if records else {}
        audit_id = first.get('audit_id', '')
        result['query_resp'] = query_resp
        result['query_data'] = query_data
        result['audit_id'] = audit_id
        result['steps'].append({
            'name': '查询供应商垫付申请审批ID',
            'code': query_data.get('code'),
            'msg': query_data.get('msg'),
            'audit_id': audit_id,
        })

    # 3) 审批通过
    with allure.step('供应商垫付申请审批通过'):
        approve_resp = AuditApi.audit_execute(
            audit_ids=[audit_id] if audit_id else [],
            audit_status=2,
        )
        approve_data = approve_resp.json()
        result['approve_resp'] = approve_resp
        result['approve_data'] = approve_data
        result['steps'].append({
            'name': '供应商垫付申请审批通过',
            'code': approve_data.get('code'),
            'msg': approve_data.get('msg'),
        })

    return result
