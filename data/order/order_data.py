"""
数据层 - 订单（Order）域

包含：
  - 5 个 order 域 yaml loader（与本文件同目录 data/order/）：
      order.yaml / audit.yaml / fee.yaml / fee_notice.yaml / fee_confirm.yaml
  - 订单基础数据类：BookRealAmountData / BaseOrderData / SubmitRequiredFields /
      AddOrderData / DistributeOrderData / SubmitOrderData / OrderTestData /
      OrderExpectations / AddOrderDataCompat / DistributeOrderDataCompat /
      SubmitOrderDataCompat / EntrustedOrderData / BusinessOrderData
  - 费用通知单 / 费用确认单数据类：FeeNoticeData / FeeConfirmData
  - 提单号生成：generate_bl_no()

应收域（ReceiveAccountData / ReceiveWriteoffData 等）已迁移至 data/receive/receive_data.py，
请使用 from data.receive import ... 引用。

API 层对应：api/order/ 子包（order_api.py / audit_api.py）
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid

import yaml


# ========================================================================
# YAML 加载（5 个 order 域 yaml 全部在本目录 data/order/ 下）
# ========================================================================

def _load_yaml(name: str) -> Dict[str, Any]:
    path = Path(__file__).parent / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_ORDER_CFG = _load_yaml("order")
_AUDIT_CFG = _load_yaml("audit")
_FEE_CFG   = _load_yaml("fee")
_NOTICE_CFG  = _load_yaml("fee_notice")
_CONFIRM_CFG = _load_yaml("fee_confirm")


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

def generate_bl_no(num) -> str:
    now = datetime.now()
    return f"lele_api_link{num}_{now.strftime('%Y%m%d%H%M%S')}"


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
