"""
API 层 - 审核生成付款单接口封装（LK24）

涉及 2 个请求：
  1. POST /api/home/audit/auditPage        - 查询待审核列表
  2. POST /api/home/audit/auditExecute  - 执行审批（通过）

所有枚举值、常量默认值统一从 data/pay/*.yaml 读取，勿在代码中硬编码。
"""
from typing import Any, List

from core.http_client import http
from data.pay import PayDemandAuditData


class PayDemandAuditApi:
    """审核生成付款单 API"""

    AUDIT_PAGE_URL = "/api/home/audit/auditPage"
    AUDIT_EXECUTE_URL = "/api/home/audit/auditExecute"

    @classmethod
    def audit_page(
        cls,
        page_no: int = None,
        page_size: int = None,
        audit_status: List[str] = None,
        expedite_status: List[str] = None,
        create_id: List[str] = None,
        main_id: List[str] = None,
        active_tab: str = None,
        audit_type: List[str] = None,
        sort_field: str = None,
        sort_order: str = None,
    ) -> Any:
        """
        查询待审核列表（auditPage）

        响应 data.data[].audit_id 为执行审批必需字段。

        Args:
            page_no           : 页码（默认 1）
            page_size        : 每页数量（默认 20）
            audit_status     : 审批状态列表（默认空数组）
            expedite_status  : 催办状态列表（默认空数组）
            create_id        : 创建人ID列表（默认空数组）
            main_id          : 主体ID列表（默认空数组）
            active_tab       : 标签（默认 examine_wait）
            audit_type       : 审批类型列表（默认 [payDemand]）
            sort_field       : 排序字段（默认 expedite_num）
            sort_order       : 排序方向（默认 desc）

        Returns:
            Response 对象
        """
        payload = PayDemandAuditData.get_audit_page_payload(
            page_no=page_no,
            page_size=page_size,
            audit_status=audit_status,
            expedite_status=expedite_status,
            create_id=create_id,
            main_id=main_id,
            active_tab=active_tab,
            audit_type=audit_type,
            sort_field=sort_field,
            sort_order=sort_order,
        )
        return http.post(cls.AUDIT_PAGE_URL, json=payload)

    @classmethod
    def audit_execute(
        cls,
        audit_ids: List[str],
        audit_status: int = None,
        audit_remark: Any = None,
        transfer_user_id: Any = None,
    ) -> Any:
        """
        执行审批（auditExecute）

        响应 code=200 即审批成功。

        Args:
            audit_ids      : 审批ID列表（**必填**，来自 auditPage 响应）
            audit_status  : 审批状态（默认 2=通过）
            audit_remark  : 审批备注（默认 None）
            transfer_user_id: 转交用户ID（默认 None）

        Returns:
            Response 对象
        """
        payload = PayDemandAuditData.get_audit_execute_payload(
            audit_ids=audit_ids,
            audit_status=audit_status,
            audit_remark=audit_remark,
            transfer_user_id=transfer_user_id,
        )
        return http.post(cls.AUDIT_EXECUTE_URL, json=payload)
