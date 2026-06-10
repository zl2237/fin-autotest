"""
审批流测试数据 - 按审批类型组织，后端生成审批单号
"""
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
            "action": "submit",
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
    # 查询待审批列表
    # =====================

    @classmethod
    def query_pending_audits_payload(
        cls,
        audit_type: str,
        audit_status: List[str] = None,
        page_no: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询审批列表的请求体"""
        if audit_status is None:
            audit_status = ["1"]
        return {
            "audit_status": audit_status,
            "page_no": page_no,
            "page_size": page_size,
            "active_tab": "examine_send",
            "audit_type": [audit_type],
            "sort_field": "create_time",
            "sort_order": "desc",
            "bl_nos": [],
            "expedite_status": [],
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
            audit_status=["1"],
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
}
