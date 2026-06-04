"""
测试数据层 - 存放接口测试所需的请求数据和预期结果

字段分层设计：
- BASE_FIELDS: 基础字段（新增、分发、提交都使用）
- SUBMIT_REQUIRED_FIELDS: 提交时必填字段
  - 新增/分发时：默认置空，方便后续配置
  - 提交时：必须填写的业务字段

使用方式：
- 新增订单: BaseOrderData + (可选)部分SubmitRequiredFields
- 分发订单: BaseOrderData + (可选)部分SubmitRequiredFields
- 提交订单: BaseOrderData + SubmitRequiredFields（完整合并）
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


# ==========================
# 提单号生成工具
# ==========================
def generate_bl_no() -> str:
    """
    生成格式化的提单号: lele_apiauto_年月日+时间戳后6位
    例如: lele_apiauto_20260529192030
    """
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    return f"lele_apiauto_{date_part}{time_part}"


# ==========================
# 订单接口 - 委托订单列表
# ==========================
@dataclass
class EntrustedOrderData:
    """委托订单列表 - 请求参数"""
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


# ==========================
# 订单接口 - 业务订单列表
# ==========================
@dataclass
class BusinessOrderData:
    """业务订单列表 - 请求参数"""
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


# ==========================
# 预期结果数据
# ==========================
class OrderExpectations:
    """订单接口预期结果"""

    # 通用成功响应码
    SUCCESS_CODE = 200
    SUCCESS_MSG = "成功"

    # 分页参数边界
    MIN_PAGE_NO = 1
    MAX_PAGE_SIZE = 100
    DEFAULT_PAGE_SIZE = 20

    # 排序字段可选值
    SORT_FIELDS = ["update_time", "create_time", "order_no", "amount"]
    SORT_ORDERS = ["asc", "desc"]

    # 必需字段（响应数据中必须有这些字段）
    REQUIRED_RESPONSE_FIELDS = ["code", "msg", "data"]

    # data 节点必需字段
    REQUIRED_DATA_FIELDS = ["total", "data"]

    # data.data 列表中每条记录的必需字段
    REQUIRED_ORDER_FIELDS = []  # 根据实际业务填写，如 ["order_no", "status"]


# ==========================
# 测试用例数据
# ==========================
class OrderTestData:
    """订单接口测试用例数据"""

    @staticmethod
    def get_entrenched_order_normal() -> Dict[str, Any]:
        """正常查询委托订单"""
        return {
            "page_no": 1,
            "page_size": 20,
            "order_no": "",
            "customer_id": [],
            "sort_field": "update_time",
            "sort_order": "desc",
            "params": {}
        }

    @staticmethod
    def get_entrenched_order_by_order_no(order_no: str) -> Dict[str, Any]:
        """根据订单号查询委托订单"""
        return {
            "page_no": 1,
            "page_size": 20,
            "order_no": order_no,
            "customer_id": [],
            "sort_field": "update_time",
            "sort_order": "desc",
            "params": {}
        }

    @staticmethod
    def get_business_order_normal() -> Dict[str, Any]:
        """正常查询业务订单"""
        return {
            "page_no": 1,
            "page_size": 20,
            "order_no": "",
            "customer_id": [],
            "sort_field": "update_time",
            "sort_order": "desc",
            "params": {}
        }

    @staticmethod
    def get_pagination_test_cases() -> List[Dict[str, Any]]:
        """分页测试用例"""
        return [
            {"page_no": 1, "page_size": 10},
            {"page_no": 1, "page_size": 50},
            {"page_no": 2, "page_size": 20},
        ]

    @staticmethod
    def get_sort_test_cases() -> List[Dict[str, str]]:
        """排序测试用例"""
        return [
            {"sort_field": "update_time", "sort_order": "desc"},
            {"sort_field": "update_time", "sort_order": "asc"},
            {"sort_field": "create_time", "sort_order": "desc"},
        ]


# ==========================
# 核心数据类 - 基础字段（新增/分发/提交共用）
# ==========================
class BaseOrderData:
    """
    订单基础字段 - 新增、分发、提交都使用

    设计原则：
    - 所有订单操作都需要的公共字段
    - 提交时与 SubmitRequiredFields 合并使用
    """

    # 公共基础参数（所有订单操作都需要）
    BASE_PARAMS = {
        "client_expand_name": "荣洋",
        "client_expand_id": "16",
        "m_delivery_type": "",
        "customer_id": "60934",
        "customer_name": "",
        "service_id": "40",
        "service_name": "李明丹tidb",
        "operator_id": "293",
        "operator_name": "",
        "customer_contact_id": "",
        "customer_contact_name": "",
        "main_sort": "易航道-易汇联-青岛易汇航-上海一帜",
        "policy_id": "296905601001193472",
        "policy_name": "陆旭阳多主体服务策略-自动匹配",
        "policy_type": "JSZX",
        "service_items": ["booking_space"],
        "business_type": "1",
        "trade_term": "",
        "carrier": "",
        "carrier_id": "",
        "etd": "",
        "atd": "",
        "ship_name": "",
        "voy": "",
        "pol": "",
        "pot": "",
        "pod": "",
        "del": "",
        "country_name": "",
        "airline_type": "",
        "ocean_type": "",
        "terms_payment": "T/T",
        "terms_transport": "CY/CY",
        "pay_type": "",
        "customer_order_sn": "",
        "terms_shipment": "",
        "shipper": "",
        "consignee": "",
        "notifier": "",
        "ship_mark": "",
        "commodity": "",
        "notes": "",
        "cargo_type": "",
        "packer": "",
        "num": "",
        "gross_weight": None,
        "bulk": None,
        "sea_trans_cost": "",
        "teu": "",
        "volume": "",
        "volume_desc": "",
        "order_sn": "",
        "status": "1",
        "sea_trans_currency": "USD",
        "container": [],
        "message_board": [],
        "customer_file_list": [],
        "remark": "",
        "policy_type_name": "",
        "main_ids": "1,3,2,6",
        "action": "submit",
        "entrust_status": 1,
        "order_file": []
    }

    # 供应商信息模板
    SUPPLIER = [{
        "is_manual": "",
        "is_primary": "1",
        "isset_fee": "0",
        "isset_supplier": "1",
        "order_id": "",
        "order_supplier_id": "",
        "service_item": "booking_space",
        "service_item_name": "订舱",
        "settle_object_id": "",
        "settlement_date": None,
        "supplier_id": "61224",
        "supplier_name": "芜湖长信科技股份有限公司",
        "supplier_pay_date": None,
        "supplier_period": None,
        "user_id": "16",
        "user_name": "荣洋"
    }]

    @classmethod
    def get_base_payload(cls, bl_no: str = None) -> Dict[str, Any]:
        """
        获取基础载荷（不包含提交必填字段）

        Args:
            bl_no: 提单号，默认自动生成

        Returns:
            基础请求参数字典
        """
        if bl_no is None:
            bl_no = generate_bl_no()

        payload = cls.BASE_PARAMS.copy()
        payload["bl_no"] = bl_no
        payload["supplier"] = cls.SUPPLIER.copy()
        return payload

    @classmethod
    def get_base_payload_with_overrides(cls, bl_no: str = None, **overrides) -> Dict[str, Any]:
        """
        获取带自定义覆盖的基础载荷

        Args:
            bl_no: 提单号
            **overrides: 要覆盖的字段，如 trade_term="FOB", carrier="MSC"

        Returns:
            覆盖后的基础参数字典
        """
        payload = cls.get_base_payload(bl_no)
        payload.update(overrides)
        return payload


# ==========================
# 核心数据类 - 提交时必填字段
# ==========================
class SubmitRequiredFields:
    """
    提交时必填字段

    设计原则：
    - 新增/分发时：这些字段默认置空（由 BaseOrderData 提供）
    - 提交时：必须填写这些字段才能成功提交
    - 灵活性：支持部分字段预先配置，部分留空待提交时填写
    """

    # 提交时必须填写的字段（默认值）
    # 新增/分发时可选择预填，提交时必须完整
    SUBMIT_REQUIRED_DEFAULTS = {
        # 贸易和运输信息
        "trade_term": "CIF",
        "carrier": "ACL",
        "carrier_id": "1",
        "etd": 1777996800,
        "atd": None,
        "ship_name": "a",
        "voy": "a",
        "pol": "ANTING,CHINA",
        "pot": "",
        "pod": "AOSHANWEI,CHINA",
        "del": "AOSHANWEI,CHINA",
        "country_name": "CHINA",
        "airline_type": "中国",
        "ocean_type": "近洋",
        "pay_type": "FREIGHT PREPAID",

        # 货物信息
        "terms_shipment": "",
        "ship_mark": "",
        "commodity": "",
        "notes": "",
        "cargo_type": "",
        "packer": "",
        "bulk": None,
        "teu": "",
        "volume": "1*AIR",
        "volume_desc": "特种柜",
        "num": "1",
        "gross_weight": "1",
        "sea_trans_cost": "1.00",

        # 参与方信息
        "shipper": "测试发货人",
        "consignee": "测试收货人",
        "notifier": "测试通知人",

        # 文件和附件
        "customer_file_list": [
            {
                "client_company_id": "60934",
                "client_company_name": "北京火山引擎科技有限公司",
                "trustee_company_id": "1",
                "trustee_company_name": "青岛易航道物流科技有限公司",
                "document_type": "BOOK_CUSTOMER",
                "file_url": "https://fnzxnfs-tidb.21eflag.com/resource/file/getFile?file_name=6a198b9b7953b.pdf&voucher=6a18e7981acf2",
                "file_name": "6a198b9b7953b.pdf",
                "file_id": "116892",
                "file_type": "pdf"
            }
        ],

        # 服务项目配置
        "service_project": {
            "booking_space": False,
            "customs_clearance": False,
            "manifest": False,
            "insurance": False,
            "trucking": False
        },
        "service_project_amount": {
            "booking_space": False,
            "customs_clearance": False,
            "manifest": False,
            "insurance": False,
            "trucking": False
        },

        # 财务相关字段
        "order_finance_arr": [],
        "order_main_bank_arr": [],
        "order_sub": [],
        "customer_payment_collection_date": None,
        "customer_put_writeoff_date": "",
        "supplier_due_date": "0",
        "discount_ratio": "",
        "cancel_remark": "",
        "cancel_time": "0",
        "effective_id": "0",
        "effective_by": "",
        "effective_time": "0",
        "business_time": "0",
        "reverse_status": "0",
        "proprietary_business_status": "0",
        "loan_status": None,
        "first_status": None,
        "second_status": None,
        "loan_pay_status": "",
        "change_type": "0",
        "copy_order_id": "0",
        "real_fee_locked": False,
        "is_sync_es": "0",
        "expect_discount_status": "0",
        "real_discount_status": "0",
        "remark": "",
        "audit_type": "",
        "is_system_generate": "0",
        "is_financing": "0",
        "confirm_status": "0",
        "is_traverse": "0",
        "financing_apply_amount": "0.00",
        "financing_apply_amount_cny": "0.00",
        "financing_apply_amount_usd": "0.00",
        "fund_code": "",
        "fund_name": None,
        "track_atd": "0",
        "finance_date": "0",

        # 港口和国家信息
        "pol_cn": None,
        "pol_country_id": "1",
        "pol_country": "CHINA",
        "pol_country_cn": "中国",
        "pod_cn": None,
        "pot_cn": "",
        "del_cn": None,
        "country_id": "1",
        "country_name_cn": "中国",

        # 客户账期信息
        "customer_period": "60",
        "customer_settlement_date": "10",
        "period_rule": "0",
        "term_rule_name": None,
        "customer_due_date": "0",
        "customer_put_date": "0",
        "customer_put_date_manual": "0",
        "supplier_invoice_date": "0",
        "supplier_invoice_taketime": "",
        "real_cost_date": "0",
        "customer_invoice_request_date": "0",
        "first_financing_doc_ok_date": "0",
        "second_financing_doc_ok_date": "0",
        "insurance_doc_ok_date": "0",
        "customer_confirm_date": "0",
        "is_delayed_recovery": "否",
        "delayed_recovery_usd": "",
        "delayed_recovery_cny": "",
        "delayed_time": "",

        # 费用状态
        "expect_fee_status": "0",
        "real_fee_status": "0",
        "fee_lock_status": "0",
        "pay_account_status": "0",
        "account_status": "0",

        # 实际支付信息
        "real_pay_usd": "0.00",
        "real_pay_cny": "0.00",
        "real_put_usd": "0.00",
        "real_put_cny": "0.00",
        "real_put_discount_rate": "0.00",
        "exchange_rate": "0.0000",
        "folde_pay_usd": "0.00",
        "folde_put_usd": "0.00",
        "folde_pay_total": "0.00",
        "folde_put_total": "0.00",
        "gross_margin": "0.00",
        "gross_margin_rate": "0.00",
        "is_special_pay": "0",
        "is_loan_before_invoice": "0",
        "is_fee_miss": "0",
        "fee_miss_name": "",
        "is_usd_project": "2",
        "pay_status": "1",
        "entrust_status": "2",

        # 状态名称
        "is_traverse_name": "未推送",
        "policy_match": "auto",
        "policy_match_name": "自动匹配",
        "real_discount_status_name": "—",
        "expect_discount_status_name": "—",
        "expect_policy_status_name": "",
        "policy_status_name": "",
        "subsidy_category_name": "—",
        "expect_subsidy_category_name": "—",
        "real_subsidy_category_name": "—",
        "pol_port_name": "ANTING,CHINA",
        "pod_port_name": "AOSHANWEI,CHINA",
        "del_port_name": "AOSHANWEI,CHINA",
        "cargo_type_name": "",
        "period_rule_name": "",
        "trade_term_name": "",
        "carrier_name": "",
        "terms_transport_name": "CY/CY",
        "terms_payment_name": "T/T",
        "pay_type_name": "",
        "m_delivery_type_name": "",
        "audit": [],
        "enable": "1",
        "discount_status": "2",
        "discount_currency": "",
        "book_upload_date": "0",
        "trans_cost_put_preserve_date": "0",
        "bl_no_upload_date": "0",
        "customer_invoice_status_name": "未开票",
        "customer_writeoff_status_name": "未核销",
        "supplier_account_status_name": "未结清",
        "supplier_invoice_status_name": "未开票",
        "supplier_writeoff_status_name": "未核销",
        "customer_account_status_name": "未结清",
        "reverse_status_name": "否",
        "is_delayed_recovery_name": "否",
        "finance_status": True,
        "policy_type_name": "结算业务",
        "business_type_name": "海运整箱",

        # 主体信息
        "policy_main_arr": [
            {"fee_main_id": "1", "main_name": "青岛易航道物流科技有限公司"},
            {"fee_main_id": "3", "main_name": "青岛易汇联供应链管理有限公司"},
            {"fee_main_id": "2", "main_name": "青岛易汇航供应链管理有限公司"},
            {"fee_main_id": "6", "main_name": "上海一帜物流科技有限公司"}
        ],
        "main_ids_name": "易航道,易汇联,青岛易汇航,上海一帜",
        "order_sub_no": "",
    }

    # 供应商模板（提交时使用）
    SUBMIT_SUPPLIER_TEMPLATE = [{
        "order_supplier_id": "",
        "order_id": "",
        "isset_supplier": "1",
        "is_primary": "1",
        "supplier_id": "61224",
        "supplier_name": "芜湖长信科技股份有限公司",
        "settle_object_id": "92102",
        "user_id": "16",
        "user_name": "荣洋",
        "service_item": "booking_space",
        "supplier_period": "30",
        "settlement_date": "19",
        "supplier_pay_date": "0",
        "is_manual": "0",
        "sys_upttime": "",
        "supplier_label": "芜湖长信科技股份有限公司-订舱",
        "service_item_name": "订舱",
        "isset_fee": False
    }]

    # Container 默认模板
    DEFAULT_CONTAINER = [{
        "box_type": "AIR",
        "box_num": "1",
        "box_no": ["1"],
        "seal_number": [""],
        "sea_trans_unit_price": "1"
    }]

    @classmethod
    def get_submit_fields(cls) -> Dict[str, Any]:
        """
        获取提交必填字段（完整默认数据）

        Returns:
            提交必填字段字典
        """
        return cls.SUBMIT_REQUIRED_DEFAULTS.copy()

    @classmethod
    def get_submit_fields_with_overrides(cls, **overrides) -> Dict[str, Any]:
        """
        获取带自定义覆盖的提交必填字段

        Args:
            **overrides: 要覆盖的字段，如 trade_term="FOB", shipper="自定义发货人"

        Returns:
            覆盖后的提交必填字段字典
        """
        fields = cls.get_submit_fields()
        fields.update(overrides)
        return fields

    @classmethod
    def get_partial_submit_fields(cls, *field_names: str) -> Dict[str, Any]:
        """
        获取部分提交必填字段（用于预配置）

        Args:
            *field_names: 要包含的字段名，如 "trade_term", "carrier"

        Returns:
            仅包含指定字段的部分字典
        """
        all_fields = cls.get_submit_fields()
        return {k: v for k, v in all_fields.items() if k in field_names}


# ==========================
# 新增订单数据类 - 继承基础字段
# ==========================
class AddOrderData:
    """
    新增订单数据

    使用方式：
    - 默认：仅使用基础字段（提交必填字段为空）
    - 可选：预填部分提交必填字段

    示例：
        # 仅基础字段
        payload = AddOrderData.get_add_payload(bl_no)

        # 预填部分提交必填字段
        payload = AddOrderData.get_add_payload_with_submit_fields(
            bl_no,
            trade_term="FOB",
            carrier="MSC"
        )
    """

    @classmethod
    def get_add_payload(cls, bl_no: str = None) -> Dict[str, Any]:
        """
        获取新增订单载荷（仅基础字段，提交必填字段为空）

        Args:
            bl_no: 提单号

        Returns:
            新增订单请求参数字典
        """
        return BaseOrderData.get_base_payload(bl_no)

    @classmethod
    def get_add_payload_with_submit_fields(cls, bl_no: str = None, **submit_fields) -> Dict[str, Any]:
        """
        获取新增订单载荷（基础字段 + 部分提交必填字段）

        Args:
            bl_no: 提单号
            **submit_fields: 预填的提交必填字段

        Returns:
            合并后的新增订单参数字典
        """
        payload = BaseOrderData.get_base_payload(bl_no)
        payload.update(submit_fields)
        return payload

    @classmethod
    def get_add_payload_with_supplier(cls, supplier: List[Dict] = None, bl_no: str = None) -> Dict[str, Any]:
        """
        获取带自定义供应商的新增订单载荷

        Args:
            supplier: 自定义供应商列表
            bl_no: 提单号

        Returns:
            请求参数字典
        """
        payload = cls.get_add_payload(bl_no)
        if supplier is not None:
            payload["supplier"] = supplier
        return payload


# ==========================
# 订单分发数据类
# ==========================
class DistributeOrderData:
    """
    订单分发数据

    使用方式与 AddOrderData 类似
    """

    @classmethod
    def get_distribute_payload(cls, order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
        """
        获取订单分发载荷（仅基础字段 + order_info）

        Args:
            order_info: 查询接口返回的订单数据（包含 order_id）
            bl_no: 提单号

        Returns:
            分发订单请求参数字典
        """
        payload = BaseOrderData.get_base_payload(bl_no)
        payload["entrust_status"] = 2

        if order_info.get("order_id"):
            payload["order_id"] = order_info["order_id"]
        if order_info.get("order_no"):
            payload["order_no"] = order_info["order_no"]

        return payload

    @classmethod
    def get_distribute_payload_with_submit_fields(
        cls,
        order_info: Dict[str, Any],
        bl_no: str = None,
        **submit_fields
    ) -> Dict[str, Any]:
        """
        获取订单分发载荷（基础字段 + 部分提交必填字段）

        Args:
            order_info: 查询接口返回的订单数据
            bl_no: 提单号
            **submit_fields: 预填的提交必填字段

        Returns:
            合并后的分发订单参数字典
        """
        payload = cls.get_distribute_payload(order_info, bl_no)
        payload.update(submit_fields)
        return payload


# ==========================
# 订单提交数据类 - 合并基础字段 + 提交必填字段
# ==========================
class SubmitOrderData:
    """
    订单提交数据

    提交时必须包含：
    - BaseOrderData 基础字段
    - SubmitRequiredFields 提交必填字段
    - order_info 中的 order_id/order_no

    使用方式：
        # 标准提交
        payload = SubmitOrderData.get_submit_payload(order_info, bl_no)

        # 自定义部分提交字段
        payload = SubmitOrderData.get_submit_payload_with_overrides(
            order_info,
            bl_no,
            trade_term="FOB",
            carrier="MSC",
            shipper="自定义发货人"
        )
    """

    @classmethod
    def get_submit_payload(cls, order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
        """
        获取订单提交载荷（基础字段 + 完整提交必填字段）

        Args:
            order_info: 查询接口返回的订单数据（包含 order_id）
            bl_no: 提单号

        Returns:
            提交订单请求参数字典
        """
        payload = BaseOrderData.get_base_payload(bl_no)
        payload.update(SubmitRequiredFields.get_submit_fields())
        cls._update_payload_common(payload, order_info, bl_no)
        return payload

    @classmethod
    def get_submit_payload_with_overrides(
        cls,
        order_info: Dict[str, Any],
        bl_no: str = None,
        **submit_overrides
    ) -> Dict[str, Any]:
        """
        获取订单提交载荷（带自定义覆盖）

        Args:
            order_info: 查询接口返回的订单数据
            bl_no: 提单号
            **submit_overrides: 要覆盖的提交字段

        Returns:
            覆盖后的提交参数字典
        """
        payload = BaseOrderData.get_base_payload(bl_no)
        fields = SubmitRequiredFields.get_submit_fields()
        fields.update(submit_overrides)
        payload.update(fields)
        cls._update_payload_common(payload, order_info, bl_no)
        return payload

    @classmethod
    def get_submit_payload_from_add_data(
        cls,
        add_payload: Dict[str, Any],
        order_info: Dict[str, Any] = None,
        bl_no: str = None
    ) -> Dict[str, Any]:
        """
        从新增载荷生成提交载荷

        适用于：新增时预填了部分提交字段，需要基于此生成完整提交数据

        Args:
            add_payload: 新增订单时的载荷
            order_info: 查询接口返回的订单数据（可选）
            bl_no: 提单号

        Returns:
            提交订单请求参数字典
        """
        payload = add_payload.copy() if add_payload else BaseOrderData.get_base_payload(bl_no)
        payload.update(SubmitRequiredFields.get_submit_fields())
        if order_info:
            cls._update_payload_common(payload, order_info, bl_no)
        return payload

    @classmethod
    def _update_payload_common(cls, payload: Dict[str, Any], order_info: Dict[str, Any], bl_no: str = None):
        """更新通用字段"""
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

        common_fields = [
            "customer_category", "customer_tax_number", "customer_address_cn",
            "customer_contact_phone", "customer_main_id", "customer_main_name",
            "business_main_id", "business_main_name"
        ]
        for field in common_fields:
            if order_info.get(field):
                payload[field] = order_info[field]

        supplier = SubmitRequiredFields.SUBMIT_SUPPLIER_TEMPLATE.copy()
        if order_info.get("supplier") and len(order_info.get("supplier", [])) > 0:
            orig_sup = order_info["supplier"][0]
            supplier[0]["order_supplier_id"] = orig_sup.get("order_supplier_id", "")
            supplier[0]["order_id"] = orig_sup.get("order_id", "")
            supplier[0]["sys_upttime"] = orig_sup.get("sys_upttime", "")

        payload["supplier"] = supplier
        payload["action"] = "submit"
        payload["status"] = 2
        payload["entrust_status"] = 2

        if not payload.get("container"):
            payload["container"] = SubmitRequiredFields.DEFAULT_CONTAINER


# ==========================
# 兼容性别名 - 保留旧接口以兼容现有测试
# ==========================
class AddOrderDataCompat(AddOrderData):
    """兼容旧的 AddOrderData 接口"""
    pass


class DistributeOrderDataCompat(DistributeOrderData):
    """兼容旧的 DistributeOrderData 接口"""

    @classmethod
    def get_distribute_payload(cls, order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
        return super().get_distribute_payload(order_info, bl_no)


class SubmitOrderDataCompat(SubmitOrderData):
    """兼容旧的 SubmitOrderData 接口"""
    pass
