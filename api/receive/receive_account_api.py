"""
API 层 - 应收对账相关接口封装

涉及两套流程：
  发起应收对账批次（LINK13）：
    1. POST /api/finance/accountFee/financePutList        - 查询应收款项列表
    2. POST /api/finance/receiveAccount/orderReceiveAccountEdit (action=check) - 预校验
    3. POST /api/finance/receiveAccount/orderReceiveAccountEdit (action=submit) - 正式发起对账批次

  确认应收对账（LINK14）：
    1. POST /api/finance/receiveAccount/receiveAccountDetail       - 查询批次详情
    2. POST /api/finance/receiveAccount/receiveConfirmList         - 查询应收确认列表（构建 confirm_list）
    3. POST /api/finance/receiveAccount/accountConfirm            - 确认应收对账
    4. POST /api/finance/receiveAccount/receiveAccountPage         - 确认后查询批次列表

所有枚举值、常量默认值统一从 data/receive/receive_account.yaml 读取，勿在代码中硬编码。
"""
import time
from typing import Dict, Any, List, Optional

from core.http_client import http
from data.receive import (
    OPERATE_TYPE_RECEIVABLE,
    ACCOUNT_TYPE_CROSS_CUSTOMER,
    CONFIRM_TYPE_PENDING,
    PAGE_NO_DEFAULT,
    PAGE_SIZE_STANDARD,
    PAGE_SIZE_LARGE,
    YEAR_OFFSET_SECONDS,
    DAY_OFFSET_SECONDS,
    TIMESTAMP_MS_FACTOR,
    SORT_FIELD_CREATE_TIME,
    SORT_ORDER_DESC,
    _RECEIVE_ACCOUNT_CFG,
)


def _default_main_id() -> str:
    """从 YAML 配置读取默认 main_id（仅当未显式传参时使用）"""
    cfg = _RECEIVE_ACCOUNT_CFG.get("finance_put_list", {})
    return cfg.get("main_id", "1")


class FinanceApi:
    """财务系统应收对账相关 API"""

    FINANCE_BASE_URL = "/api/finance"

    FINANCE_PUT_LIST_URL = "/api/finance/accountFee/financePutList"
    RECEIVE_ACCOUNT_EDIT_URL = "/api/finance/receiveAccount/orderReceiveAccountEdit"
    RECEIVE_ACCOUNT_DETAIL_URL = "/api/finance/receiveAccount/receiveAccountDetail"
    RECEIVE_CONFIRM_LIST_URL = "/api/finance/receiveAccount/receiveConfirmList"
    ACCOUNT_CONFIRM_URL = "/api/finance/receiveAccount/accountConfirm"
    RECEIVE_ACCOUNT_PAGE_URL = "/api/finance/receiveAccount/receiveAccountPage"

    @classmethod
    def query_finance_put_list(
        cls,
        bl_no: str,
        put_settle_object_id: str,
        main_id: str = None,
        page_no: int = None,
        page_size: int = None,
        operate_type: int = None,
    ) -> Any:
        """
        查询应收款项列表（financePutList）

        用于预填充 orderReceiveAccountEdit 的 select_list。

        Args:
            bl_no                : 提单号
            put_settle_object_id : 托单结算对象ID
            main_id              : 主体ID（默认从 YAML 读取）
            page_no              : 页码（默认 PAGE_NO_DEFAULT）
            page_size            : 每页数量（默认 PAGE_SIZE_STANDARD）
            operate_type         : 操作类型（默认 OPERATE_TYPE_RECEIVABLE = 1 = 应收）

        Returns:
            Response 对象
        """
        if main_id is None:
            main_id = _default_main_id()
        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            page_size = PAGE_SIZE_STANDARD
        if operate_type is None:
            operate_type = OPERATE_TYPE_RECEIVABLE

        payload = {
            "page_no": page_no,
            "page_size": page_size,
            "bl_no": bl_no,
            "operate_type": operate_type,
            "search_style": "account",
            "account_simple_name": None,
            "account_type": ACCOUNT_TYPE_CROSS_CUSTOMER,
            "customer_id": None,
            "put_settle_object_id": str(put_settle_object_id),
            "main_id": str(main_id),
            "pay_settle_object_id": None,
        }
        return http.post(cls.FINANCE_PUT_LIST_URL, json=payload)

    @classmethod
    def edit_receive_account(
        cls,
        action: str,
        put_settle_object_id: str,
        main_id: str,
        put_settle_object: str,
        main_name: str,
        select_list: List[Dict[str, Any]],
        operate_type: int = None,
        receive_account_id: Optional[str] = None,
        pay_settle_object: Optional[str] = None,
        account_simple_name: Optional[str] = None,
        customer_id: Optional[str] = None,
        pay_settle_object_id: Optional[str] = None,
    ) -> Any:
        """
        应收对账批次编辑（预校验 / 正式提交）

        action=check : 预校验，不创建批次，返回 receive_account_id=0
        action=submit: 正式发起对账批次，返回 receive_account_id 和批次号

        Args:
            action               : 操作类型，check 或 submit（使用 ACTION_CHECK / ACTION_SUBMIT 常量）
            put_settle_object_id : 托单结算对象ID
            main_id              : 主体ID
            put_settle_object    : 托单结算对象名称
            main_name            : 主体名称
            select_list          : 应收款项列表（来自 financePutList 响应）
            operate_type         : 操作类型（默认 OPERATE_TYPE_RECEIVABLE）
            receive_account_id   : 对账ID（预校验响应返回，提交时回传）
            pay_settle_object    : 付款结算对象名称
            account_simple_name  : 账户简称
            customer_id          : 客户ID
            pay_settle_object_id : 付款结算对象ID

        Returns:
            Response 对象
        """
        if operate_type is None:
            operate_type = OPERATE_TYPE_RECEIVABLE

        payload = {
            "account_simple_name": account_simple_name,
            "account_type": ACCOUNT_TYPE_CROSS_CUSTOMER,
            "customer_id": customer_id,
            "put_settle_object_id": str(put_settle_object_id),
            "main_id": str(main_id),
            "pay_settle_object_id": pay_settle_object_id,
            "selection_time": int(time.time()),
            "action": action,
            "operate_type": operate_type,
            "receive_account_id": receive_account_id,
            "main_name": main_name,
            "put_settle_object": put_settle_object,
            "pay_settle_object": pay_settle_object,
            "select_list": select_list,
        }
        return http.post(cls.RECEIVE_ACCOUNT_EDIT_URL, json=payload)

    @classmethod
    def get_receive_account_detail(
        cls,
        receive_account_id: str,
    ) -> Any:
        """
        查询应收对账批次详情（receiveAccountDetail）

        用于获取批次的完整信息。

        Args:
            receive_account_id: 应收对账批次ID

        Returns:
            Response 对象
        """
        payload = {
            "receive_account_id": str(receive_account_id),
        }
        return http.post(cls.RECEIVE_ACCOUNT_DETAIL_URL, json=payload)

    @classmethod
    def get_receive_confirm_list(
        cls,
        receive_account_id: str,
        confirm_type: int = None,
        order_ids: List[str] = None,
    ) -> Any:
        """
        查询应收确认列表（receiveConfirmList）

        用于构建 accountConfirm 所需的 confirm_list。

        Args:
            receive_account_id: 应收对账批次ID
            confirm_type      : 确认类型（默认 CONFIRM_TYPE_PENDING = 0 = 待确认）
            order_ids          : 订单ID列表

        Returns:
            Response 对象
        """
        if confirm_type is None:
            confirm_type = CONFIRM_TYPE_PENDING
        if order_ids is None:
            order_ids = []
        payload = {
            "confirm_type": confirm_type,
            "receive_account_id": str(receive_account_id),
            "order_ids": order_ids,
        }
        return http.post(cls.RECEIVE_CONFIRM_LIST_URL, json=payload)

    @classmethod
    def confirm_receive_account(
        cls,
        receive_account_id: str,
        confirm_list: List[Dict[str, Any]],
        confirm_type: int = None,
    ) -> Any:
        """
        确认应收对账（accountConfirm）

        Args:
            receive_account_id: 应收对账批次ID
            confirm_list       : 确认列表（来自 receiveConfirmList 响应）
            confirm_type       : 确认类型（默认 CONFIRM_TYPE_PENDING = 0 = 待确认）

        Returns:
            Response 对象
        """
        if confirm_type is None:
            confirm_type = CONFIRM_TYPE_PENDING
        payload = {
            "confirm_type": confirm_type,
            "receive_account_id": str(receive_account_id),
            "confirm_list": confirm_list,
        }
        return http.post(cls.ACCOUNT_CONFIRM_URL, json=payload)

    @classmethod
    def get_receive_account_page(
        cls,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
        bl_nos: List[str] = None,
        sort_field: str = None,
        sort_order: str = None,
    ) -> Any:
        """
        查询应收对账批次分页列表（receiveAccountPage）

        用于确认后验证批次状态已更新。

        Args:
            page_no            : 页码（默认 PAGE_NO_DEFAULT = 1）
            page_size          : 每页数量（默认 PAGE_SIZE_LARGE = 20）
            create_time_start  : 创建时间开始（时间戳秒，默认 1 年前）
            create_time_end    : 创建时间结束（时间戳秒，默认 1 天后）
            bl_nos             : 提单号列表
            sort_field         : 排序字段（默认 SORT_FIELD_CREATE_TIME）
            sort_order         : 排序方向（默认 SORT_ORDER_DESC）

        Returns:
            Response 对象
        """
        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            page_size = PAGE_SIZE_LARGE
        if sort_field is None:
            sort_field = SORT_FIELD_CREATE_TIME
        if sort_order is None:
            sort_order = SORT_ORDER_DESC
        if bl_nos is None:
            bl_nos = []

        import datetime as _dt_module
        if create_time_start is None:
            create_time_start = str(int(_dt_module.datetime.now().timestamp()) - YEAR_OFFSET_SECONDS)
        if create_time_end is None:
            create_time_end = str(int(time.time()) + DAY_OFFSET_SECONDS)

        payload = {
            "page_no": page_no,
            "page_size": page_size,
            "create_time": [int(create_time_start) * TIMESTAMP_MS_FACTOR, int(create_time_end) * TIMESTAMP_MS_FACTOR],
            "bl_nos": bl_nos,
            "sort_field": sort_field,
            "sort_order": sort_order,
            "params": {},
            "create_time_start": create_time_start,
            "create_time_end": create_time_end,
        }
        return http.post(cls.RECEIVE_ACCOUNT_PAGE_URL, json=payload)
