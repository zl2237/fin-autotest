"""
API 层 - 应收开票批次相关接口封装

涉及流程：发起应收开票批次审批（LINK15）
  1. POST /api/finance/accountFee/financePutList          - 查询应收款项列表（开票模式）
  2. POST /api/home/exchangeRate/monthExchangeRate        - 获取汇率
  3. POST /api/finance/receiveInvoiceBatch/getSellInfo  - 获取开票方信息（买家/卖家）
  4. POST /api/Finance/ReceiveInvoiceBatch/batchOrderEdit (action=check)  - 预校验
  5. POST /api/Finance/ReceiveInvoiceBatch/batchOrderEdit (action=submit) - 正式提交
  6. POST /api/Finance/ReceiveInvoiceBatch/batchpage              - 验证批次创建

所有枚举值、常量默认值统一从 data/receive_invoice.yaml 读取，勿在代码中硬编码。
"""
import time
from typing import Dict, Any, List, Optional

from core.http_client import http
from data.receive import (
    OPERATE_TYPE_RECEIVABLE,
    ACCOUNT_TYPE_CROSS_CUSTOMER,
    PAGE_NO_DEFAULT,
    PAGE_SIZE_STANDARD,
    PAGE_SIZE_LARGE,
    YEAR_OFFSET_SECONDS,
    DAY_OFFSET_SECONDS,
    TIMESTAMP_MS_FACTOR,
    SORT_FIELD_CREATE_TIME,
    SORT_ORDER_DESC,
    _RECEIVE_ACCOUNT_CFG,
    _RECEIVE_INVOICE_CFG,
    INVOICE_BATCH_TYPE,
    INVOICE_SEARCH_STYLE,
    INVOICE_ACTION_CHECK,
    INVOICE_ACTION_AUDIT,
    INVOICE_ACTION_SUBMIT,
    INVOICE_STYLE_FORMAL,
    INVOICE_APPLY_TYPE_CROSS,
    INVOICE_USD_TURN_ON,
    INVOICE_USD_TURN_OFF,
    INVOICE_MERGE_CNY_NO,
    INVOICE_RATE_TYPE_SPECIFY,
    INVOICE_DEFAULT_RATE,
    INVOICE_DEFAULT_FORM,
    INVOICE_DEFAULT_TYPE,
    INVOICE_DEFAULT_ITEM,
    INVOICE_FAST_REMARK,
    INVOICE_APPLY_SIMPLE,
    INVOICE_PURCHASER_TAX_NUMBER,
)


def _default_main_id() -> str:
    cfg = _RECEIVE_ACCOUNT_CFG.get("finance_put_list", {})
    return cfg.get("main_id", "1")


def _ri_const(key: str, default):
    return _RECEIVE_INVOICE_CFG.get("_constants", {}).get(key, default) if _RECEIVE_INVOICE_CFG else default


class InvoiceBatchApi:
    """应收开票批次相关 API"""

    FINANCE_PUT_LIST_URL = "/api/finance/accountFee/financePutList"
    MONTH_EXCHANGE_RATE_URL = "/api/home/exchangeRate/monthExchangeRate"
    GET_SELL_INFO_URL = "/api/finance/receiveInvoiceBatch/getSellInfo"
    BATCH_ORDER_EDIT_URL = "/api/Finance/ReceiveInvoiceBatch/batchOrderEdit"
    BATCH_PAGE_URL = "/api/Finance/ReceiveInvoiceBatch/batchpage"

    @classmethod
    def query_finance_put_list_for_invoice(
        cls,
        bl_no: str,
        put_settle_object_id: str,
        main_id: str = None,
        page_no: int = None,
        page_size: int = None,
    ) -> Any:
        """
        查询应收款项列表（开票模式）

        用于构建开票批次申请，search_style="invoice"，batch_type=1。

        Args:
            bl_no                : 提单号
            put_settle_object_id : 托单结算对象ID
            main_id              : 主体ID（默认从 YAML 读取）
            page_no              : 页码（默认 PAGE_NO_DEFAULT）
            page_size            : 每页数量（默认 PAGE_SIZE_STANDARD）

        Returns:
            Response 对象
        """
        if main_id is None:
            main_id = _default_main_id()
        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            from data.receive import PAGE_SIZE_STANDARD
            page_size = PAGE_SIZE_STANDARD

        payload = {
            "page_no": page_no,
            "page_size": page_size,
            "put_settle_object_id": str(put_settle_object_id),
            "main_id": str(main_id),
            "bl_no": bl_no,
            "operate_type": OPERATE_TYPE_RECEIVABLE,
            "batch_type": INVOICE_BATCH_TYPE,
            "search_style": INVOICE_SEARCH_STYLE,
            "customer_id": [],
            "pay_settle_object_id": [],
            "account_type": ACCOUNT_TYPE_CROSS_CUSTOMER,
            "bl_nos": [],
        }
        return http.post(cls.FINANCE_PUT_LIST_URL, json=payload)

    @classmethod
    def get_month_exchange_rate(
        cls,
        main_id: str = None,
        original_currency: str = "USD",
        target_currency: str = "CNY",
    ) -> Any:
        """
        获取月度汇率

        Args:
            main_id           : 主体ID（默认从 YAML 读取）
            original_currency : 原币种
            target_currency  : 目标币种

        Returns:
            Response 对象
        """
        if main_id is None:
            main_id = _default_main_id()
        payload = {
            "main_id": str(main_id),
            "original_currency": original_currency,
            "target_currency": target_currency,
        }
        return http.post(cls.MONTH_EXCHANGE_RATE_URL, json=payload)

    @classmethod
    def get_sell_info(
        cls,
        put_settle_object_id: str,
        put_settle_object: str,
        main_id: str,
        main_name_cn: str,
        order_fee_real_ids: List[str],
        order_sub_ids: List[str],
        sys_rate: str,
        usd_is_turn: str = None,
    ) -> Any:
        """
        获取开票方信息（getSellInfo）

        用于构建 batchOrderEdit 的 usd_require.purchaser_id / seller_id 等字段。
        该接口需在 settleObjectDetail 查询到 purchaser 信息之后调用。

        Args:
            put_settle_object_id : 托单结算对象ID
            put_settle_object    : 托单结算对象名称
            main_id              : 主体ID
            main_name_cn         : 主体中文名称
            order_fee_real_ids   : 费用ID列表（来自 financePutList）
            order_sub_ids        : 子订单ID列表（来自 financePutList）
            sys_rate             : 系统汇率（来自 monthExchangeRate）
            usd_is_turn          : USD 是否转 CNY（USD_TURN_ENABLED / USD_TURN_DISABLED）

        Returns:
            Response 对象（data 为卖家金融账户列表）
        """
        if usd_is_turn is None:
            usd_is_turn = INVOICE_USD_TURN_ON

        payload = {
            "cny_file": [],
            "usd_file": [],
            "debitno_file": [],
            "style": INVOICE_STYLE_FORMAL,
            "apply_type": INVOICE_APPLY_TYPE_CROSS,
            "customer_id": [],
            "customer_name": [put_settle_object],
            "put_settle_object_id": str(put_settle_object_id),
            "main_id": str(main_id),
            "pay_settle_object_id": [],
            "turn_rate": "",
            "merge_with_cny": INVOICE_MERGE_CNY_NO,
            "selectRadio": "",
            "receive_invoice_batch_id": "",
            "batch_apply_name": "",
            "invoice_form": "",
            "invoice_type": "",
            "invoice_items": "",
            "invoice_rate_type": "",
            "rate_type": "",
            "usd_is_turn": usd_is_turn,
            "order_fee_real_id": order_fee_real_ids,
            "usd_requireinvoice_form": "",
            "usd_requireinvoice_type": "",
            "usd_requiretruck_remark": "",
            "usd_requireinvoice_items_count": "",
            "usd_requireinvoice_items": "",
            "usd_requireinvoice_rate": "",
            "usd_requireinvoice_rate_type": "",
            "usd_requireseller_name": "",
            "cny_requireinvoice_form": "",
            "cny_requireinvoice_type": "",
            "cny_requiretruck_remark": "",
            "cny_requireinvoice_items_count": "",
            "cny_requireinvoice_items": "",
            "cny_requireinvoice_rate": "",
            "cny_requireinvoice_rate_type": "",
            "cny_requireseller_name": "",
            "usd_require": {
                "fast_remark": INVOICE_FAST_REMARK,
                "currency": "",
                "amount_total_usd": "",
                "amount_total_cny": "",
                "rate": "",
                "turn_amount_total_cny": "",
                "turn_amount_total_usd": "",
                "turn_amount_total": "",
                "invoice_apply_name": "",
                "invoice_apply_simple": INVOICE_APPLY_SIMPLE,
                "invoice_form": "",
                "invoice_type": "",
                "purchaser_id": "",
                "purchaser_head_cn": "",
                "purchaser_tax_number": INVOICE_PURCHASER_TAX_NUMBER,
                "seller_id": "",
                "seller_name": "",
                "bank_account": "",
                "seller_info": "",
                "invoice_items": "",
                "invoice_rate_type": "",
                "invoice_rate": "",
                "require_other": "",
                "remark": "",
                "rate_list": [],
                "purchaser_name": put_settle_object,
            },
            "cny_require": {
                "fast_remark": INVOICE_FAST_REMARK,
                "currency": "",
                "amount_total_usd": "",
                "amount_total_cny": "",
                "rate": "",
                "turn_amount_total_cny": "",
                "turn_amount_total_usd": "",
                "turn_amount_total": "",
                "invoice_apply_name": "",
                "invoice_apply_simple": INVOICE_APPLY_SIMPLE,
                "invoice_form": "",
                "invoice_type": "",
                "purchaser_id": "",
                "purchaser_head_cn": "",
                "purchaser_tax_number": INVOICE_PURCHASER_TAX_NUMBER,
                "seller_id": "",
                "seller_name": "",
                "bank_account": "",
                "seller_info": "",
                "invoice_items": "",
                "invoice_rate_type": "",
                "invoice_rate": "",
                "require_other": "",
                "remark": "",
                "rate_list": [],
            },
            "usd_file_id": [],
            "cny_file_id": [],
            "debitno_file_id": [],
            "batch_order_remark": [],
            "batch_type": str(INVOICE_BATCH_TYPE),
            "cost_usd": "0.00",
            "cost_cny": "0.00",
            "put_settle_object": put_settle_object,
            "main_name_cn": main_name_cn,
            "order_sub_id": order_sub_ids,
            "sys_rate": sys_rate,
        }
        return http.post(cls.GET_SELL_INFO_URL, json=payload)

    @classmethod
    def batch_order_edit(
        cls,
        action: str,
        put_settle_object_id: str,
        put_settle_object: str,
        main_id: str,
        main_name_cn: str,
        order_fee_real_ids: List[str],
        order_sub_ids: List[str],
        order_sub_customer_ids: List[str],
        usd_require: Dict[str, Any],
        cny_require: Dict[str, Any],
        sys_rate: str = "",
        appoint_rate: str = "",
        cost_usd: str = "0.00",
        cost_cny: str = "0.00",
        rate_type: str = None,
        audit_msg: Dict[str, Any] = None,
        select_node_user: List[Dict[str, Any]] = None,
        receive_invoice_batch_id: str = "",
        fee_currency: str = "USD",
    ) -> Any:
        """
        应收开票批次编辑（预校验 / 触发审批 / 正式提交）

        action=check  : 预校验
        action=audit  : 触发审批流（返回 node_user_ids）
        action=submit : 正式提交开票批次申请

        Args:
            action               : 操作类型
            put_settle_object_id : 托单结算对象ID
            put_settle_object   : 托单结算对象名称
            main_id             : 主体ID
            main_name_cn        : 主体中文名称
            order_fee_real_ids  : 费用ID列表
            order_sub_ids       : 子订单ID列表
            order_sub_customer_ids: 子订单客户ID列表
            usd_require         : USD 开票要求（来自 getSellInfo 响应 + 本地计算）
            cny_require        : CNY 开票要求
            sys_rate           : 系统汇率
            appoint_rate       : 指定汇率
            cost_usd           : 费用合计 USD
            cost_cny           : 费用合计 CNY
            rate_type          : 汇率类型
            audit_msg          : 审批消息（submit 时使用）
            select_node_user   : 审批节点用户（submit 时使用）
            receive_invoice_batch_id: 开票批次ID
            fee_currency       : 费用币种

        Returns:
            Response 对象
        """
        if rate_type is None:
            rate_type = INVOICE_RATE_TYPE_SPECIFY
        if audit_msg is None:
            audit_msg = {}
        if select_node_user is None:
            select_node_user = []

        payload = {
            "cny_file": [],
            "usd_file": [],
            "debitno_file": [],
            "style": INVOICE_STYLE_FORMAL,
            "apply_type": INVOICE_APPLY_TYPE_CROSS,
            "customer_id": [],
            "customer_name": [put_settle_object],
            "put_settle_object_id": str(put_settle_object_id),
            "main_id": str(main_id),
            "pay_settle_object_id": [],
            "turn_rate": appoint_rate,
            "merge_with_cny": INVOICE_MERGE_CNY_NO,
            "selectRadio": "",
            "receive_invoice_batch_id": receive_invoice_batch_id,
            "batch_apply_name": "",
            "invoice_form": "",
            "invoice_type": "",
            "invoice_items": "",
            "invoice_rate_type": "",
            "rate_type": rate_type,
            "usd_is_turn": INVOICE_USD_TURN_ON,
            "order_fee_real_id": order_fee_real_ids,
            "usd_requireinvoice_form": "",
            "usd_requireinvoice_type": "",
            "usd_requiretruck_remark": "",
            "usd_requireinvoice_items_count": "",
            "usd_requireinvoice_items": "",
            "usd_requireinvoice_rate": "",
            "usd_requireinvoice_rate_type": "",
            "usd_requireseller_name": "",
            "cny_requireinvoice_form": "",
            "cny_requireinvoice_type": "",
            "cny_requiretruck_remark": "",
            "cny_requireinvoice_items_count": "",
            "cny_requireinvoice_items": "",
            "cny_requireinvoice_rate": "",
            "cny_requireinvoice_rate_type": "",
            "cny_requireseller_name": "",
            "usd_require": usd_require,
            "cny_require": cny_require,
            "usd_file_id": [],
            "cny_file_id": [],
            "debitno_file_id": [],
            "batch_order_remark": [
                {"order_sub_id": sid, "currency": fee_currency}
                for sid in order_sub_ids
            ] if action == INVOICE_ACTION_SUBMIT else [],
            "batch_type": str(INVOICE_BATCH_TYPE),
            "cost_usd": cost_usd,
            "cost_cny": cost_cny,
            "put_settle_object": put_settle_object,
            "main_name_cn": main_name_cn,
            "order_sub_id": order_sub_ids,
            "sys_rate": sys_rate,
            "appoint_rate": appoint_rate,
            "action": action,
            "fee_currency": fee_currency,
            "order_sub_customer_id": order_sub_customer_ids,
            "audit_msg": audit_msg,
            "select_node_user": select_node_user,
        }
        return http.post(cls.BATCH_ORDER_EDIT_URL, json=payload)

    @classmethod
    def query_batch_page(
        cls,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
        sort_field: str = None,
        sort_order: str = None,
        bl_no: str = None,
    ) -> Any:
        """
        查询应收开票批次分页列表

        用于确认后验证批次状态。

        Args:
            page_no            : 页码（默认 1）
            page_size          : 每页数量（默认 PAGE_SIZE_LARGE = 20）
            create_time_start  : 创建时间开始（时间戳秒，默认 1 年前）
            create_time_end    : 创建时间结束（时间戳秒，默认 1 天后）
            sort_field         : 排序字段（默认 create_time）
            sort_order         : 排序方向（默认 desc）
            bl_no              : 提单号（可选，用于精确查询）

        Returns:
            Response 对象
        """
        import datetime as _dt_module
        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            page_size = PAGE_SIZE_LARGE
        if sort_field is None:
            sort_field = SORT_FIELD_CREATE_TIME
        if sort_order is None:
            sort_order = SORT_ORDER_DESC
        if create_time_start is None:
            create_time_start = str(int(_dt_module.datetime.now().timestamp()) - YEAR_OFFSET_SECONDS)
        if create_time_end is None:
            create_time_end = str(int(time.time()) + DAY_OFFSET_SECONDS)

        params = {}
        if bl_no:
            params["bl_no"] = bl_no

        payload = {
            "page_no": page_no,
            "page_size": page_size,
            "order_no": "",
            "create_time": [int(create_time_start) * TIMESTAMP_MS_FACTOR, int(create_time_end) * TIMESTAMP_MS_FACTOR],
            "sort_field": sort_field,
            "sort_order": sort_order,
            "params": params,
            "create_time_start": create_time_start,
            "create_time_end": create_time_end,
        }
        return http.post(cls.BATCH_PAGE_URL, json=payload)
