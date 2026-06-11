"""
审批流测试数据 - 按审批类型组织，后端生成审批单号
"""
import time as _time
import random as _random
from typing import Any, Dict, List

import os
import yaml as _yaml

_AUDIT_CFG = _yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "audit.yaml"), encoding="utf-8"))


class AuditFlowData:

    _BUILDERS = {}   # 延迟填充，见底部注册

    @classmethod
    def build_send_payload(cls, audit_type: str, order_id: str) -> Dict[str, Any]:
        """根据审批类型构建发起审批的 payload"""
        builder = cls._BUILDERS.get(audit_type)
        if not builder:
            raise ValueError(f"未知的审批类型: {audit_type}")
        return builder(order_id)

    # =====================
    # 资产推送审批
    # =====================

    @classmethod
    def _asset_push_payload(cls, order_id: str) -> Dict[str, Any]:
        cfg = _AUDIT_CFG["asset_push"]
        return {
            "action": _AUDIT_CFG["submit_action"],
            "order_id": str(order_id),
            "audit_msg": {
                "title": cfg["audit_msg"]["title"],
                "code": "",
                "msgs": cfg["audit_msg"]["msgs"],
            },
            "select_node_user": cfg["select_node_user"],
        }

    @classmethod
    def asset_push_payload(cls, order_id: str) -> Dict[str, Any]:
        """发起资产推送审批的请求体"""
        return cls._asset_push_payload(order_id)

    # =====================
    # 订单锁定审批
    # =====================

    @classmethod
    def _actual_cost_lock_payload(
        cls,
        order_id: str,
        container: List[Dict[str, Any]],
        policy_type: str = "JSZX",
        business_type: str = "1",
        business_no: str = "",
    ) -> Dict[str, Any]:
        """
        发起订单锁定审批的请求体

        Args:
            order_id     : 业务订单ID
            container    : 箱型信息列表（从 get_container_from_order 获取）
            policy_type  : 策略类型
            business_type: 业务类型
            business_no  : 业务单号（前端自动生成，此处填空字符串由后端填充）
        """
        cfg = _AUDIT_CFG["actual_cost_lock"]
        ts = str(int(_time.time() * 1000))
        rand = str(_random.randint(1000, 9999))
        code = f"ZDD{ts}{rand}"

        enriched_container = []
        for idx, c in enumerate(container):
            enriched_container.append({
                **c,
                "_XID": f"row_{idx + 1}",
            })

        return {
            "action": _AUDIT_CFG["submit_action"],
            "order_id": str(order_id),
            "container": enriched_container,
            "policy_type": policy_type,
            "business_type": business_type,
            "box_no_continue": cfg["box_no_continue"],
            "check_self_fee_status": cfg["check_self_fee_status"],
            "audit_msg": {
                "title": cfg["audit_msg"]["title"],
                "code": code,
                "msgs": cfg["audit_msg"]["msgs"],
            },
            "select_node_user": cfg["select_node_user"],
        }

    # =====================
    # 供应商垫付申请审批
    # =====================

    @classmethod
    def _add_special_payment_flag_payload(
        cls,
        order_id: str,
    ) -> Dict[str, Any]:
        """发起供应商垫付申请审批的请求体"""
        cfg = _AUDIT_CFG["add_special_payment_flag"]
        return {
            "audit_note": "",
            "order_ids": [str(order_id)],
            "action": _AUDIT_CFG["submit_action"],
            "audit_msg": {
                "title": cfg["audit_msg"]["title"],
                "code": "",
                "msgs": cfg["audit_msg"]["msgs"],
            },
            "select_node_user": cfg["select_node_user"],
        }

    # =====================
    # 未放款开票申请审批
    # =====================

    @classmethod
    def _add_loan_before_invoice_payload(
        cls,
        order_id: str,
    ) -> Dict[str, Any]:
        """发起未放款开票申请审批的请求体"""
        cfg = _AUDIT_CFG["add_loan_before_invoice"]
        return {
            "audit_note": "",
            "order_ids": [str(order_id)],
            "action": _AUDIT_CFG["submit_action"],
            "audit_msg": {
                "title": cfg["audit_msg"]["title"],
                "code": "",
                "msgs": cfg["audit_msg"]["msgs"],
            },
            "select_node_user": cfg["select_node_user"],
        }

    # =====================
    # 查询待审批列表
    # =====================

    @classmethod
    def query_pending_audits_payload(
        cls,
        audit_type: str,
        audit_status: List[str] = None,
        page_no: int = None,
        page_size: int = None,
        active_tab: str = None,
        bl_no: str = None,
        sort_field: str = "create_time",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """查询审批列表的请求体"""
        if audit_status is None:
            audit_status = [_AUDIT_CFG["query_audit_status_pending"]]
        if active_tab is None:
            active_tab = _AUDIT_CFG["query_active_tab"]
        if page_no is None:
            page_no = _AUDIT_CFG["query_page_no"]
        if page_size is None:
            page_size = _AUDIT_CFG["query_page_size"]
        return {
            "audit_status": audit_status,
            "page_no": page_no,
            "page_size": page_size,
            "active_tab": active_tab,
            "audit_type": [audit_type],
            "sort_field": sort_field,
            "sort_order": sort_order,
            "bl_nos": [bl_no] if bl_no else [],
            "expedite_status": _AUDIT_CFG["query_expedite_status"],
            "create_id": [],
            "executor_id": [],
            "customer_id": [],
            "params": {},
        }

    @classmethod
    def get_latest_audit_id(cls, audit_type: str) -> Dict[str, Any]:
        """查询某类型最新一条审批记录"""
        return cls.query_pending_audits_payload(
            audit_type=audit_type,
            audit_status=[_AUDIT_CFG["query_audit_status_pending"]],
            page_no=1,
            page_size=1,
        )

    # =====================
    # 审批通过 / 拒绝
    # =====================

    @classmethod
    def approve_payload(
        cls,
        audit_ids: List[str],
        audit_status: int = 2,
        audit_remark: str = None,
        transfer_user_id: str = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "audit_ids": [str(aid) for aid in audit_ids],
            "audit_status": audit_status,
        }
        if audit_remark is not None:
            payload["audit_remark"] = audit_remark
        if transfer_user_id is not None:
            payload["transfer_user_id"] = transfer_user_id
        return payload


# ========================================================================
# 审批类型 → payload 构建器 注册
# ========================================================================

AuditFlowData._BUILDERS = {
    "assetPush": AuditFlowData._asset_push_payload,
    "actualCostLockApplication": AuditFlowData._actual_cost_lock_payload,
    "addLoanBeforeInvoiceApply": AuditFlowData._add_loan_before_invoice_payload,
    "addSpecialPaymentFlag": AuditFlowData._add_special_payment_flag_payload,
}
