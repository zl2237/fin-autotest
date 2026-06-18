"""
API 层 - 应付对账批次接口封装

涉及流程：发起应付对账批次（LK19）
  1. POST /api/finance/accountFee/financePayList    - 按 bl_no 查询应付项列表
  2. POST /api/finance/payAccount/orderPayAccountEdit  - 发起应付对账批次

所有枚举值、常量默认值统一从 data/pay/payable.yaml 读取，勿在代码中硬编码。
"""
from typing import Any, Dict, List

from core.http_client import http
from data.pay import (
    OPERATE_TYPE_BILL_OF_LADING,
    ACCOUNT_TYPE_CROSS_CUSTOMER,
    PAGE_NO_DEFAULT,
    PAGE_SIZE_STANDARD,
    PAY_ACCOUNT_ACTION_SUBMIT,
    PayableAccountData,
)


class PayableApi:
    """应付对账批次 API"""

    FINANCE_PAY_LIST_URL = "/api/finance/accountFee/financePayList"
    ORDER_PAY_ACCOUNT_EDIT_URL = "/api/finance/payAccount/orderPayAccountEdit"

    @classmethod
    def query_finance_pay_list(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Any:
        """
        查询应付项列表（financePayList）

        响应 data.data[].amount_list[].order_fee_real_id 为应付对账必需字段。

        Args:
            bl_no              : 提单号（精确查询，来自上游链路）
            page_no            : 页码（默认 PAGE_NO_DEFAULT）
            page_size          : 每页数量（默认 PAGE_SIZE_STANDARD）
            create_time_start  : 创建时间开始（Unix 秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 秒，默认 1 年后）

        Returns:
            Response 对象
        """
        payload = PayableAccountData.get_finance_pay_list_payload(
            bl_no=bl_no,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
        )
        return http.post(cls.FINANCE_PAY_LIST_URL, json=payload)

    @classmethod
    def submit_pay_account(
        cls,
        select_list: List[Dict[str, Any]],
        selection_time: int = None,
        action: str = None,
        account_simple_name: str = None,
        account_type: str = None,
        customer_id: str = None,
        put_settle_object_id: str = None,
        main_id: str = None,
        pay_settle_object_id: str = None,
        main_name: str = None,
        put_settle_object: str = None,
        pay_settle_object: str = None,
    ) -> Any:
        """
        发起应付对账批次（orderPayAccountEdit）

        响应 data.pay_account_id / data.pay_account_no 为应付对账批次标识。

        Args:
            select_list          : 应付项列表（来自 financePayList 响应 data.data）
            selection_time       : 选择时间（Unix 秒，默认当前时间）
            action               : 操作类型（默认 submit）
            account_simple_name  : 账户简称
            account_type         : 账户类型（默认跨客户）
            customer_id          : 客户ID
            put_settle_object_id : 托单结算对象ID
            main_id              : 主体ID
            pay_settle_object_id : 付款结算对象ID
            main_name            : 主体名称
            put_settle_object   : 托单结算对象名称
            pay_settle_object   : 付款结算对象名称

        Returns:
            Response 对象
        """
        import time as _time

        if selection_time is None:
            selection_time = int(_time.time())
        if action is None:
            action = PAY_ACCOUNT_ACTION_SUBMIT
        if account_type is None:
            account_type = ACCOUNT_TYPE_CROSS_CUSTOMER

        payload = {
            "account_simple_name": account_simple_name,
            "account_type": account_type,
            "customer_id": customer_id,
            "put_settle_object_id": put_settle_object_id,
            "main_id": main_id,
            "pay_settle_object_id": pay_settle_object_id,
            "selection_time": selection_time,
            "action": action,
            "operate_type": OPERATE_TYPE_BILL_OF_LADING,
            "pay_account_id": None,
            "main_name": main_name,
            "put_settle_object": put_settle_object,
            "pay_settle_object": pay_settle_object,
            "select_list": select_list,
        }
        return http.post(cls.ORDER_PAY_ACCOUNT_EDIT_URL, json=payload)
