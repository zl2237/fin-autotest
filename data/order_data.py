"""
数据层 - 存放接口测试所需的请求数据和预期结果

使用方式：
- 新增订单: BaseOrderData + (可选)部分SubmitRequiredFields
- 分发订单: BaseOrderData + (可选)部分SubmitRequiredFields
- 提交订单: BaseOrderData + SubmitRequiredFields（完整合并）
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid

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


_ORDER_CFG = _load_yaml("order")
_FEE_CFG   = _load_yaml("fee")
_NOTICE_CFG  = _load_yaml("fee_notice")
_CONFIRM_CFG = _load_yaml("fee_confirm")
# ============================================================================
# 应收对账相关常量（统一从 receive_account.yaml 读取）
# ============================================================================
_RECEIVE_ACCOUNT_CFG = _load_yaml("receive_account")
_RA_CONST = _RECEIVE_ACCOUNT_CFG.get("_constants", {})

# ============================================================================
# 应收开票批次相关常量（统一从 receive_invoice.yaml 读取）
# ============================================================================
_RECEIVE_INVOICE_CFG = _load_yaml("receive_invoice")
_RI_CONST = _RECEIVE_INVOICE_CFG.get("_constants", {}) if _RECEIVE_INVOICE_CFG else {}

# ============================================================================
# 应收发票上传与登记相关常量（统一从 receive_invoice_upload.yaml 读取）
# ============================================================================
_RECEIVE_INVOICE_UPLOAD_CFG = _load_yaml("receive_invoice_upload")

# ============================================================================
# 应收核销相关常量（统一从 receive_writeoff.yaml 读取）
# ============================================================================
_RECEIVE_WRITEOFF_CFG = _load_yaml("receive_writeoff")
_RW_CONST = _RECEIVE_WRITEOFF_CFG.get("_constants", {}) if _RECEIVE_WRITEOFF_CFG else {}

# -- operate_type / account_type / confirm_type --
OPERATE_TYPE_RECEIVABLE = _RA_CONST.get("operate_type", 1)
ACCOUNT_TYPE_CROSS_CUSTOMER = _RA_CONST.get("account_type", "2")
CONFIRM_TYPE_PENDING = _RA_CONST.get("confirm_type", 0)

# -- action 常量 --
ACTION_CHECK = _RA_CONST.get("action_check", "check")
ACTION_SUBMIT = _RA_CONST.get("action_submit", "submit")

# -- 分页 --
PAGE_NO_DEFAULT = _RA_CONST.get("page_no", 1)
PAGE_SIZE_STANDARD = _RA_CONST.get("page_size", 50)
PAGE_SIZE_LARGE = _RA_CONST.get("page_size_large", 20)

# -- 时间偏移（秒）--
YEAR_OFFSET_SECONDS = _RA_CONST.get("page_year_offset", 365) * 86400
DAY_OFFSET_SECONDS = _RA_CONST.get("page_day_offset", 1) * 86400
TIMESTAMP_MS_FACTOR = _RA_CONST.get("timestamp_ms_factor", 1000)

# -- 排序 --
SORT_FIELD_CREATE_TIME = _RA_CONST.get("sort_field", "create_time")
SORT_ORDER_DESC = _RA_CONST.get("sort_order_desc", "desc")

# -- 主体名称（从 receive_account.yaml 读取）--
CUSTOMER_MAIN_NAME = _RA_CONST.get("customer_main_name", "青岛易航道物流科技有限公司")
RECEIVE_ACCOUNT_MAIN_NAME = _RA_CONST.get("main_name", "青岛易航道物流科技有限公司")

# -- 应收开票批次常量（从 receive_invoice.yaml 读取）--
INVOICE_BATCH_TYPE = _RI_CONST.get("batch_type", 1)
INVOICE_SEARCH_STYLE = _RI_CONST.get("search_style_invoice", "invoice")
INVOICE_ACTION_CHECK = _RI_CONST.get("action_check", "check")
INVOICE_ACTION_AUDIT = _RI_CONST.get("action_audit", "audit")
INVOICE_ACTION_SUBMIT = _RI_CONST.get("action_submit", "submit")
INVOICE_STYLE_FORMAL = _RI_CONST.get("style_formal", "1")
INVOICE_APPLY_TYPE_CROSS = _RI_CONST.get("apply_type_cross_customer", "2")
INVOICE_USD_TURN_ON = _RI_CONST.get("usd_turn_enabled", "1")
INVOICE_USD_TURN_OFF = _RI_CONST.get("usd_turn_disabled", "")
INVOICE_MERGE_CNY_NO = _RI_CONST.get("merge_with_cny_no", "2")
INVOICE_RATE_TYPE_SPECIFY = _RI_CONST.get("rate_type_specify", "1")
INVOICE_DEFAULT_RATE = _RI_CONST.get("default_exchange_rate", 7)
INVOICE_DEFAULT_FORM = _RI_CONST.get("default_invoice_form", "1")
INVOICE_DEFAULT_TYPE = _RI_CONST.get("default_invoice_type", "1")
INVOICE_DEFAULT_ITEM = _RI_CONST.get("default_invoice_item", "2")


# -- 应收核销常量（从 receive_writeoff.yaml 读取）--
RECEIVE_WRITEOFF_ACTION_SUBMIT = _RW_CONST.get("action_submit", "submit")
RECEIVE_WRITEOFF_AUDIT_NOTE = _RW_CONST.get("audit_note_default", "")
RECEIVE_WRITEOFF_NAME = _RW_CONST.get("writeoff_name_default", "Test Receivable Write-off")
RECEIVE_WRITEOFF_FEE_MATCH_TYPE = _RW_CONST.get("fee_match_type", "1")
RECEIVE_WRITEOFF_TYPE = _RW_CONST.get("writeoff_type", "1")
RECEIVE_WRITEOFF_MODE = _RW_CONST.get("writeoff_mode", "fee")
RECEIVE_WRITEOFF_SELECT_NODE_USER = _RW_CONST.get("select_node_user", [])
RECEIVE_WRITEOFF_PAGE_NO = _RW_CONST.get("page_no", 1)
RECEIVE_WRITEOFF_PAGE_SIZE = _RW_CONST.get("page_size", 20)
RECEIVE_WRITEOFF_SORT_FIELD = _RW_CONST.get("sort_field", "fee_create_time")
RECEIVE_WRITEOFF_SORT_ORDER = _RW_CONST.get("sort_order_desc", "desc")
RECEIVE_WRITEOFF_IS_PENETRATE = _RW_CONST.get("is_penetrate", "0")
RECEIVE_WRITEOFF_YEAR_OFFSET_SECONDS = _RW_CONST.get("page_year_offset", 365) * 86400
RECEIVE_WRITEOFF_DAY_OFFSET_SECONDS = _RW_CONST.get("page_day_offset", 1) * 86400
RECEIVE_WRITEOFF_MAIN_BANK_ID = _RW_CONST.get("statement", {}).get("main_bank_id", "11")
RECEIVE_WRITEOFF_STATEMENT_CURRENCY = _RW_CONST.get("statement", {}).get("statement_currency", "USD")
RECEIVE_WRITEOFF_STATEMENT_EXCHANGE_RATE = _RW_CONST.get("statement", {}).get("exchange_rate", 1)
RECEIVE_WRITEOFF_STATEMENT_ISCHANGE_RATE = _RW_CONST.get("statement", {}).get("ischangeRate", False)
RECEIVE_WRITEOFF_STATEMENT_RECEIPT_VOUCHER = _RW_CONST.get("statement", {}).get("receipt_voucher", "")
RECEIVE_WRITEOFF_STATEMENT_WRITEOFF_AMOUNT_CNY = _RW_CONST.get("statement", {}).get("writeoff_amount_cny", "0.00")
RECEIVE_WRITEOFF_STATEMENT_WRITEOFF_AMOUNT_USD = _RW_CONST.get("statement", {}).get("writeoff_amount_usd", "0.00")
RECEIVE_WRITEOFF_MAIN_NAME = _RW_CONST.get("main_name", "青岛易航道物流科技有限公司")
RECEIVE_WRITEOFF_MAIN_ID = _RW_CONST.get("main_id", "1")


# ========================================================================
# 订舱费用 - 录费用接口 bookRealAmountEdit
# 费用行直接从 fee.yaml 读取，拼入请求体结构
# ========================================================================

class BookRealAmountData:

    @classmethod
    def get_customer_standard_fees(cls) -> List[Dict[str, Any]]:
        """客户应收标准费用（3条），从 fee.yaml 读取"""
        return _FEE_CFG.get("customer", [])

    @classmethod
    def get_supplier_standard_fees(cls) -> List[Dict[str, Any]]:
        """供应商应付标准费用（3条），从 fee.yaml 读取"""
        return _FEE_CFG.get("supplier", [])

    @classmethod
    def get_customer_settle_object_id(cls) -> str:
        """从 fee.yaml 客户费用配置中提取托单结算对象ID（settle_object_id）"""
        fees = cls.get_customer_standard_fees()
        if fees:
            return str(fees[0].get("settle_object_id", ""))
        return ""

    @classmethod
    def build_fee_row(
        cls,
        config: Dict[str, Any],
        side: str,
        row_index: int,
        unique_id: str,
    ) -> Dict[str, Any]:
        """将 YAML 配置转为一行列，与真实请求体完全对齐"""
        is_supplier = side == "supplier"
        row = {
            "order_fee_real_id": None,
            "fee_type": int(config.get("fee_type", 0)),
            "policy_sub_id": None,
            "service_project": "booking_space",
            "cost_id": str(config["cost_id"]),
            "settle_object_id": str(config["settle_object_id"]),
            "subsidy_category": str(config.get("subsidy_category", "0")),
            "currency": str(config["currency"]),
            "unit_price": str(config["unit_price"]),
            "unit": str(config.get("unit", "")),
            "specs": str(config.get("specs", "")),
            "num": str(config["num"]),
            "remark": None,
            "discount_ratio": int(config["discount_ratio"]),
            "discount_amount": str(config["discount_amount"]),
            "discount_status": _FEE_CFG["row_discount_status"],
            "policy_sub_status_name": _FEE_CFG["row_policy_sub_status_name"],
            "pay_sync_status": _FEE_CFG["row_pay_sync_status"],
            "unique_id": unique_id,
            "init_main_name": (
                _FEE_CFG["row_supplier_init_main_name"] if is_supplier else _FEE_CFG["row_customer_init_main_name"]
            ),
            "main_name": None if is_supplier else _FEE_CFG["row_customer_init_main_name"],
            "rowIndex": row_index,
        }
        return row

    @classmethod
    def get_payload(
        cls,
        order_id: str,
        to_customer_fees: List[Dict[str, Any]] = None,
        to_supplier_fees: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if to_customer_fees is None:
            to_customer_fees = []
        if to_supplier_fees is None:
            to_supplier_fees = []

        pair_count = min(len(to_customer_fees), len(to_supplier_fees))
        customer_rows = []
        supplier_rows = []

        for i in range(pair_count):
            pair_uid = str(uuid.uuid4())
            customer_rows.append(cls.build_fee_row(to_customer_fees[i], "customer", i, pair_uid))
            supplier_rows.append(cls.build_fee_row(to_supplier_fees[i], "supplier", i, pair_uid))

        return {
            "action": _FEE_CFG["fee_action"],
            "order_id": str(order_id),
            "discount_ratio": _FEE_CFG["fee_discount_ratio"],
            "service_project": _FEE_CFG["fee_service_project"],
            "import_status": _FEE_CFG["fee_import_status"],
            "to_customer": {"put_amount": {"standard_list": customer_rows}},
            "to_supplier": {"pay_amount": {"standard_list": supplier_rows}},
        }


# ========================================================================
# 提单号
# ========================================================================

def generate_bl_no() -> str:
    now = datetime.now()
    return f"lele_apiauto_{now.strftime('%Y%m%d%H%M%S')}"


# ========================================================================
# 基础字段
# ========================================================================

class BaseOrderData:
    BASE_PARAMS: Dict[str, Any] = _ORDER_CFG["base_params"]
    SUPPLIER: List[Dict[str, Any]] = _ORDER_CFG["supplier_template"]

    @classmethod
    def get_base_payload(cls, bl_no: str = None) -> Dict[str, Any]:
        payload = cls.BASE_PARAMS.copy()
        payload["bl_no"] = bl_no if bl_no else generate_bl_no()
        payload["supplier"] = cls.SUPPLIER.copy()
        return payload

    @classmethod
    def get_base_payload_with_overrides(cls, bl_no: str = None, **overrides) -> Dict[str, Any]:
        payload = cls.get_base_payload(bl_no)
        payload.update(overrides)
        return payload


# ========================================================================
# 提交必填字段
# ========================================================================

class SubmitRequiredFields:
    SUBMIT_REQUIRED_DEFAULTS: Dict[str, Any] = _ORDER_CFG["submit_fields"]
    SUBMIT_SUPPLIER_TEMPLATE: List[Dict[str, Any]] = _ORDER_CFG["supplier_template"]
    DEFAULT_CONTAINER: List[Dict[str, Any]] = _ORDER_CFG["container_template"]

    @classmethod
    def get_submit_fields(cls) -> Dict[str, Any]:
        return cls.SUBMIT_REQUIRED_DEFAULTS.copy()

    @classmethod
    def get_submit_fields_with_overrides(cls, **overrides) -> Dict[str, Any]:
        fields = cls.get_submit_fields()
        fields.update(overrides)
        return fields

    @classmethod
    def get_partial_submit_fields(cls, *field_names: str) -> Dict[str, Any]:
        return {k: v for k, v in cls.get_submit_fields().items() if k in field_names}


# ========================================================================
# 新增订单
# ========================================================================

class AddOrderData:
    @classmethod
    def get_add_payload(cls, bl_no: str = None) -> Dict[str, Any]:
        return BaseOrderData.get_base_payload(bl_no)

    @classmethod
    def get_add_payload_with_submit_fields(cls, bl_no: str = None, **submit_fields) -> Dict[str, Any]:
        payload = BaseOrderData.get_base_payload(bl_no)
        payload.update(submit_fields)
        return payload

    @classmethod
    def get_add_payload_with_supplier(cls, supplier: List[Dict] = None, bl_no: str = None) -> Dict[str, Any]:
        payload = cls.get_add_payload(bl_no)
        if supplier is not None:
            payload["supplier"] = supplier
        return payload


# ========================================================================
# 分发订单
# ========================================================================

class DistributeOrderData:
    @classmethod
    def get_distribute_payload(cls, order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
        payload = BaseOrderData.get_base_payload(bl_no)
        payload["entrust_status"] = 2
        if order_info.get("order_id"):
            payload["order_id"] = order_info["order_id"]
        if order_info.get("order_no"):
            payload["order_no"] = order_info["order_no"]
        return payload

    @classmethod
    def get_distribute_payload_with_submit_fields(
        cls, order_info: Dict[str, Any], bl_no: str = None, **submit_fields
    ) -> Dict[str, Any]:
        payload = cls.get_distribute_payload(order_info, bl_no)
        payload.update(submit_fields)
        return payload


# ========================================================================
# 提交订单
# ========================================================================

class SubmitOrderData:
    @classmethod
    def get_submit_payload(cls, order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
        payload = BaseOrderData.get_base_payload(bl_no)
        payload.update(SubmitRequiredFields.get_submit_fields())
        cls._update_payload_common(payload, order_info, bl_no)
        return payload

    @classmethod
    def get_submit_payload_with_overrides(
        cls, order_info: Dict[str, Any], bl_no: str = None, **submit_overrides
    ) -> Dict[str, Any]:
        payload = BaseOrderData.get_base_payload(bl_no)
        fields = SubmitRequiredFields.get_submit_fields()
        fields.update(submit_overrides)
        payload.update(fields)
        cls._update_payload_common(payload, order_info, bl_no)
        return payload

    @classmethod
    def get_submit_payload_from_add_data(
        cls, add_payload: Dict[str, Any], order_info: Dict[str, Any] = None, bl_no: str = None
    ) -> Dict[str, Any]:
        payload = add_payload.copy() if add_payload else BaseOrderData.get_base_payload(bl_no)
        payload.update(SubmitRequiredFields.get_submit_fields())
        if order_info:
            cls._update_payload_common(payload, order_info, bl_no)
        return payload

    @classmethod
    def _update_payload_common(cls, payload: Dict[str, Any], order_info: Dict[str, Any], bl_no: str = None):
        if bl_no:
            payload["bl_no"] = bl_no
        elif order_info.get("bl_no"):
            payload["bl_no"] = order_info["bl_no"]
        else:
            payload["bl_no"] = generate_bl_no()

        if order_info.get("order_id"):
            payload["order_id"] = order_info["order_id"]
        if order_info.get("order_no"):
            payload["order_no"] = order_info["order_no"]

        for field in [
            "customer_category", "customer_tax_number", "customer_address_cn",
            "customer_contact_phone", "customer_main_id", "customer_main_name",
            "business_main_id", "business_main_name"
        ]:
            if order_info.get(field):
                payload[field] = order_info[field]

        supplier = SubmitRequiredFields.SUBMIT_SUPPLIER_TEMPLATE.copy()
        if order_info.get("supplier") and order_info["supplier"]:
            orig = order_info["supplier"][0]
            supplier[0]["order_supplier_id"] = orig.get("order_supplier_id", "")
            supplier[0]["order_id"] = orig.get("order_id", "")
            supplier[0]["sys_upttime"] = orig.get("sys_upttime", "")

        payload["supplier"] = supplier
        payload["action"] = "submit"
        payload["status"] = 2
        payload["entrust_status"] = 2

        if not payload.get("container"):
            payload["container"] = SubmitRequiredFields.DEFAULT_CONTAINER


# ========================================================================
# 测试数据 & 预期结果
# ========================================================================

class OrderTestData:
    @staticmethod
    def get_entrenched_order_normal() -> Dict[str, Any]:
        return {
            "page_no": 1, "page_size": 20, "order_no": "",
            "customer_id": [], "sort_field": "update_time", "sort_order": "desc", "params": {}
        }

    @staticmethod
    def get_entrenched_order_by_order_no(order_no: str) -> Dict[str, Any]:
        return {
            "page_no": 1, "page_size": 20, "order_no": order_no,
            "customer_id": [], "sort_field": "update_time", "sort_order": "desc", "params": {}
        }

    @staticmethod
    def get_business_order_normal() -> Dict[str, Any]:
        return {
            "page_no": 1, "page_size": 20, "order_no": "",
            "customer_id": [], "sort_field": "update_time", "sort_order": "desc", "params": {}
        }

    @staticmethod
    def get_pagination_test_cases() -> List[Dict[str, Any]]:
        return _ORDER_CFG.get("pagination", [])

    @staticmethod
    def get_sort_test_cases() -> List[Dict[str, str]]:
        return _ORDER_CFG.get("sort", [])


class OrderExpectations:
    SUCCESS_CODE = 200
    SUCCESS_MSG = "成功"
    MIN_PAGE_NO = 1
    MAX_PAGE_SIZE = 100
    DEFAULT_PAGE_SIZE = 20
    SORT_FIELDS = ["update_time", "create_time", "order_no", "amount"]
    SORT_ORDERS = ["asc", "desc"]
    REQUIRED_RESPONSE_FIELDS = ["code", "msg", "data"]
    REQUIRED_DATA_FIELDS = ["total", "data"]
    REQUIRED_ORDER_FIELDS = []


# ========================================================================
# 兼容性别名 & dataclass
# ========================================================================

class AddOrderDataCompat(AddOrderData):
    pass


class DistributeOrderDataCompat(DistributeOrderData):
    pass


class SubmitOrderDataCompat(SubmitOrderData):
    pass


@dataclass
class EntrustedOrderData:
    page_no: int = 1
    page_size: int = 20
    order_no: str = ""
    customer_id: List[str] = None
    sort_field: str = "update_time"
    sort_order: str = "desc"
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.customer_id is None:
            self.customer_id = []
        if self.params is None:
            self.params = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_no": self.page_no,
            "page_size": self.page_size,
            "order_no": self.order_no,
            "customer_id": self.customer_id,
            "sort_field": self.sort_field,
            "sort_order": self.sort_field,
            "params": self.params
        }


@dataclass
class BusinessOrderData:
    page_no: int = 1
    page_size: int = 20
    order_no: str = ""
    customer_id: List[str] = None
    sort_field: str = "update_time"
    sort_order: str = "desc"
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.customer_id is None:
            self.customer_id = []
        if self.params is None:
            self.params = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_no": self.page_no,
            "page_size": self.page_size,
            "order_no": self.order_no,
            "customer_id": self.customer_id,
            "sort_field": self.sort_field,
            "sort_order": self.sort_order,
            "params": self.params
        }


# ========================================================================
# 费用通知单 - 生成费用通知单接口 orderNotice
# ========================================================================

class FeeNoticeData:

    @classmethod
    def get_generate_payload(
        cls,
        order_id: str,
        finance_ids: List[str] = None,
        bank_ids: List[str] = None,
        action: str = "submit",
    ) -> Dict[str, Any]:
        """
        构建生成费用通知单的请求体

        Args:
            order_id    : 业务订单ID（从链路流程获取）
            finance_ids : 费用ID列表（默认取 yaml 配置）
            bank_ids    : 账户ID列表（默认取 yaml 配置）
            action      : 操作类型

        Returns:
            请求体字典
        """
        return {
            "action": action,
            "order_id": str(order_id),
            "finance_ids": finance_ids if finance_ids is not None else _NOTICE_CFG["finance_ids"],
            "bank_ids": bank_ids if bank_ids is not None else _NOTICE_CFG["bank_ids"],
        }

    @classmethod
    def get_default_finance_ids(cls) -> List[str]:
        """默认费用ID列表"""
        return _NOTICE_CFG["finance_ids"].copy()

    @classmethod
    def get_default_bank_ids(cls) -> List[str]:
        """默认账户ID列表"""
        return _NOTICE_CFG["bank_ids"].copy()


# ========================================================================
# 费用确认单 - 生成费用确认单接口 orderConfirmLoan
# ========================================================================

class FeeConfirmData:

    @classmethod
    def get_generate_payload(
        cls,
        order_id: str,
        finance_ids: List[str] = None,
        bank_ids: List[str] = None,
        action: str = "submit",
    ) -> Dict[str, Any]:
        """
        构建生成费用确认单的请求体

        Args:
            order_id    : 业务订单ID（从链路流程获取）
            finance_ids : 费用ID列表（默认取 _CONFIRM_CFG 配置）
            bank_ids    : 账户ID列表（默认取 _CONFIRM_CFG 配置）
            action      : 操作类型

        Returns:
            请求体字典
        """
        return {
            "action": action,
            "order_id": str(order_id),
            "finance_ids": finance_ids if finance_ids is not None else _CONFIRM_CFG["finance_ids"],
            "bank_ids": bank_ids if bank_ids is not None else _CONFIRM_CFG["bank_ids"],
        }

    @classmethod
    def get_default_finance_ids(cls) -> List[str]:
        """默认费用ID列表"""
        return _CONFIRM_CFG["finance_ids"].copy()

    @classmethod
    def get_default_bank_ids(cls) -> List[str]:
        """默认账户ID列表"""
        return _CONFIRM_CFG["bank_ids"].copy()


# ========================================================================
# 应收对账批次 - 发起应收对账批次接口
# ========================================================================

class ReceiveAccountData:

    @classmethod
    def get_finance_put_list_payload(
        cls,
        bl_no: str,
        put_settle_object_id: str,
        main_id: str = None,
        page_no: int = None,
        page_size: int = None,
    ) -> Dict[str, Any]:
        """
        构建 financePutList 查询请求体

        Args:
            bl_no                : 提单号
            put_settle_object_id : 托单结算对象ID
            main_id              : 主体ID（默认从 _constants.main_id 读取）
            page_no              : 页码（默认 PAGE_NO_DEFAULT）
            page_size            : 每页数量（默认 PAGE_SIZE_STANDARD）

        Returns:
            请求体字典
        """
        if main_id is None:
            cfg = _RECEIVE_ACCOUNT_CFG.get("finance_put_list", {})
            main_id = cfg.get("main_id", "1")
        if page_no is None:
            page_no = PAGE_NO_DEFAULT
        if page_size is None:
            page_size = PAGE_SIZE_STANDARD
        cfg = _RECEIVE_ACCOUNT_CFG.get("finance_put_list", {})
        return {
            "page_no": page_no,
            "page_size": page_size,
            "bl_no": bl_no,
            "operate_type": cfg.get("operate_type", OPERATE_TYPE_RECEIVABLE),
            "search_style": cfg.get("search_style", "account"),
            "account_simple_name": cfg.get("account_simple_name"),
            "account_type": cfg.get("account_type", ACCOUNT_TYPE_CROSS_CUSTOMER),
            "customer_id": cfg.get("customer_id"),
            "put_settle_object_id": str(put_settle_object_id),
            "main_id": str(main_id),
            "pay_settle_object_id": cfg.get("pay_settle_object_id"),
        }

    @classmethod
    def build_select_list_from_put_list(
        cls,
        put_list_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        从 financePutList 响应 data.data 中提取 amount_list，
        重组为 orderReceiveAccountEdit 所需的 select_list 结构。

        Args:
            put_list_data: financePutList 响应中的 data 字典

        Returns:
            select_list 列表（包含 order 和 amount_list）
        """
        result = []
        records = put_list_data.get("data", [])
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
                "fund_name": record.get("fund_name"),
                "ship_name": record.get("ship_name"),
                "voy": record.get("voy"),
                "status": record.get("status"),
                "is_special_pay": record.get("is_special_pay"),
                "pay_status": record.get("pay_status"),
                "is_loan_before_invoice": record.get("is_loan_before_invoice"),
                "customer_order_sn": record.get("customer_order_sn"),
                "order_sub_id": record.get("order_sub_id"),
                "order_sub_no": record.get("order_sub_no"),
                "main_id": record.get("main_id"),
                "main_name": record.get("main_name"),
                "service_project": record.get("service_project"),
                "currency": record.get("currency"),
                "amount_total": record.get("amount_total"),
                "pay_settle_object_type": record.get("pay_settle_object_type"),
                "put_settle_object_id": record.get("put_settle_object_id"),
                "put_settle_object": record.get("put_settle_object"),
                "pay_settle_object": record.get("pay_settle_object"),
                "book_supplier_period": record.get("book_supplier_period"),
                "book_supplier_pay_date": record.get("book_supplier_pay_date"),
                "book_supplier_name": record.get("book_supplier_name"),
                "operable_amount": record.get("operable_amount"),
                "un_operable_amount": record.get("un_operable_amount"),
                "operable_flag": record.get("operable_flag"),
                "policy_type_name": record.get("policy_type_name"),
                "order_sub_currency": record.get("order_sub_currency"),
                "order_main_finance": record.get("order_main_finance"),
                "order_error_messages": record.get("order_error_messages", []),
                "order_error_message": record.get("order_error_message", ""),
                "order_error_flag": record.get("order_error_flag", False),
                "amount_list": amount_list,
            })
        return result


# ========================================================================
# 应收核销 - 应收核销接口（LK18）
# ========================================================================
# 链路结构：
#   step1: feeTakePage    - 按提单号分页查询费用实付 ID 列表
#   step2: writeoffBatch  - 应收核销（依赖 step1 的 order_fee_real_id）
# ========================================================================

class ReceiveWriteoffData:

    @classmethod
    def get_fee_take_page_payload(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Dict[str, Any]:
        """
        构建 feeTakePage 查询请求体（按提单号查询 order_fee_real_id 列表）

        Args:
            bl_no              : 提单号（精确查询）
            page_no            : 页码（默认 RECEIVE_WRITEOFF_PAGE_NO）
            page_size          : 每页数量（默认 RECEIVE_WRITEOFF_PAGE_SIZE）
            create_time_start  : 创建时间开始（Unix 时间戳秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 时间戳秒，默认 1 年后）

        Returns:
            请求体字典
        """
        import time as _time

        if page_no is None:
            page_no = RECEIVE_WRITEOFF_PAGE_NO
        if page_size is None:
            page_size = RECEIVE_WRITEOFF_PAGE_SIZE
        if create_time_start is None:
            create_time_start = str(int(_time.time()) - RECEIVE_WRITEOFF_YEAR_OFFSET_SECONDS)
        if create_time_end is None:
            create_time_end = str(int(_time.time()) + RECEIVE_WRITEOFF_YEAR_OFFSET_SECONDS)

        cfg = _RECEIVE_WRITEOFF_CFG.get("fee_take_page", {}) if _RECEIVE_WRITEOFF_CFG else {}
        return {
            "page_no": page_no,
            "page_size": page_size,
            "create_time": [
                int(create_time_start) * 1000,
                int(create_time_end) * 1000,
            ],
            "customer_id": cfg.get("customer_id", []),
            "bl_nos": [],
            "bl_no": str(bl_no),
            "is_penetrate": cfg.get("is_penetrate", RECEIVE_WRITEOFF_IS_PENETRATE),
            "sort_field": cfg.get("sort_field", RECEIVE_WRITEOFF_SORT_FIELD),
            "sort_order": cfg.get("sort_order", RECEIVE_WRITEOFF_SORT_ORDER),
            "params": cfg.get("params", {}),
            "create_time_start": create_time_start,
            "create_time_end": create_time_end,
        }

    @classmethod
    def build_writeoff_object_from_fee_take_page(
        cls,
        fee_take_page_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        从 feeTakePage 响应 data.data 中提取 order_fee_real_id + un_writeoff_amount，
        重组为 writeoffBatch 所需的 writeoff_object 列表。

        Args:
            fee_take_page_data: feeTakePage 响应中的 data 字典

        Returns:
            writeoff_object 列表（每个元素含 order_fee_real_id 和 un_writeoff_amount）
        """
        result = []
        records = (fee_take_page_data or {}).get("data", []) or []
        for record in records:
            order_fee_real_id = str(record.get("order_fee_real_id", ""))
            if not order_fee_real_id:
                continue
            un_writeoff_amount = str(record.get("un_writeoff_amount", "0.00"))
            result.append({
                "order_fee_real_id": order_fee_real_id,
                "un_writeoff_amount": un_writeoff_amount,
            })
        return result

    @classmethod
    def get_writeoff_batch_payload(
        cls,
        writeoff_object: List[Dict[str, Any]],
        main_id: str = None,
        main_name: str = None,
        receipt_time: int = None,
        writeoff_name: str = None,
        audit_note: str = None,
        action: str = None,
        select_node_user: List[Dict[str, Any]] = None,
        statement_currency: str = None,
    ) -> Dict[str, Any]:
        """
        构建 writeoffBatch 应收核销请求体。

        该接口请求体金额字段较多（_usd_total / _cny_total / statement_*_total），
        本方法根据 writeoff_object 自动按币种求和填充，避免硬编码金额。

        Args:
            writeoff_object    : 核销对象列表（来自 build_writeoff_object_from_fee_take_page）
            main_id            : 主体ID（默认 RECEIVE_WRITEOFF_MAIN_ID）
            main_name          : 主体名称（默认 RECEIVE_WRITEOFF_MAIN_NAME）
            receipt_time       : 收款时间（Unix 时间戳秒，默认当前时间）
            writeoff_name      : 核销批次名称（默认 RECEIVE_WRITEOFF_NAME）
            audit_note         : 审批备注（默认空，走常规核销）
            action             : 操作类型（默认 submit）
            select_node_user   : 指定审批人列表（默认空数组）
            statement_currency : 账单币种（默认 USD）

        Returns:
            请求体字典
        """
        import time as _time

        if main_id is None:
            main_id = RECEIVE_WRITEOFF_MAIN_ID
        if main_name is None:
            main_name = RECEIVE_WRITEOFF_MAIN_NAME
        if receipt_time is None:
            receipt_time = int(_time.time())
        if writeoff_name is None:
            writeoff_name = RECEIVE_WRITEOFF_NAME
        if audit_note is None:
            audit_note = RECEIVE_WRITEOFF_AUDIT_NOTE
        if action is None:
            action = RECEIVE_WRITEOFF_ACTION_SUBMIT
        if select_node_user is None:
            select_node_user = list(RECEIVE_WRITEOFF_SELECT_NODE_USER)
        if statement_currency is None:
            statement_currency = RECEIVE_WRITEOFF_STATEMENT_CURRENCY

        # 按币种分别累计未核销金额 / 使用核销金额
        un_writeoff_usd_total = 0.0
        un_writeoff_cny_total = 0.0
        use_writeoff_usd_total = 0.0
        use_writeoff_cny_total = 0.0

        # 由于 writeoff_object 中没有 currency 字段，金额按 statement_currency 全部计入对应币种
        try:
            total = sum(float(item.get("un_writeoff_amount", 0)) for item in writeoff_object)
        except (TypeError, ValueError):
            total = 0.0

        if statement_currency == "USD":
            un_writeoff_usd_total = total
            use_writeoff_usd_total = total
        elif statement_currency == "CNY":
            un_writeoff_cny_total = total
            use_writeoff_cny_total = total
        else:
            # 其他币种默认按 USD 计入
            un_writeoff_usd_total = total
            use_writeoff_usd_total = total

        statement_amount = f"{total:.2f}" if total else "0.00"
        use_statement_amount = f"{total:.2f}" if total else "0.00"
        writeoff_amount_cny = RECEIVE_WRITEOFF_STATEMENT_WRITEOFF_AMOUNT_CNY
        writeoff_amount_usd = (
            f"{total:.2f}" if total else RECEIVE_WRITEOFF_STATEMENT_WRITEOFF_AMOUNT_USD
        )

        statement_item = {
            "statement_currency": statement_currency,
            "statement_amount": statement_amount,
            "writeoff_amount_cny": writeoff_amount_cny,
            "writeoff_amount_usd": writeoff_amount_usd,
            "exchange_rate": RECEIVE_WRITEOFF_STATEMENT_EXCHANGE_RATE,
            "ischangeRate": RECEIVE_WRITEOFF_STATEMENT_ISCHANGE_RATE,
            "main_bank_id": RECEIVE_WRITEOFF_MAIN_BANK_ID,
            "receipt_time": int(receipt_time),
            "receipt_voucher": RECEIVE_WRITEOFF_STATEMENT_RECEIPT_VOUCHER,
            "use_statement_amount_cny_total": (
                f"{use_writeoff_cny_total:.2f}" if use_writeoff_cny_total else "0.00"
            ),
            "use_statement_amount_usd_total": (
                f"{use_writeoff_usd_total:.2f}" if use_writeoff_usd_total else "0.00"
            ),
        }

        return {
            "action": action,
            "audit_note": audit_note,
            "writeoff_object": writeoff_object,
            "writeoff_name": writeoff_name,
            "fee_match_type": RECEIVE_WRITEOFF_FEE_MATCH_TYPE,
            "writeoff_type": RECEIVE_WRITEOFF_TYPE,
            "writeoff_mode": RECEIVE_WRITEOFF_MODE,
            "un_writeoff_amount_usd_total": f"{un_writeoff_usd_total:.2f}",
            "un_writeoff_amount_cny_total": f"{un_writeoff_cny_total:.2f}",
            "use_writeoff_amount_usd_total": f"{use_writeoff_usd_total:.2f}",
            "use_writeoff_amount_cny_total": f"{use_writeoff_cny_total:.2f}",
            "statement_amount_cny_total": f"{un_writeoff_cny_total:.2f}",
            "statement_amount_usd_total": f"{un_writeoff_usd_total:.2f}",
            "statement": [statement_item],
            "main_id": str(main_id),
            "main_name": main_name,
            "select_node_user": select_node_user,
        }
