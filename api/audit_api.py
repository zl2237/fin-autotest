"""
API 层 - 审批流相关接口封装
"""
from typing import Any

from core.http_client import http
from data.audit_data import AuditFlowData


class AuditApi:

    # =====================
    # 接口地址
    # =====================

    _SEND_URLS = {
        "assetPush": "/api/order/orderFee/assetPush",  # 资产推送
    }

    AUDIT_PAGE_URL = "/api/home/audit/auditPage"       # 查询审批列表
    AUDIT_EXECUTE_URL = "/api/home/audit/auditExecute"   # 执行审批

    # =====================
    # 通用发起审批（按类型分发）
    # =====================

    @classmethod
    def send_audit(cls, audit_type: str, order_id: str) -> Any:
        """
        发起指定类型的审批

        Args:
            audit_type: 审批类型，如 'assetPush'
            order_id  : 订单ID

        Returns:
            Response 对象
        """
        url = cls._SEND_URLS.get(audit_type)
        if not url:
            raise ValueError(f"未知的审批类型: {audit_type}，请在 AuditApi._SEND_URLS 中注册")
        payload = AuditFlowData.build_send_payload(audit_type, order_id)
        return http.post(url, json=payload)

    # =====================
    # 资产推送快捷方法
    # =====================

    @classmethod
    def send_asset_push(cls, order_id: str) -> Any:
        """发起资产推送审批"""
        return cls.send_audit("assetPush", order_id)

    # =====================
    # 查询审批列表
    # =====================

    @classmethod
    def query_pending_audits(
        cls,
        audit_type: str,
        audit_status: list = None,
        page_no: int = 1,
        page_size: int = 20,
    ) -> Any:
        """
        查询审批列表

        Args:
            audit_type   : 审批类型，如 'assetPush'
            audit_status : 审批状态列表，默认 ['1']
            page_no     : 页码
            page_size   : 每页条数

        Returns:
            Response 对象
        """
        payload = AuditFlowData.query_pending_audits_payload(
            audit_type=audit_type,
            audit_status=audit_status,
            page_no=page_no,
            page_size=page_size,
        )
        return http.post(cls.AUDIT_PAGE_URL, json=payload)

    # =====================
    # 执行审批
    # =====================

    @classmethod
    def audit_execute(
        cls,
        audit_ids: list,
        audit_status: int = 2,
        audit_remark: str = None,
        transfer_user_id: str = None,
    ) -> Any:
        """
        执行审批（通过/拒绝/转交）

        Args:
            audit_ids       : 审批ID列表
            audit_status    : 审批状态，2=通过
            audit_remark    : 审批备注
            transfer_user_id: 转交用户ID

        Returns:
            Response 对象
        """
        payload = AuditFlowData.approve_payload(
            audit_ids=audit_ids,
            audit_status=audit_status,
            audit_remark=audit_remark,
            transfer_user_id=transfer_user_id,
        )
        return http.post(cls.AUDIT_EXECUTE_URL, json=payload)

