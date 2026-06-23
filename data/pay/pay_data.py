"""
数据层 - 付款（Pay）域

包含：
  - pay_account.yaml / payable_invoice.yaml 配置 loader
  - 应付对账批次模块级常量（OPERATE_TYPE / ACCOUNT_TYPE 等）
  - PayableAccountData   应付对账（link19 / link20）
  - PayableInvoiceData   应付开票申请（link21）

API 层对应：api/pay/ 子包
"""
from pathlib import Path
from typing import Any, Dict, List

import json
import yaml


# ========================================================================
# YAML 加载（每个阶段/链路对应独立 YAML 文件）
# ========================================================================

def _load_yaml(name: str) -> Dict[str, Any]:
    path = Path(__file__).parent / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# payable_account.yaml - link19 / link20（应付对账批次 + 确认应付对账）
# payable_invoice.yaml - link21（发起应付开票申请）
# payable_invoice_upload.yaml - link22（应付发票上传与登记）
_CFG = _load_yaml("pay_account")
_INV_CFG = _load_yaml("payable_invoice")
_UPLOAD_CFG = _load_yaml("payable_invoice_upload")
_CONST = _CFG.get("_constants", {}) if _CFG else {}
_INV_CONST = _INV_CFG.get("_constants", {}) if _INV_CFG else {}


# ========================================================================
# 共享基础常量（pay_account.yaml 与 payable_invoice.yaml 各自维护一份同值常量，
# 加载时优先 payable_invoice.yaml；pay_account.yaml 作为回退）
# ========================================================================

def _shared_const(key: str, default: Any) -> Any:
    """优先 payable_invoice.yaml，再 pay_account.yaml，最后默认值"""
    if key in _INV_CONST:
        return _INV_CONST[key]
    if key in _CONST:
        return _CONST[key]
    return default


OPERATE_TYPE_BILL_OF_LADING = _shared_const("operate_type", 1)
ACCOUNT_TYPE_CROSS_CUSTOMER = _shared_const("account_type", "2")

PAGE_NO_DEFAULT = _shared_const("page_no", 1)
PAGE_SIZE_STANDARD = _shared_const("page_size", 50)
SORT_FIELD_CREATE_TIME = _shared_const("sort_field", "create_time")
SORT_ORDER_DESC = _shared_const("sort_order_desc", "desc")
YEAR_OFFSET_SECONDS = _shared_const("page_year_offset", 365) * 86400

# -- payable account (LK19 / LK20) --
PAY_ACCOUNT_ACTION_SUBMIT = (
    _CFG.get("order_pay_account_edit", {}).get("action_submit", "submit")
)
PAY_ACCOUNT_PAGE_ACCOUNT_STATUS = (
    _CFG.get("pay_account_page", {}).get("account_status", ["1"])
)
ACCOUNT_CONFIRM_TYPE = _CFG.get("account_confirm", {}).get("confirm_type", 0)
ACCOUNT_CONFIRM_QUICK_STATUS = _CFG.get("account_confirm", {}).get("quick_status", 1)

# -- payable invoice apply (LK21) -- 全部从 payable_invoice.yaml 读取
FPL_INVOICE_SEARCH_STYLE = (
    _INV_CFG.get("finance_pay_list_invoice", {}).get("search_style", "invoice")
)
FPL_INVOICE_BATCH_TYPE = (
    _INV_CFG.get("finance_pay_list_invoice", {}).get("batch_type", 1)
)
GOBI_DEFAULT_EXCHANGE_RATE = _INV_CFG.get("get_order_info_by_fee_id", {}).get("default_exchange_rate", 7)
GOBI_USD_INVOICE_REMARK = _INV_CFG.get("get_order_info_by_fee_id", {}).get("usd_invoice_remark", 0)
GOBI_STYLE = _INV_CFG.get("get_order_info_by_fee_id", {}).get("style", 1)
GOBI_INVOICE_APPLY_SIMPLE = _INV_CFG.get("get_order_info_by_fee_id", {}).get("invoice_apply_simple", "")

_boe_pay = _INV_CFG.get("batch_order_edit_pay", {})
BOE_PAY_ACTION = _boe_pay.get("action_submit", "submit")
BOE_PAY_APPLY_TYPE = _boe_pay.get("apply_type", "2")
BOE_PAY_BATCH_TYPE = _boe_pay.get("batch_type", "1")
BOE_PAY_MERGE_WITH_CNY = _boe_pay.get("merge_with_cny", "2")
BOE_PAY_USD_IS_TURN = _boe_pay.get("usd_is_turn", "2")
BOE_PAY_RATE_TYPE = _boe_pay.get("rate_type", "3")
BOE_PAY_INVOICE_FORM = _boe_pay.get("invoice_form", "1")
BOE_PAY_INVOICE_TYPE = _boe_pay.get("invoice_type", "1")
BOE_PAY_INVOICE_ITEM = _boe_pay.get("invoice_item", "2")
BOE_PAY_INVOICE_ITEM_NAME = _boe_pay.get("invoice_item_name", "国际货物运输代理海运费")
BOE_PAY_DEFAULT_INVOICE_RATE = _boe_pay.get("default_invoice_rate", 6)
BOE_PAY_DEFAULT_EXCHANGE_RATE = _boe_pay.get("default_exchange_rate", "7")
BOE_PAY_APPOINT_RATE = _boe_pay.get("appoint_rate", "7")
BOE_PAY_SYS_RATE = _boe_pay.get("sys_rate", "")
BOE_PAY_REMARK = _boe_pay.get("remark", "—")
BOE_PAY_REQUIRE_OTHER = _boe_pay.get("require_other", "暂无要求")
BOE_PAY_INVOICE_APPLY_NAME_PATTERN = _boe_pay.get(
    "invoice_apply_name_pattern", "{main_name} + {pay_settle_object} + {month} + USD {amount}"
)
BOE_PAY_INVOICE_APPLY_SIMPLE = _boe_pay.get("invoice_apply_simple", "")
BOE_PAY_FAST_REMARK = _boe_pay.get("fast_remark", "[]")
BOE_PAY_PURCHASER_TAX_NUMBER = _boe_pay.get("purchaser_tax_number", "")
BOE_PAY_BATCH_ORDER_REMARK = _boe_pay.get("batch_order_remark", "test_remark")


# ========================================================================
# 应付对账批次 - 发起应付对账批次接口（LK19）
# ========================================================================
# 链路结构：
#   step1: financePayList       - 按提单号查询应付项列表（提取 amount_list）
#   step2: orderPayAccountEdit  - 发起应付对账批次（提交 select_list）
# ========================================================================

class PayableAccountData:

    @classmethod
    def get_finance_pay_list_payload(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Dict[str, Any]:
        """
        构建 financePayList 查询请求体（按 bl_no 查询应付项）

        Args:
            bl_no              : 提单号（精确查询，来自上游链路）
            page_no            : 页码（默认 PAGE_NO_DEFAULT）
            page_size          : 每页数量（默认 PAGE_SIZE_STANDARD）
            create_time_start  : 创建时间开始（Unix 秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 秒，默认 1 年后）

        Returns:
            请求体字典
        """
        import time as _time

        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            page_size = PAGE_SIZE_STANDARD
        if create_time_start is None:
            create_time_start = str(int(_time.time()) - YEAR_OFFSET_SECONDS)
        if create_time_end is None:
            create_time_end = str(int(_time.time()) + YEAR_OFFSET_SECONDS)

        pay_cfg = _CFG.get("finance_pay_list", {}) if _CFG else {}
        return {
            "page_no": page_no,
            "page_size": page_size,
            "bl_no": str(bl_no),
            "operate_type": OPERATE_TYPE_BILL_OF_LADING,
            "search_style": pay_cfg.get("search_style", "account"),
            "account_simple_name": pay_cfg.get("account_simple_name"),
            "account_type": ACCOUNT_TYPE_CROSS_CUSTOMER,
            "customer_id": pay_cfg.get("customer_id"),
            "put_settle_object_id": pay_cfg.get("put_settle_object_id"),
            "main_id": pay_cfg.get("main_id"),
            "pay_settle_object_id": pay_cfg.get("pay_settle_object_id"),
            "bl_nos": [],
        }

    @classmethod
    def build_select_list_from_pay_list(
        cls,
        pay_list_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        从 financePayList 响应 data.data 中提取 amount_list，
        重组为 orderPayAccountEdit 所需的 select_list 结构。

        该方法直接透传 financePayList 响应中的所有字段，
        不对字段值做任何转换，确保与后端期望完全一致。

        Args:
            pay_list_data: financePayList 响应中的 data 字典

        Returns:
            select_list 列表（包含 order 和 amount_list）
        """
        result = []
        records = pay_list_data.get("data", [])
        for record in records:
            amount_list = record.get("amount_list", [])
            result.append({
                # -- order 级别字段 --
                "order_id": record.get("order_id"),
                "order_no": record.get("order_no"),
                "bl_no": record.get("bl_no"),
                "customer_id": record.get("customer_id"),
                "customer_name": record.get("customer_name"),
                "customer_main_id": record.get("customer_main_id"),
                "customer_main_name": record.get("customer_main_name"),
                "business_main_id": record.get("business_main_id"),
                "business_main_name": record.get("business_main_name"),
                "policy_type": record.get("policy_type"),
                "trade_term": record.get("trade_term"),
                "customer_period": record.get("customer_period"),
                "customer_put_date": record.get("customer_put_date"),
                "atd": record.get("atd"),
                "etd": record.get("etd"),
                "create_time": record.get("create_time"),
                "finance_date": record.get("finance_date"),
                "ship_name": record.get("ship_name"),
                "voy": record.get("voy"),
                "fund_name": record.get("fund_name"),
                "status": record.get("status"),
                "is_special_pay": record.get("is_special_pay"),
                "pay_status": record.get("pay_status"),
                "is_loan_before_invoice": record.get("is_loan_before_invoice"),
                "customer_order_sn": record.get("customer_order_sn"),
                "order_sub_id": record.get("order_sub_id"),
                "order_sub_no": record.get("order_sub_no"),
                "main_id": record.get("main_id"),
                "main_name": record.get("main_name"),
                "currency": record.get("currency"),
                "amount_total": record.get("amount_total"),
                "service_project": record.get("service_project"),
                "pay_settle_object_type": record.get("pay_settle_object_type"),
                "real_settle_object_id": record.get("real_settle_object_id"),
                "real_settle_object": record.get("real_settle_object"),
                "put_settle_object": record.get("put_settle_object"),
                "put_settle_object_id": record.get("put_settle_object_id"),
                "pay_settle_object": record.get("pay_settle_object"),
                "pay_settle_object_id": record.get("pay_settle_object_id"),
                "book_supplier_period": record.get("book_supplier_period"),
                "book_supplier_pay_date": record.get("book_supplier_pay_date"),
                "book_supplier_name": record.get("book_supplier_name"),
                "operable_amount": record.get("operable_amount"),
                "un_operable_amount": record.get("un_operable_amount"),
                "operable_flag": record.get("operable_flag"),
                "order_sub_currency": record.get("order_sub_currency"),
                "order_main_finance": record.get("order_main_finance"),
                "order_error_messages": record.get("order_error_messages", []),
                "order_error_message": record.get("order_error_message", ""),
                "order_error_flag": record.get("order_error_flag", False),
                # -- amount_list（来自 financePayList 响应，含 order_fee_real_id）--
                "amount_list": amount_list,
            })
        return result

    @classmethod
    def get_pay_account_page_payload(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
        account_status: List[str] = None,
    ) -> Dict[str, Any]:
        """
        构建 payAccountPage 查询请求体（按 bl_no 查询应付对账批次状态）

        Args:
            bl_no              : 提单号（精确查询，来自上游链路）
            page_no            : 页码（默认 PAGE_NO_DEFAULT）
            page_size          : 每页数量（默认 PAGE_SIZE_STANDARD）
            create_time_start  : 创建时间开始（Unix 秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 秒，默认 1 年后）
            account_status     : 账户状态列表（默认 ["1"]=对账中）

        Returns:
            请求体字典
        """
        import time as _time

        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            page_size = PAGE_SIZE_STANDARD
        if create_time_start is None:
            create_time_start = str(int(_time.time()) - YEAR_OFFSET_SECONDS)
        if create_time_end is None:
            create_time_end = str(int(_time.time()) + YEAR_OFFSET_SECONDS)
        if account_status is None:
            account_status = list(PAY_ACCOUNT_PAGE_ACCOUNT_STATUS)

        return {
            "page_no": page_no,
            "page_size": page_size,
            "create_time": [
                int(create_time_start) * 1000,
                int(create_time_end) * 1000,
            ],
            "customer_id": [],
            "account_status": account_status,
            "currency": [],
            "create_id": [],
            "account_by": [],
            "bl_nos": [str(bl_no)],
            "sort_field": SORT_FIELD_CREATE_TIME,
            "sort_order": SORT_ORDER_DESC,
            "params": {},
            "create_time_start": create_time_start,
            "create_time_end": create_time_end,
        }

    @classmethod
    def get_account_confirm_payload(
        cls,
        pay_account_id: str,
        confirm_type: int = None,
        quick_status: int = None,
    ) -> Dict[str, Any]:
        """
        构建 accountConfirm 确认应付对账请求体。

        Args:
            pay_account_id : 应付对账批次ID（来自 orderPayAccountEdit 响应）
            confirm_type   : 确认类型（默认 ACCOUNT_CONFIRM_TYPE=0）
            quick_status   : 快捷确认标识（默认 ACCOUNT_CONFIRM_QUICK_STATUS=1）

        Returns:
            请求体字典
        """
        if confirm_type is None:
            confirm_type = ACCOUNT_CONFIRM_TYPE
        if quick_status is None:
            quick_status = ACCOUNT_CONFIRM_QUICK_STATUS

        return {
            "confirm_type": confirm_type,
            "pay_account_id": str(pay_account_id),
            "quick_status": quick_status,
            "confirm_list": [],
        }


class PayableInvoiceData:
    """
    应付开票申请（LK21）数据类

    涉及 3 个接口：
      1. financePayList（开票模式）  - 按 bl_no 查询应付开票项列表
      2. getOrderInfoByFeeId         - 按 order_fee_real_id 列表查询开票订单详情
      3. batchOrderEdit              - 提交应付开票批次申请（apply_type=2，submit 即生效）
    """

    @classmethod
    def get_finance_pay_list_invoice_payload(
        cls,
        bl_no: str,
        main_id: str = None,
        pay_settle_object_id: str = None,
        pay_settle_object: str = None,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Dict[str, Any]:
        """
        构建 financePayList（开票模式）的请求体

        与 link19 的发起应付对账批次共用同一接口，
        仅 search_style / batch_type 不同（开票模式）。

        注意：main_id / pay_settle_object_id / pay_settle_object 三个字段**必填**，
        但**优先级**为：
          1. 显式入参（来自上游 confirm_payable_result）
          2. YAML 默认配置（data/pay/payable_invoice.yaml 的
             finance_pay_list_invoice.{main_id,pay_settle_object_id,pay_settle_object}）
          3. 都没有则抛 AssertionError
        缺一不可，否则 financePayList 会按全量 fee 返回，
        导致后续 batchOrderEdit 返回 406。
        参考请求体：
          {"page_no":1,"page_size":50,"bl_no":"","bl_nos":[...],
           "main_id":"6","pay_settle_object_id":"92102",
           "pay_settle_object":"芜湖长信科技股份有限公司",
           "operate_type":1,"batch_type":1,"search_style":"invoice",
           "customer_id":[],"put_settle_object_id":[],"account_type":"2"}

        Args:
            bl_no               : 提单号（来自上游链路）
            main_id             : 主体ID（可选，缺省时从 YAML 读取）
            pay_settle_object_id: 付款结算对象ID（可选，缺省时从 YAML 读取）
            pay_settle_object   : 付款结算对象名称（可选，缺省时从 YAML 读取）
            page_no             : 页码
            page_size           : 每页数量
            create_time_start   : 创建时间开始（Unix 秒）
            create_time_end     : 创建时间结束（Unix 秒）

        Returns:
            请求体字典
        """
        # 优先级：入参 > YAML > 报错
        _inv_cfg = _INV_CFG.get("finance_pay_list_invoice", {}) if _INV_CFG else {}
        resolved_main_id = main_id if main_id else _inv_cfg.get("main_id", "")
        resolved_pay_settle_object_id = (
            pay_settle_object_id if pay_settle_object_id
            else _inv_cfg.get("pay_settle_object_id", "")
        )
        resolved_pay_settle_object = (
            pay_settle_object if pay_settle_object
            else _inv_cfg.get("pay_settle_object", "")
        )

        if not resolved_main_id or not resolved_pay_settle_object_id or not resolved_pay_settle_object:
            raise AssertionError(
                f'financePayList（开票模式）必填字段缺失: '
                f'main_id={resolved_main_id!r}, '
                f'pay_settle_object_id={resolved_pay_settle_object_id!r}, '
                f'pay_settle_object={resolved_pay_settle_object!r}。'
                f'请通过以下方式之一提供：'
                f'(1) 调用方传入显式入参；'
                f'(2) 在 data/pay/payable_invoice.yaml 的 finance_pay_list_invoice 块中配置默认值。'
                f'否则 financePayList 会按全量 fee 返回数据，'
                f'间接导致后续 batchOrderEdit 返回 406。'
            )

        import time as _time

        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            page_size = PAGE_SIZE_STANDARD
        if create_time_start is None:
            create_time_start = str(int(_time.time()) - YEAR_OFFSET_SECONDS)
        if create_time_end is None:
            create_time_end = str(int(_time.time()) + YEAR_OFFSET_SECONDS)

        return {
            "page_no": page_no,
            "page_size": page_size,
            "bl_no": str(bl_no),
            "bl_nos": [str(bl_no)],
            "main_id": str(resolved_main_id),
            "pay_settle_object_id": str(resolved_pay_settle_object_id),
            "pay_settle_object": str(resolved_pay_settle_object),
            "operate_type": OPERATE_TYPE_BILL_OF_LADING,
            "search_style": FPL_INVOICE_SEARCH_STYLE,
            "batch_type": FPL_INVOICE_BATCH_TYPE,
            "account_type": ACCOUNT_TYPE_CROSS_CUSTOMER,
            "customer_id": [],
            "put_settle_object_id": [],
        }

    @classmethod
    def get_order_info_by_fee_id_payload(
        cls,
        order_fee_real_ids: List[str],
        exchange_rate: Any = None,
        usd_invoice_remark: int = None,
        style: int = None,
    ) -> Dict[str, Any]:
        """
        构建 getOrderInfoByFeeId 请求体

        Args:
            order_fee_real_ids : 费用实付 ID 列表（来自 financePayList 响应）
            exchange_rate      : 汇率（默认 GOBI_DEFAULT_EXCHANGE_RATE）
            usd_invoice_remark : 备注模式（默认 GOBI_USD_INVOICE_REMARK=0）
            style              : 模式（默认 GOBI_STYLE=1）

        Returns:
            请求体字典
        """
        if exchange_rate is None:
            exchange_rate = GOBI_DEFAULT_EXCHANGE_RATE
        if usd_invoice_remark is None:
            usd_invoice_remark = GOBI_USD_INVOICE_REMARK
        if style is None:
            style = GOBI_STYLE

        return {
            "order_fee_real_id": [str(x) for x in order_fee_real_ids],
            "exchange_rate": exchange_rate,
            "usd_invoice_remark": usd_invoice_remark,
            "style": style,
        }

    @classmethod
    def build_batch_order_edit_pay_payload(
        cls,
        order_info_data_list: List[Dict[str, Any]],
        finance_pay_records: List[Dict[str, Any]],
        main_id: str,
        main_name: str,
        pay_settle_object: str,
        pay_settle_object_id: str,
        exchange_rate: Any = None,
        customer_id: str = None,
        customer_name: str = None,
        batch_order_remark: str = None,
        action: str = None,
    ) -> Dict[str, Any]:
        """
        构建 batchOrderEdit（apply_type=2 应付）提交请求体

        1. 费率列表 rate_list 由 order_info_data_list 推导
           （订单信息包含 fee_real_name / fee_real_no / cost_no / real_amount 等）
        2. seller_info 从 order_info_data_list 中提取 supplier finance 信息
        3. 总额汇总 amount_total_usd / cost_usd 等

        Args:
            order_info_data_list    : getOrderInfoByFeeId 响应 data 列表
            finance_pay_records     : financePayList 响应 data 列表（用于 selectRadio / amount_total）
            main_id                 : 主体ID（来自上游链路）
            main_name               : 主体名称
            pay_settle_object       : 付款结算对象名称
            pay_settle_object_id    : 付款结算对象ID
            exchange_rate           : 汇率（默认 BOE_PAY_DEFAULT_EXCHANGE_RATE）
            customer_id             : 客户ID（取自 financePayList 第一条记录的 customer_id）
            customer_name           : 客户名称（取自 financePayList 第一条记录的 customer_name）
            batch_order_remark      : 批次备注
            action                  : 操作类型（默认 submit，提交即生效）

        Returns:
            请求体字典
        """
        if action is None:
            action = BOE_PAY_ACTION
        if exchange_rate is None:
            exchange_rate = BOE_PAY_DEFAULT_EXCHANGE_RATE
        if batch_order_remark is None:
            batch_order_remark = BOE_PAY_BATCH_ORDER_REMARK

        # 兜底：customer 从 finance_pay_records 第一条取
        first_pay_record = finance_pay_records[0] if finance_pay_records else {}
        if not customer_id:
            customer_id = str(first_pay_record.get("customer_id", ""))
        if not customer_name:
            customer_name = first_pay_record.get("customer_name", "")
        if not customer_id:
            customer_id = ""

        # 提取 order_fee_real_id 列表 + 订单 sub_id 列表 + 客户 id 列表
        order_fee_real_id_list = [
            str(item.get("order_fee_real_id", ""))
            for item in order_info_data_list
        ]
        order_sub_id_list = []
        order_sub_customer_id_list = []
        for item in order_info_data_list:
            sub_id = str(item.get("order_sub_id", ""))
            if sub_id and sub_id not in order_sub_id_list:
                order_sub_id_list.append(sub_id)
            cust_id = str(item.get("customer_id", ""))
            if cust_id and cust_id not in order_sub_customer_id_list:
                order_sub_customer_id_list.append(cust_id)

        # 总额合计（USD）
        amount_total_usd = 0.0
        for item in order_info_data_list:
            try:
                amount_total_usd += float(item.get("real_amount", 0) or 0)
            except (TypeError, ValueError):
                pass
        amount_total_usd = round(amount_total_usd, 2)

        # seller_info（取第一条记录的 supplier finance 信息）
        first_item = order_info_data_list[0] if order_info_data_list else {}
        seller_info = {
            "supplier_finance_id": str(first_item.get("book_supplier_id", "")),
            "supplier_id": str(first_item.get("book_supplier_id", "")),
            "chinese_header": first_item.get("book_supplier_name", ""),
            "english_header": first_item.get("book_supplier_name", ""),
            "identifier_no": "",
            "phone": "",
            "currency": first_item.get("currency", "USD"),
            "bank_account": first_item.get("bank_account_usd", ""),
            "swift_code": "",
            "register_address": "",
            "open_bank_cn": first_item.get("open_bank_usd", ""),
            "remark": "",
        }
        seller_id = str(first_item.get("book_supplier_id", ""))

        # purchaser 信息（来自 main_id / main_name）
        purchaser_head_cn = main_name
        purchaser_tax_number = BOE_PAY_PURCHASER_TAX_NUMBER

        # 申请批次名（{main_name} + {pay_settle_object} + {YYYY-MM} + USD {amount}）
        try:
            from datetime import datetime as _dt
            month_str = _dt.fromtimestamp(int(_dt.now().timestamp())).strftime("%Y-%m")
        except Exception:
            month_str = "2026-05"
        invoice_apply_name = BOE_PAY_INVOICE_APPLY_NAME_PATTERN.format(
            main_name=main_name,
            pay_settle_object=pay_settle_object,
            month=month_str,
            amount=f"{amount_total_usd:.2f}",
        )

        # rate_list
        rate_list = []
        for idx, item in enumerate(order_info_data_list):
            rate_list.append({
                "cost_name": item.get("fee_real_name") or item.get("cost_name", ""),
                "fee_real_no": item.get("fee_real_no", ""),
                "cost_no": item.get("cost_no", ""),
                "invoice_rate": str(BOE_PAY_DEFAULT_INVOICE_RATE),
                "real_amount": str(item.get("real_amount", "0.00")),
                "currency": item.get("currency", "USD"),
                "invoice_item": BOE_PAY_INVOICE_ITEM,
                "amount_error_flag": False,
                "rowIndex": idx,
                "invoice_item_name": BOE_PAY_INVOICE_ITEM_NAME,
            })

        # usd_require 块（与 link15 模板对齐，currency=USD）
        rate_float = float(exchange_rate)
        usd_require = {
            "fast_remark": BOE_PAY_FAST_REMARK,
            "currency": "USD",
            "amount_total_usd": amount_total_usd,
            "amount_total_cny": "",
            "rate": rate_float,
            "turn_amount_total_cny": f"{amount_total_usd * rate_float:.2f}",
            "turn_amount_total_usd": "",
            "turn_amount_total": f"{amount_total_usd * rate_float:.2f}",
            "invoice_apply_name": invoice_apply_name,
            "invoice_apply_simple": BOE_PAY_INVOICE_APPLY_SIMPLE,
            "invoice_form": BOE_PAY_INVOICE_FORM,
            "invoice_type": BOE_PAY_INVOICE_TYPE,
            "purchaser_id": str(main_id),
            "purchaser_head_cn": purchaser_head_cn,
            "purchaser_tax_number": purchaser_tax_number,
            "seller_id": seller_id,
            "seller_name": first_item.get("book_supplier_name", ""),
            "bank_account": "",
            "seller_info": json.dumps(seller_info, ensure_ascii=False),
            "invoice_items": [],
            "invoice_rate_type": None,
            "invoice_rate": None,
            "require_other": BOE_PAY_REQUIRE_OTHER,
            "remark": BOE_PAY_REMARK,
            "rate_list": rate_list,
            "purchaser_name": purchaser_head_cn,
        }

        cny_require = {
            "fast_remark": "[]",
            "currency": "",
            "amount_total_usd": "",
            "amount_total_cny": "",
            "rate": "",
            "turn_amount_total_cny": "",
            "turn_amount_total_usd": "",
            "turn_amount_total": "",
            "invoice_apply_name": "",
            "invoice_apply_simple": BOE_PAY_INVOICE_APPLY_SIMPLE,
            "invoice_form": "",
            "invoice_type": "",
            "purchaser_id": "",
            "purchaser_head_cn": "",
            "purchaser_tax_number": "",
            "seller_id": "",
            "seller_name": "",
            "bank_account": "",
            "seller_info": "",
            "invoice_items": "",
            "invoice_rate_type": "",
            "invoice_rate": "",
            "require_other": "",
            "remark": "—",
            "rate_list": [],
        }

        # batch_order_remark 块（每个 sub_id 一条）
        remark_list = []
        for sub_id in order_sub_id_list:
            remark_list.append({
                "order_sub_id": sub_id,
                "remark": batch_order_remark,
                "currency": "USD",
            })

        return {
            "cny_file": [],
            "usd_file": [],
            "style": BOE_PAY_INVOICE_FORM,
            "apply_type": BOE_PAY_APPLY_TYPE,
            "customer_id": [customer_id] if customer_id else [],
            "customer_name": [customer_name] if customer_name else [],
            "put_settle_object_id": [],
            "main_id": str(main_id),
            "pay_settle_object_id": str(pay_settle_object_id),
            "turn_rate": "",
            "merge_with_cny": BOE_PAY_MERGE_WITH_CNY,
            "selectRadio": "",
            "pay_invoice_batch_id": "",
            "batch_apply_name": "",
            "invoice_form": "",
            "invoice_type": "",
            "invoice_items": "",
            "invoice_rate_type": "",
            "rate_type": BOE_PAY_RATE_TYPE,
            "usd_is_turn": BOE_PAY_USD_IS_TURN,
            "order_fee_real_id": order_fee_real_id_list,
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
            "batch_order_remark": remark_list,
            "batch_type": BOE_PAY_BATCH_TYPE,
            "cost_usd": f"{amount_total_usd:.2f}",
            "cost_cny": "0.00",
            "main_name_cn": main_name,
            "pay_settle_object": pay_settle_object,
            "order_sub_id": order_sub_id_list,
            "sys_rate": BOE_PAY_SYS_RATE,
            "appoint_rate": str(BOE_PAY_APPOINT_RATE),
            "action": action,
            "fee_currency": "USD",
            "order_sub_customer_id": order_sub_customer_id_list,
            "audit_msg": {
                "title": "开票批次ID",
                "code": None,
                "msgs": ["应付开票批次申请"],
            },
            "select_node_user": [],
        }


# ========================================================================
# 应付发票上传与登记 - 常量（LK22）
# ========================================================================

_PIUP_CONST = _UPLOAD_CFG.get("_constants", {}) if _UPLOAD_CFG else {}
_PIUP_UPLOAD = _UPLOAD_CFG.get("upload_file", {}) if _UPLOAD_CFG else {}
_PIUP_APPLY_PAGE = _UPLOAD_CFG.get("apply_page", {}) if _UPLOAD_CFG else {}
_PIUP_BUYER = _UPLOAD_CFG.get("buyer", {}) if _UPLOAD_CFG else {}
_PIUP_SELLER = _UPLOAD_CFG.get("seller", {}) if _UPLOAD_CFG else {}

PIUP_INVOICE_TYPE = _PIUP_CONST.get("invoice_type", "1")
PIUP_INVOICE_TYPE_NAME = _PIUP_CONST.get("invoice_type_name", "增值税数电普通发票")
PIUP_INVOICE_AMOUNT = _PIUP_CONST.get("invoice_amount", "1500")
PIUP_INVOICE_TAX_AMOUNT = _PIUP_CONST.get("invoice_tax_amount", "0.00")
PIUP_EXCHANGE_RATE = _PIUP_CONST.get("invoice_exchange_rate", "7.0000")
PIUP_USD_AMOUNT = _PIUP_CONST.get("usd_amount", "1500")
PIUP_BUYER_IDENTITY = _PIUP_CONST.get("buyer_identity", "main")
PIUP_SELLER_IDENTITY = _PIUP_CONST.get("seller_identity", "supplier")
PIUP_UPLOAD_PAGE = _PIUP_CONST.get("upload_page", "pay")
PIUP_PAGE_NO = _PIUP_CONST.get("page_no", 1)
PIUP_PAGE_SIZE = _PIUP_CONST.get("page_size", 20)
PIUP_SORT_FIELD = _PIUP_CONST.get("sort_field", "create_time")
PIUP_SORT_ORDER_DESC = _PIUP_CONST.get("sort_order_desc", "desc")
PIUP_ALLOCATION_CURRENCY = _PIUP_CONST.get("currency", "USD")

PIUP_INVOICE_FILENAME = _PIUP_UPLOAD.get("filename", "pay_invoice.pdf")

PIUP_BUYER_CHINESE_HEADER = _PIUP_BUYER.get("chinese_header", "")
PIUP_BUYER_IDENTIFIER_NO = _PIUP_BUYER.get("identifier_no", "")
PIUP_SELLER_CHINESE_HEADER = _PIUP_SELLER.get("chinese_header", "")
PIUP_SELLER_IDENTIFIER_NO = _PIUP_SELLER.get("identifier_no", "")


# ========================================================================
# 应付发票上传与登记 - 数据构建（LK22）
# ========================================================================

class PayableInvoiceUploadData:

    @classmethod
    def get_invoice_file_path(cls) -> str:
        """
        返回应付发票文件的绝对路径，从 YAML 配置读取文件名拼接而来。
        """
        import os as _os
        _attachment_dir = _os.path.join(_os.path.dirname(__file__), "..", "attachment")
        return _os.path.join(_attachment_dir, PIUP_INVOICE_FILENAME)

    @classmethod
    def build_invoice_add_payload(
        cls,
        file_id: str,
        file_name: str,
        file_url: str,
        original_name: str,
        invoice_number: str,
        invoice_amount: str = None,
        buyer_chinese_header: str = None,
        buyer_identifier_no: str = None,
        seller_chinese_header: str = None,
        seller_identifier_no: str = None,
        invoice_date: int = None,
    ) -> Dict[str, Any]:
        """
        构建 invoiceAdd 请求体（应付发票登记）

        返回列表结构（与 receive 侧 invoiceAdd 保持一致）：
          [{"invoice_number": ..., "invoice_type": ..., ...}]

        Args:
            file_id               : 上传后的文件ID
            file_name             : 上传后的文件名
            file_url             : 上传后的文件URL
            original_name         : 原始文件名
            invoice_number        : 发票号码（必须唯一，由调用方生成）
            invoice_amount        : 发票金额（默认 PIUP_INVOICE_AMOUNT）
            buyer_chinese_header : 购买方名称（默认 PIUP_BUYER_CHINESE_HEADER）
            buyer_identifier_no  : 购买方税号（默认 PIUP_BUYER_IDENTIFIER_NO）
            seller_chinese_header: 销售方名称（默认 PIUP_SELLER_CHINESE_HEADER）
            seller_identifier_no : 销售方税号（默认 PIUP_SELLER_IDENTIFIER_NO）
            invoice_date         : 发票日期（默认当天 00:00:00 Unix 秒）

        Returns:
            请求体列表（单元素 list）
        """
        import time as _time
        from datetime import datetime as _dt

        if invoice_amount is None:
            invoice_amount = PIUP_INVOICE_AMOUNT
        if invoice_date is None:
            now = _dt.now()
            invoice_date = int(_dt(now.year, now.month, now.day).timestamp())

        invoice_original = {
            "file_id": str(file_id),
            "file_name": str(file_name),
            "file_type": "pdf",
            "original_name": str(original_name),
            "file_url": str(file_url),
        }

        buyer_identity = PIUP_BUYER_IDENTITY
        seller_identity = PIUP_SELLER_IDENTITY
        bch = buyer_chinese_header if buyer_chinese_header is not None else PIUP_BUYER_CHINESE_HEADER
        bin_ = buyer_identifier_no if buyer_identifier_no is not None else PIUP_BUYER_IDENTIFIER_NO
        sch = seller_chinese_header if seller_chinese_header is not None else PIUP_SELLER_CHINESE_HEADER
        sin_ = seller_identifier_no if seller_identifier_no is not None else PIUP_SELLER_IDENTIFIER_NO

        return [{
            "invoice_number": str(invoice_number),
            "invoice_type": PIUP_INVOICE_TYPE,
            "invoice_type_name": PIUP_INVOICE_TYPE_NAME,
            "invoice_amount": str(invoice_amount),
            "invoice_tax_amount": PIUP_INVOICE_TAX_AMOUNT,
            "invoice_date": invoice_date,
            "currency": "USD",
            "usd_amount": str(invoice_amount),
            "invoice_exchange_rate": PIUP_EXCHANGE_RATE,
            "invoice_original": invoice_original,
            "buyer_chinese_header": bch,
            "buyer_identifier_no": bin_,
            "buyer_identity": buyer_identity,
            "isbuyer_identity": buyer_identity,
            "seller_chinese_header": sch,
            "seller_identifier_no": sin_,
            "seller_identity": seller_identity,
            "isseller_identity": seller_identity,
            "invoice_image_name": str(file_name),
            "file_path": str(file_url),
        }]

    @classmethod
    def build_apply_page_payload(
        cls,
        bl_nos: List[str],
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Dict[str, Any]:
        """
        构建 applyPage 请求体（按 bl_nos 查询应付开票申请ID）

        与 receive 侧的 applyPage 共用接口模式，但查询条件不同。

        Args:
            bl_nos             : 提单号列表（**必填**）
            page_no           : 页码（默认 1）
            page_size         : 每页数量（默认 20）
            create_time_start : 创建时间开始（Unix 秒，默认 1 年前）
            create_time_end   : 创建时间结束（Unix 秒，默认 1 天后）

        Returns:
            请求体字典
        """
        import time as _time

        ap_cfg = _PIUP_APPLY_PAGE
        if page_no is None:
            page_no = ap_cfg.get("page_no", 1)
        if page_size is None:
            page_size = ap_cfg.get("page_size", 20)
        if create_time_start is None:
            create_time_start = str(
                int(_time.time()) - ap_cfg.get("create_time_year_offset", 365) * 86400
            )
        if create_time_end is None:
            create_time_end = str(
                int(_time.time()) + ap_cfg.get("create_time_day_offset", 1) * 86400
            )

        return {
            "page_no": page_no,
            "page_size": page_size,
            "order_no": "",
            "create_time": [
                int(create_time_start) * 1000,
                int(create_time_end) * 1000,
            ],
            "cancel_status": ap_cfg.get("cancel_status", []),
            "bl_nos": [str(b) for b in bl_nos],
            "customer_id": ap_cfg.get("customer_id", []),
            "main_id": ap_cfg.get("main_id", []),
            "pay_settle_object_id": ap_cfg.get("pay_settle_object_id", []),
            "currency": ap_cfg.get("currency", []),
            "invoice_status": ap_cfg.get("invoice_status", []),
            "writeoff_status": ap_cfg.get("writeoff_status", []),
            "create_id": ap_cfg.get("create_id", []),
            "sort_field": ap_cfg.get("sort_field", "create_time"),
            "sort_order": ap_cfg.get("sort_order", "desc"),
            "params": ap_cfg.get("params", {}),
            "create_time_start": create_time_start,
            "create_time_end": create_time_end,
        }

    @classmethod
    def build_allocation_payload(
        cls,
        pay_invoice_apply_id: str,
        pay_invoice_id: str,
        un_amount: str,
        action: str = "submit",
    ) -> Dict[str, Any]:
        """
        构建 allocationInvoiceFee 请求体（分配发票到费用）

        Args:
            pay_invoice_apply_id : 应付开票申请ID（来自 applyPage 响应，**必填**）
            pay_invoice_id       : 应付发票ID（来自 invoiceAdd 响应，**必填**）
            un_amount            : 未分配金额（来自 applyPage 响应，**必填**）
            action               : 操作类型（默认 submit）

        Returns:
            请求体字典
        """
        return {
            "pay_invoice_apply_id": str(pay_invoice_apply_id),
            "invoice_arr": [{
                "pay_invoice_id": str(pay_invoice_id),
                "invoice_amount_use": str(un_amount),
            }],
            "action": action,
        }


# ========================================================================
# 发起付款需求 - 配置与数据构建（LK23）
# ========================================================================
# 链路结构：
#   step1: financePayList       - 查询应付费用列表（获取 select_list）
#   step2: paymentList         - 付款需求预览（获取 payment_list 及汇总数据）
#   step3: demandEditByOrder  - 提交付款需求（action=submit）
# ========================================================================

_DEMAND_CFG = _load_yaml("pay_demand")
_DEMAND_CONST = _DEMAND_CFG.get("_constants", {}) if _DEMAND_CFG else {}


# 模块级常量（从 pay_demand.yaml 读取）
PAY_DEMAND_OPERATE_TYPE = _DEMAND_CONST.get("operate_type", 1)
PAY_DEMAND_BATCH_TYPE = _DEMAND_CONST.get("batch_type", 1)
PAY_DEMAND_PAGE_NO = _DEMAND_CONST.get("page_no", 1)
PAY_DEMAND_PAGE_SIZE = _DEMAND_CONST.get("page_size", 50)
PAY_DEMAND_YEAR_OFFSET_SECONDS = _DEMAND_CONST.get("page_year_offset", 365) * 86400

_DEMAND_CFG_INNER = _DEMAND_CFG.get("finance_pay_list", {}) if _DEMAND_CFG else {}
PAY_DEMAND_SEARCH_STYLE = _DEMAND_CFG_INNER.get("search_style", "payment")

_DEMAND_PAYMENT = _DEMAND_CFG.get("payment_demand", {}) if _DEMAND_CFG else {}
PAY_DEMAND_OPERATION_TYPE = _DEMAND_PAYMENT.get("operation_type", 1)
PAY_DEMAND_SPLIT_DIMENSION = _DEMAND_PAYMENT.get("split_dimension", [
    "customer_id", "main_id", "pay_settle_object_id", "currency"
])
PAY_DEMAND_AUDIT_MSG = _DEMAND_PAYMENT.get("audit_msg", {})
PAY_DEMAND_ACTION_SUBMIT = _DEMAND_PAYMENT.get("action_submit", "submit")


class PayDemandData:
    """
    发起付款需求（LK23）数据类

    涉及 3 个接口：
      1. financePayList        - 查询应付费用列表（付款需求模式）
      2. paymentList          - 付款需求预览
      3. demandEditByOrder    - 提交付款需求

    字段处理规则（已在 record 梳理中确认）：
      - operate_type / batch_type：data 层固定值
      - select_amount / cost_usd / cost_cny：从 amount_list 累加计算
      - split_dimension：data 层配置
      - _XID：索引拼接 (row_0, row_1...)
      - select_node_user：data 层配置（user_id 从 .env 读取）
      - fee_currency：从 select_list 获取币种
      - all_money_data / right_money_data：从 payment_list 汇总计算
      - audit_msg：data 层固定值
    """

    @classmethod
    def get_finance_pay_list_payload(
        cls,
        bl_no: str,
        main_id: str = None,
        pay_settle_object_id: str = None,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Dict[str, Any]:
        """
        构建 financePayList 查询请求体（付款需求模式）

        与 link19 对账模式共用接口，仅 search_style 不同（payment vs account）。

        Args:
            bl_no               : 提单号（精确查询，来自上游链路）
            main_id             : 主体ID（可选，缺省时从 YAML 读取）
            pay_settle_object_id: 付款结算对象ID（可选，缺省时从 YAML 读取）
            page_no            : 页码（默认 PAGE_NO_DEFAULT）
            page_size          : 每页数量（默认 PAGE_SIZE_STANDARD）
            create_time_start  : 创建时间开始（Unix 秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 秒，默认 1 年后）

        Returns:
            请求体字典
        """
        import time as _time

        if page_no is None:
            page_no = PAY_DEMAND_PAGE_NO
        if page_size is None:
            page_size = PAY_DEMAND_PAGE_SIZE
        if create_time_start is None:
            create_time_start = str(int(_time.time()) - PAY_DEMAND_YEAR_OFFSET_SECONDS)
        if create_time_end is None:
            create_time_end = str(int(_time.time()) + PAY_DEMAND_YEAR_OFFSET_SECONDS)

        return {
            "page_no": page_no,
            "page_size": page_size,
            "contain_fee_type": [],
            "bl_nos": [str(bl_no)],
            "main_id": [str(main_id)] if main_id else [],
            "pay_settle_object_id": [str(pay_settle_object_id)] if pay_settle_object_id else [],
            "operate_type": PAY_DEMAND_OPERATE_TYPE,
            "batch_type": PAY_DEMAND_BATCH_TYPE,
            "search_style": PAY_DEMAND_SEARCH_STYLE,
            "customer_id": "",
            "put_settle_object_id": "",
        }

    @classmethod
    def build_payment_list_payload(
        cls,
        pay_list_data: Dict[str, Any],
        select_amount: str,
        cost_usd: str,
        cost_cny: str,
        split_dimension: List[str] = None,
    ) -> Dict[str, Any]:
        """
        构建 paymentList 请求体（付款需求预览）

        该接口为中间预览步骤，返回 payment_list 及汇总数据供 Step 3 使用。

        Args:
            pay_list_data    : financePayList 响应中的 data 字典
            select_amount    : 选中金额（sum of real_amount）
            cost_usd        : 美元总额
            cost_cny        : 人民币总额
            split_dimension  : 拆分维度列表（默认从 YAML 读取）

        Returns:
            请求体字典
        """
        import time as _time

        if split_dimension is None:
            split_dimension = PAY_DEMAND_SPLIT_DIMENSION

        select_list = cls._build_select_list(pay_list_data)

        return {
            "operation_type": PAY_DEMAND_OPERATION_TYPE,
            "pay_demand_name": "",
            "customer_id": "",
            "put_settle_object_id": "",
            "main_id": None,
            "pay_settle_object_id": "",
            "select_list": select_list,
            "split_dimension": split_dimension,
            "demand_remark": "",
            "cost_usd": cost_usd,
            "cost_cny": cost_cny,
        }

    @classmethod
    def build_demand_edit_payload(
        cls,
        pay_list_data: Dict[str, Any],
        payment_list_data: Dict[str, Any],
        split_dimension: List[str] = None,
        select_node_user: List[Dict[str, Any]] = None,
        bl_nos: List[str] = None,
    ) -> Dict[str, Any]:
        """
        构建 demandEditByOrder 请求体（提交付款需求）

        Step 3 请求体包含 Step 2 响应的全部字段。

        Args:
            pay_list_data       : financePayList 响应中的 data 字典
            payment_list_data   : paymentList 响应中的 data 字典
            split_dimension     : 拆分维度列表（默认从 YAML 读取）
            select_node_user    : 审批节点用户（默认从 YAML + .env 读取）
            bl_nos             : 提单号列表（默认单元素列表）

        Returns:
            请求体字典
        """
        import time as _time

        if split_dimension is None:
            split_dimension = PAY_DEMAND_SPLIT_DIMENSION
        if bl_nos is None:
            bl_nos = []

        # Step 1: 构建 select_list（与 paymentList 一致）
        select_list = cls._build_select_list(pay_list_data)

        # Step 2: 从 paymentList 响应提取汇总数据
        payment_list = payment_list_data.get("payment_list", []) or []
        pay_amount_cny_total = payment_list_data.get("pay_amount_cny_total", "0.00")
        pay_amount_usd_total = payment_list_data.get("pay_amount_usd_total", "0.00")
        system_exchange_rate = payment_list_data.get("system_exchange_rate", "7.7000")
        exchange_amount_total = payment_list_data.get("exchange_amount_total", "0.00")
        pay_settle_object_total = payment_list_data.get("pay_settle_object_total", 1)

        # Step 3: 计算 select_amount / cost_usd / cost_cny
        select_amount, cost_usd, cost_cny = cls._calc_cost_totals(select_list)

        # Step 4: 构建 payment_list（含 _XID 索引）
        payment_list_with_xid = cls._build_payment_list_with_xid(payment_list)

        # Step 5: 构建 all_money_data / right_money_data
        all_money_data = cls._build_money_data(select_amount, cost_usd, cost_cny, exchange_amount_total)
        right_money_data = all_money_data.copy()

        # Step 6: 获取 fee_currency（从 select_list 第一条记录）
        fee_currency = cls._get_fee_currency(select_list)

        # Step 7: select_node_user
        if select_node_user is None:
            select_node_user = cls._build_select_node_user()

        # Step 8: audit_msg
        audit_msg = PAY_DEMAND_AUDIT_MSG.copy()

        return {
            "operation_type": PAY_DEMAND_OPERATION_TYPE,
            "pay_demand_name": "",
            "customer_id": "",
            "put_settle_object_id": "",
            "main_id": [str(m.get("main_id", "")) for m in select_list if m.get("main_id")],
            "pay_settle_object_id": [str(p.get("pay_settle_object_id", "")) for p in select_list if p.get("pay_settle_object_id")],
            "select_list": select_list,
            "select_amount": select_amount,
            "split_dimension": split_dimension,
            "demand_remark": "",
            "cost_usd": cost_usd,
            "cost_cny": cost_cny,
            "pay_amount_cny_total": pay_amount_cny_total,
            "pay_amount_usd_total": pay_amount_usd_total,
            "system_exchange_rate": system_exchange_rate,
            "exchange_amount_total": exchange_amount_total,
            "pay_settle_object_total": pay_settle_object_total,
            "payment_list": payment_list_with_xid,
            "pay_form_count": f"审核通过后将生成{len(payment_list_with_xid)}个付款单，其中{len(payment_list_with_xid)}为预计拆分付款单数量（根据圈选费用、拆分维度计算）",
            "action": PAY_DEMAND_ACTION_SUBMIT,
            "select_node_user": select_node_user,
            "fee_currency": fee_currency,
            "all_money_data": all_money_data,
            "right_money_data": right_money_data,
            "bl_nos": bl_nos,
            "audit_msg": audit_msg,
        }

    @classmethod
    def _build_select_list(cls, pay_list_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 financePayList 响应构建 select_list

        直接透传所有字段，不做转换，确保与后端期望一致。
        """
        result = []
        records = pay_list_data.get("data", [])
        for record in records:
            amount_list = record.get("amount_list", [])
            result.append({
                "order_id": record.get("order_id"),
                "order_no": record.get("order_no"),
                "bl_no": record.get("bl_no"),
                "customer_id": record.get("customer_id"),
                "customer_name": record.get("customer_name"),
                "customer_main_id": record.get("customer_main_id"),
                "customer_main_name": record.get("customer_main_name"),
                "business_main_id": record.get("business_main_id"),
                "business_main_name": record.get("business_main_name"),
                "policy_type": record.get("policy_type"),
                "trade_term": record.get("trade_term"),
                "customer_period": record.get("customer_period"),
                "customer_put_date": record.get("customer_put_date"),
                "atd": record.get("atd"),
                "etd": record.get("etd"),
                "create_time": record.get("create_time"),
                "finance_date": record.get("finance_date"),
                "ship_name": record.get("ship_name"),
                "voy": record.get("voy"),
                "fund_name": record.get("fund_name"),
                "status": record.get("status"),
                "is_special_pay": record.get("is_special_pay"),
                "pay_status": record.get("pay_status"),
                "is_loan_before_invoice": record.get("is_loan_before_invoice"),
                "customer_order_sn": record.get("customer_order_sn"),
                "order_sub_id": record.get("order_sub_id"),
                "order_sub_no": record.get("order_sub_no"),
                "main_id": record.get("main_id"),
                "main_name": record.get("main_name"),
                "currency": record.get("currency"),
                "amount_total": record.get("amount_total"),
                "service_project": record.get("service_project"),
                "pay_settle_object_type": record.get("pay_settle_object_type"),
                "real_settle_object_id": record.get("real_settle_object_id"),
                "real_settle_object": record.get("real_settle_object"),
                "put_settle_object": record.get("put_settle_object"),
                "put_settle_object_id": record.get("put_settle_object_id"),
                "pay_settle_object": record.get("pay_settle_object"),
                "pay_settle_object_id": record.get("pay_settle_object_id"),
                "book_supplier_period": record.get("book_supplier_period"),
                "book_supplier_pay_date": record.get("book_supplier_pay_date"),
                "book_supplier_name": record.get("book_supplier_name"),
                "operable_amount": record.get("operable_amount"),
                "un_operable_amount": record.get("un_operable_amount"),
                "operable_flag": record.get("operable_flag"),
                "order_sub_currency": record.get("order_sub_currency"),
                "order_main_finance": record.get("order_main_finance"),
                "order_error_messages": record.get("order_error_messages", []),
                "order_error_message": record.get("order_error_message", ""),
                "order_error_flag": record.get("order_error_flag", False),
                "amount_list": amount_list,
                "select_amount": cls._calc_select_amount(amount_list),
            })
        return result

    @classmethod
    def _calc_select_amount(cls, amount_list: List[Dict[str, Any]]) -> str:
        """从 amount_list 计算 select_amount（选中金额）"""
        total = 0.0
        for item in amount_list:
            try:
                total += float(item.get("real_amount", 0) or 0)
            except (TypeError, ValueError):
                pass
        return f"{total:.2f}"

    @classmethod
    def _calc_cost_totals(
        cls,
        select_list: List[Dict[str, Any]],
    ) -> tuple:
        """
        从 select_list 计算 cost_usd / cost_cny

        Returns:
            (select_amount, cost_usd, cost_cny)
        """
        cost_usd = 0.0
        cost_cny = 0.0

        for record in select_list:
            currency = record.get("currency", "USD")
            amount_str = record.get("select_amount") or record.get("amount_total", "0.00")
            try:
                amount = float(amount_str)
            except (TypeError, ValueError):
                amount = 0.0

            if currency == "USD":
                cost_usd += amount
            else:
                cost_cny += amount

        return (
            f"{cost_usd + cost_cny:.2f}",
            f"{cost_usd:.2f}",
            f"{cost_cny:.2f}",
        )

    @classmethod
    def _build_payment_list_with_xid(
        cls,
        payment_list: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        为 payment_list 添加 _XID 字段

        _XID = "row_{索引}" 格式
        """
        result = []
        for idx, item in enumerate(payment_list):
            new_item = item.copy()
            new_item["_XID"] = f"row_{idx}"
            result.append(new_item)
        return result

    @classmethod
    def _build_money_data(
        cls,
        select_amount: str,
        cost_usd: str,
        cost_cny: str,
        exchange_amount_total: str,
    ) -> Dict[str, Any]:
        """
        构建 all_money_data / right_money_data

        金额汇总计算逻辑：
          totalAmount = cost_usd * 汇率 + cost_cny
        """
        try:
            cost_usd_float = float(cost_usd or 0)
            cost_cny_float = float(cost_cny or 0)
            exchange_rate = float(exchange_amount_total) / cost_usd_float if cost_usd_float else 7.7
        except (TypeError, ValueError, ZeroDivisionError):
            exchange_rate = 7.7

        if cost_cny_float == 0:
            total_text = f"USD {cost_usd} + CNY 0.00"
        elif cost_usd_float == 0:
            total_text = f"USD 0.00 + CNY {cost_cny}"
        else:
            total_text = f"USD {cost_usd} + CNY {cost_cny}"

        operable_text = total_text

        try:
            total_amount = round(cost_usd_float * exchange_rate + cost_cny_float, 2)
        except (TypeError, ValueError):
            total_amount = 0.0

        return {
            "totalAmount": f"{total_amount:.2f}",
            "total_text": total_text,
            "operable_text": operable_text,
        }

    @classmethod
    def _get_fee_currency(cls, select_list: List[Dict[str, Any]]) -> str:
        """从 select_list 第一条记录获取 fee_currency"""
        if select_list:
            first_record = select_list[0]
            currency = first_record.get("currency", "USD")
            if currency:
                return currency
        return "USD"

    @classmethod
    def _build_select_node_user(cls) -> List[Dict[str, Any]]:
        """
        构建 select_node_user

        user_id 从 .env 的 ORDER_CREATE_ID 读取。
        """
        from dotenv import load_dotenv
        import os

        load_dotenv()
        user_id = os.getenv("ORDER_CREATE_ID", "60")

        return [{
            "node_sort": 0,
            "user_id": str(user_id),
        }]


# ========================================================================
# 审核生成付款单 - 配置与数据构建（LK24）
# ========================================================================
# 链路结构：
#   step1: auditPage       - 查询待审核列表
#   step2: auditExecute - 执行审批（通过）
# ========================================================================

def _load_yaml_audit(name: str) -> Dict[str, Any]:
    """加载审核配置 YAML"""
    path = Path(__file__).parent / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_AUDIT_CFG = _load_yaml_audit("pay_demand_audit")
_AUDIT_CONST = _AUDIT_CFG.get("_constants", {}) if _AUDIT_CFG else {}
_AUDIT_PAGE_CFG = _AUDIT_CFG.get("audit_page", {}) if _AUDIT_CFG else {}
_AUDIT_EXEC_CFG = _AUDIT_CFG.get("audit_execute", {}) if _AUDIT_CFG else {}


class PayDemandAuditData:
    """
    审核生成付款单（LK24）数据类

    涉及 2 个接口：
      1. auditPage      - 查询待审核列表
      2. auditExecute - 执行审批（通过）
    """

    @classmethod
    def get_audit_page_payload(
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
    ) -> Dict[str, Any]:
        """
        构建 auditPage 查询请求体

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
            请求体字典
        """
        if page_no is None:
            page_no = _AUDIT_CONST.get("page_no", 1)
        if page_size is None:
            page_size = _AUDIT_CONST.get("page_size", 20)
        if active_tab is None:
            active_tab = _AUDIT_PAGE_CFG.get("active_tab", "examine_wait")
        if audit_type is None:
            audit_type = _AUDIT_PAGE_CFG.get("audit_type", ["payDemand"])
        if sort_field is None:
            sort_field = _AUDIT_PAGE_CFG.get("sort_field", "expedite_num")
        if sort_order is None:
            sort_order = _AUDIT_PAGE_CFG.get("sort_order", "desc")
        if audit_status is None:
            audit_status = []
        if expedite_status is None:
            expedite_status = []
        if create_id is None:
            create_id = []
        if main_id is None:
            main_id = []

        return {
            "page_no": page_no,
            "page_size": page_size,
            "audit_status": audit_status,
            "expedite_status": expedite_status,
            "create_id": create_id,
            "main_id": main_id,
            "active_tab": active_tab,
            "audit_type": audit_type,
            "sort_field": sort_field,
            "sort_order": sort_order,
            "params": {},
        }

    @classmethod
    def get_audit_execute_payload(
        cls,
        audit_ids: List[str],
        audit_status: int = None,
        audit_remark: Any = None,
        transfer_user_id: Any = None,
    ) -> Dict[str, Any]:
        """
        构建 auditExecute 执行审批请求体

        Args:
            audit_ids      : 审批ID列表（**必填**）
            audit_status  : 审批状态（默认 2=通过）
            audit_remark  : 审批备注（默认 None）
            transfer_user_id: 转交用户ID（默认 None）

        Returns:
            请求体字典
        """
        if audit_status is None:
            audit_status = _AUDIT_EXEC_CFG.get("audit_status", 2)

        return {
            "audit_ids": [str(aid) for aid in audit_ids],
            "audit_status": audit_status,
            "audit_remark": audit_remark,
            "transfer_user_id": transfer_user_id,
        }


