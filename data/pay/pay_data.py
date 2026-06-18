"""
数据层 - 付款（Pay）域

包含：
  - payable.yaml 配置 loader
  - 应付对账批次模块级常量（OPERATE_TYPE / ACCOUNT_TYPE 等）
  - PayableAccountData  应付对账（link19）

API 层对应：api/pay/ 子包
"""
from pathlib import Path
from typing import Any, Dict, List

import yaml


# ========================================================================
# YAML 加载
# ========================================================================

def _load_yaml(name: str) -> Dict[str, Any]:
    path = Path(__file__).parent / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_CFG = _load_yaml("payable")
_CONST = _CFG.get("_constants", {}) if _CFG else {}


# ========================================================================
# 应付对账批次常量（统一从 payable.yaml 读取）
# ========================================================================

OPERATE_TYPE_BILL_OF_LADING = _CONST.get("operate_type", 1)
ACCOUNT_TYPE_CROSS_CUSTOMER = _CONST.get("account_type", "2")

PAGE_NO_DEFAULT = _CONST.get("page_no", 1)
PAGE_SIZE_STANDARD = _CONST.get("page_size", 50)
SORT_FIELD_CREATE_TIME = _CONST.get("sort_field", "create_time")
SORT_ORDER_DESC = _CONST.get("sort_order_desc", "desc")
YEAR_OFFSET_SECONDS = _CONST.get("page_year_offset", 365) * 86400

PAY_ACCOUNT_ACTION_SUBMIT = (
    _CFG.get("order_pay_account_edit", {}).get("action_submit", "submit")
)


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
