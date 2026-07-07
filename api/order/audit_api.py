"""
API 层 - 审批流相关接口封装
"""
from typing import Any, Dict, List

from core.http_client import http
from data.order import AuditFlowData


class AuditApi:

    # =====================
    # 接口地址
    # =====================

    _SEND_URLS = {
        "assetPush": "/api/order/orderFee/assetPush",                    # 资产推送
        "actualCostLockApplication": "/api/order/orderFee/realAmountSubmit",  # 订单锁定
        "addLoanBeforeInvoiceApply": "/api/order/order/changeInvoiceApply",   # 未放款开票申请
        "addSpecialPaymentFlag": "/api/order/order/changeSpecialPayRules",     # 供应商垫付申请
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

    @classmethod
    def send_actual_cost_lock(
        cls,
        order_id: str,
        container: List[Dict[str, Any]],
        policy_type: str = "JSZX",
        business_type: str = "1",
        business_no: str = "",
    ) -> Any:
        """
        发起订单锁定审批

        Args:
            order_id     : 业务订单ID
            container    : 箱型信息列表（从 get_container_from_order 获取）
            policy_type  : 策略类型
            business_type: 业务类型
            business_no  : 业务单号（后端自动生成，此处填空字符串）

        Returns:
            Response 对象
        """
        from data.order import AuditFlowData
        payload = AuditFlowData._actual_cost_lock_payload(
            order_id=order_id,
            container=container,
            policy_type=policy_type,
            business_type=business_type,
            business_no=business_no,
        )
        return http.post(cls._SEND_URLS["actualCostLockApplication"], json=payload)

    @classmethod
    def send_add_loan_before_invoice(cls, order_id: str) -> Any:
        """发起未放款开票申请审批"""
        from data.order import AuditFlowData
        payload = AuditFlowData._add_loan_before_invoice_payload(order_id)
        return http.post(cls._SEND_URLS["addLoanBeforeInvoiceApply"], json=payload)

    @classmethod
    def send_add_special_payment_flag(cls, order_id: str) -> Any:
        """发起供应商垫付申请审批"""
        from data.order import AuditFlowData
        payload = AuditFlowData._add_special_payment_flag_payload(order_id)
        return http.post(cls._SEND_URLS["addSpecialPaymentFlag"], json=payload)

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
        active_tab: str = "examine_send",
        bl_no: str = None,
        sort_field: str = "create_time",
        sort_order: str = "desc",
        relation_id: str = None,
    ) -> Any:
        """
        查询审批列表

        Args:
            audit_type   : 审批类型，如 'assetPush'
            audit_status : 审批状态列表，默认 ['1']
            page_no     : 页码
            page_size   : 每页条数
            active_tab  : 标签页，'examine_send'=我发起的，'examine_wait'=我审批的
            bl_no       : 提单号（用于精确筛选）
            sort_field  : 排序字段，默认 'create_time'
            sort_order  : 排序方向，默认 'desc'
            relation_id : 关联业务ID（精确筛选）

        Returns:
            Response 对象
        """
        payload = AuditFlowData.query_pending_audits_payload(
            audit_type=audit_type,
            audit_status=audit_status,
            page_no=page_no,
            page_size=page_size,
            active_tab=active_tab,
            bl_no=bl_no,
            sort_field=sort_field,
            sort_order=sort_order,
            relation_id=relation_id,
        )
        return http.post(cls.AUDIT_PAGE_URL, json=payload)

    # =====================
    # 开票批次审批快捷方法
    # =====================

    @classmethod
    def query_invoice_batch_audit(
        cls,
        relation_id: str = None,
        audit_status: list = None,
        page_no: int = 1,
        page_size: int = 20,
        active_tab: str = "examine_wait",
    ) -> Any:
        """
        查询应收开票批次审批列表

        Args:
            relation_id  : 关联业务ID（来自 batchOrderEdit 响应中的 batch_id）
            audit_status : 审批状态列表，默认 ['1']
            page_no      : 页码
            page_size    : 每页条数
            active_tab   : 标签页，'examine_wait'=待我审批

        Returns:
            Response 对象
        """
        return cls.query_pending_audits(
            audit_type="invoiceBatchApplication",
            audit_status=audit_status,
            page_no=page_no,
            page_size=page_size,
            active_tab=active_tab,
            relation_id=relation_id,
        )

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

