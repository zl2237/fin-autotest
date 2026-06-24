"""
审批相关步骤：
- record_audit                通用审批（按 audit_configs 逐条执行）
- record_order_lock           订单锁定审批
- record_invoice_apply        未放款开票申请审批
- record_supplier_advance     供应商垫付申请审批
"""
from typing import Any, Dict, List

import allure

from api.order import AuditApi, OrderApi


def _loop_approve_until_done(
    audit_type: str,
    relation_id: str = None,
    bl_no: str = None,
    active_tab: str = "examine_send",
    sort_field: str = "create_time",
    sort_order: str = "desc",
    audit_status: int = 2,
    max_nodes: int = 20,
    query_step_name: str = None,
    approve_step_name: str = None,
) -> List[Dict[str, Any]]:
    """
    循环调用审批通过接口，直至审批流所有节点都处理完。

    每次审批后重新查询待审批列表；若列表为空，说明审批流已结束。

    Args:
        audit_type  : 审批类型（如 'actualCostLockApplication'）
        relation_id : 关联业务ID（精确筛选）
        bl_no       : 提单号（精确筛选）
        active_tab  : 查询标签页，默认 'examine_wait'
        sort_field  : 排序字段
        sort_order  : 排序方向
        audit_status: 审批状态，默认 2（通过）
        max_nodes   : 最大循环次数，防止死循环

    Returns:
        每轮审批的响应数据列表
    """
    approve_results = []

    for i in range(1, max_nodes + 1):
        default_query_step_name = f"查询审批ID({i})"
        step_name = query_step_name or default_query_step_name
        # 1) 查询待审批ID
        with allure.step(f"{step_name}: {audit_type}"):
            query_resp = AuditApi.query_pending_audits(
                audit_type=audit_type,
                audit_status=["1"],
                page_no=1,
                page_size=1,
                active_tab=active_tab,
                bl_no=bl_no,
                sort_field=sort_field,
                sort_order=sort_order,
                relation_id=relation_id,
            )
            query_data = query_resp.json()
        records = query_data.get("data", {}).get("data", [])
        if not records:
            break  # 审批流已结束

        first = records[0]
        audit_id = first.get("audit_id", "")

        # 2) 审批通过
        default_approve_step_name = f"审批通过({i})"
        approve_name = approve_step_name or default_approve_step_name
        with allure.step(f"{approve_name}: {audit_type}"):
            approve_resp = AuditApi.audit_execute(
                audit_ids=[audit_id] if audit_id else [],
                audit_status=audit_status,
            )
            approve_data = approve_resp.json()
            approve_results.append({
                "node_index": i,
                "audit_id": audit_id,
                "query_resp": query_resp,
                "query_data": query_data,
                "approve_resp": approve_resp,
                "approve_data": approve_data,
                "query_step": {
                    "name": step_name,
                    "code": query_data.get("code"),
                    "msg": query_data.get("msg"),
                },
                "approve_step": {
                    "name": approve_name,
                    "code": approve_data.get("code"),
                    "msg": approve_data.get("msg"),
                },
            })

    return approve_results


def record_audit(
    order_id: str,
    audit_configs: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    录审批（发起审批 → 查询审批ID → 循环审批通过），按配置列表逐条执行

    audit_configs 每条配置格式：
        {
            'audit_type': 'assetPush',   # 审批类型
            'audit_status': 2,           # 审批状态，2=通过（默认）
            'active_tab': 'examine_wait', # 查询标签页（默认）
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

        # 2) 循环审批直到结束
        active_tab = cfg.get('active_tab', 'examine_wait')
        with allure.step(f'循环审批通过({i + 1}): {audit_type}'):
            approve_results = _loop_approve_until_done(
                audit_type=audit_type,
                active_tab=active_tab,
                audit_status=cfg.get('audit_status', 2),
                query_step_name=cfg.get('query_step_name', f'查询审批ID({i + 1})'),
                approve_step_name=cfg.get('approve_step_name', f'审批通过({i + 1})'),
            )

        result['results'].append({
            'index': i,
            'config': cfg,
            'send_resp': send_resp,
            'send_data': send_data,
            'approve_results': approve_results,
        })
        if approve_results:
            first = approve_results[0]
            result['results'][i]['audit_id'] = first['audit_id']
            result['results'][i]['approve_resp'] = first['approve_resp']
            result['results'][i]['approve_data'] = first['approve_data']
            # 兼容 fee_steps.py 旧字段名（audit_after_fee 分支）
            result['results'][i]['audit_approve_resp'] = first['approve_resp']
            result['results'][i]['audit_approve_data'] = first['approve_data']

        for ar in approve_results:
            result['steps'].append(ar['query_step'])
            result['steps'].append(ar['approve_step'])

    return result


def record_order_lock(
    order_id: str,
    bl_no: str = None,
) -> Dict[str, Any]:
    """
    录订单锁定审批（发起审批 → 循环审批通过，直至审批流结束）

    Args:
        order_id: 业务订单ID
        bl_no   : 提单号（用于查询 container）

    Returns:
        {
            'order_id': str,
            'container': [...],
            'send_resp': Response,
            'send_data': dict,
            'approve_results': [...],
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
            from data.order import SubmitRequiredFields
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

    # 3) 循环审批直到结束
    with allure.step('循环审批通过: actualCostLockApplication'):
        approve_results = _loop_approve_until_done(
            audit_type='actualCostLockApplication',
            active_tab='examine_wait',
            bl_no=bl_no,
            query_step_name='查询订单锁定审批ID',
            approve_step_name='订单锁定审批通过',
        )
        result['approve_results'] = approve_results
        if approve_results:
            first = approve_results[0]
            result['audit_id'] = first['audit_id']
            result['approve_resp'] = first['approve_resp']
            result['approve_data'] = first['approve_data']
        for ar in approve_results:
            result['steps'].append(ar['query_step'])
            result['steps'].append(ar['approve_step'])

    return result


def record_invoice_apply(
    order_id: str,
    bl_no: str,
) -> Dict[str, Any]:
    """
    录未放款开票申请审批（发起审批 → 循环审批通过，直至审批流结束）

    Args:
        order_id: 业务订单ID
        bl_no   : 提单号（用于查询筛选）

    Returns:
        {
            'order_id': str,
            'send_resp': Response,
            'send_data': dict,
            'approve_results': [...],
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

    # 2) 循环审批直到结束
    with allure.step('循环审批通过: addLoanBeforeInvoiceApply'):
        approve_results = _loop_approve_until_done(
            audit_type='addLoanBeforeInvoiceApply',
            active_tab='examine_wait',
            bl_no=bl_no,
            sort_field='expedite_num',
            sort_order='desc',
            query_step_name='查询未放款开票申请审批ID',
            approve_step_name='未放款开票申请审批通过',
        )
        result['approve_results'] = approve_results
        if approve_results:
            first = approve_results[0]
            result['audit_id'] = first['audit_id']
            result['approve_resp'] = first['approve_resp']
            result['approve_data'] = first['approve_data']
        for ar in approve_results:
            result['steps'].append(ar['query_step'])
            result['steps'].append(ar['approve_step'])

    return result


def record_supplier_advance(
    order_id: str,
    bl_no: str,
) -> Dict[str, Any]:
    """
    录供应商垫付申请审批（发起审批 → 循环审批通过，直至审批流结束）

    Args:
        order_id: 业务订单ID
        bl_no   : 提单号（用于查询筛选）

    Returns:
        {
            'order_id': str,
            'send_resp': Response,
            'send_data': dict,
            'approve_results': [...],
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

    # 2) 循环审批直到结束
    with allure.step('循环审批通过: addSpecialPaymentFlag'):
        approve_results = _loop_approve_until_done(
            audit_type='addSpecialPaymentFlag',
            active_tab='examine_wait',
            bl_no=bl_no,
            sort_field='expedite_num',
            sort_order='desc',
            query_step_name='查询供应商垫付申请审批ID',
            approve_step_name='供应商垫付申请审批通过',
        )
        result['approve_results'] = approve_results
        if approve_results:
            first = approve_results[0]
            result['audit_id'] = first['audit_id']
            result['approve_resp'] = first['approve_resp']
            result['approve_data'] = first['approve_data']
        for ar in approve_results:
            result['steps'].append(ar['query_step'])
            result['steps'].append(ar['approve_step'])

    return result
