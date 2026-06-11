"""
API 层 - 订单相关接口封装
"""
from typing import Dict, Any, Optional, List
from core.http_client import http
from data.order_data import (
    OrderTestData,
    AddOrderData,
    DistributeOrderData,
    SubmitOrderData,
    BaseOrderData,
    SubmitRequiredFields,
    BookRealAmountData,
    FeeNoticeData,
    FeeConfirmData,
    generate_bl_no
)
from config.settings import ORDER_OPERATOR_CONFIG


class OrderApi:
    """订单相关 API"""

    # 接口地址
    ENTRUSTED_ORDER_URL = "/api/order/orderEntrust/orderPage"  # 委托订单列表
    BUSINESS_ORDER_URL = "/api/order/order/orderPage"          # 业务订单列表
    ADD_ORDER_URL = "/api/order/orderEntrust/orderAdd"          # 新增订单
    DISTRIBUTE_ORDER_URL = "/api/order/orderEntrust/orderAdd"   # 订单分发（与新增同一接口）
    SUBMIT_ORDER_URL = "/api/order/order/orderAdd"              # 订单提交
    GENERATE_SUB_ORDER_URL = "/api/order/order/generateOrderSub"  # 生成子订单
    BOOK_REAL_AMOUNT_URL = "/api/order/orderFee/bookRealAmountEdit"  # 订舱费用录费用
    FEE_NOTICE_URL = "/api/order/order/orderNotice"  # 生成费用通知单
    FEE_CONFIRM_URL = "/api/order/order/orderConfirmLoan"  # 生成费用确认单

    @classmethod
    def get_entrust_order_list(
        cls,
        page_no: int = 1,
        page_size: int = 20,
        order_no: str = "",
        customer_id: str = "",
        create_id: List[str] = None,
        status: str = "",
        sort_field: str = "update_time",
        sort_order: str = "desc",
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        获取委托订单列表

        Args:
            page_no: 页码
            page_size: 每页数量
            order_no: 订单号（精确查询）
            customer_id: 客户ID
            create_id: 创建者ID列表
            status: 订单状态
            sort_field: 排序字段
            sort_order: 排序方向（asc/desc）
            params: 扩展参数
            **kwargs: 其他参数

        Returns:
            Response 对象
        """
        if create_id is None:
            create_id = []
        if params is None:
            params = {}

        payload = {
            "page_no": page_no,
            "page_size": page_size,
            "order_no": order_no,
            "customer_id": customer_id,
            "create_id": create_id,
            "status": status,
            "sort_field": sort_field,
            "sort_order": sort_order,
            "params": params,
            **kwargs
        }

        return http.post(cls.ENTRUSTED_ORDER_URL, json=payload)

    @classmethod
    def get_latest_order_by_creator(cls, create_id: str = None) -> Dict[str, Any]:
        """
        查询指定创建者的最新订单

        Args:
            create_id: 创建者用户ID

        Returns:
            最新订单数据（字典），如果查询失败或没有订单返回空字典
        """
        if create_id is None:
            create_id = ORDER_OPERATOR_CONFIG["create_id"]

        resp = cls.get_entrust_order_list(
            page_no=1,
            page_size=1,
            create_id=[create_id],
            sort_field="update_time",
            sort_order="desc"
        )
        data = resp.json()

        if data.get("code") == 200:
            orders = data.get("data", {}).get("data", [])
            if orders and len(orders) > 0:
                return orders[0]

        return {}

    @classmethod
    def get_order_by_bl_no(cls, bl_no: str) -> Dict[str, Any]:
        """
        按提单号查询订单（精确匹配）

        Args:
            bl_no: 提单号

        Returns:
            订单数据（字典），如果查询失败或没有订单返回空字典
        """
        payload = {
            "page_no": 1,
            "page_size": 20,
            "order_no": "",
            "customer_id": "",
            "bl_nos": [],
            "service_items": "",
            "is_traverse": "",
            "status": "",
            "fee_lock_status": "",
            "customer_account_status": "",
            "create_id": "",
            "bl_no": bl_no,
            "sort_field": "update_time",
            "sort_order": "desc",
            "params": {}
        }

        resp = http.post(cls.ENTRUSTED_ORDER_URL, json=payload)
        data = resp.json()

        if data.get("code") == 200:
            orders = data.get("data", {}).get("data", [])
            if orders and len(orders) > 0:
                return orders[0]

        return {}

    @classmethod
    def get_container_from_order(cls, order_no: str = None, bl_no: str = None) -> List[Dict[str, Any]]:
        """
        从业务订单详情中提取箱信息（用于订单锁定审批）

        Args:
            order_no: 业务订单号（精确查询）
            bl_no  : 提单号（备用）

        Returns:
            container 列表
        """
        resp = cls.get_business_order_list(order_no=order_no, bl_no=bl_no)
        data = resp.json()
        records = data.get("data", {}).get("data", [])
        order = records[0] if records else {}
        sub_list = order.get("data", []) if isinstance(order.get("data"), list) else []
        container = []
        for sub in sub_list:
            for c in (sub.get("container") or []):
                container.append({
                    "order_container_id": c.get("order_container_id", ""),
                    "box_type": c.get("box_type", ""),
                    "box_num": c.get("box_num", ""),
                    "box_no": c.get("box_no") or [""],
                    "seal_number": c.get("seal_number") or [""],
                    "sea_trans_unit_price": c.get("sea_trans_unit_price", 1),
                })
        return container

    @classmethod
    def get_business_order_list(
        cls,
        page_no: int = 1,
        page_size: int = 20,
        order_no: str = "",
        customer_id: Optional[List[str]] = None,
        sort_field: str = "update_time",
        sort_order: str = "desc",
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        获取业务订单列表

        Args:
            page_no: 页码
            page_size: 每页数量
            order_no: 订单号（精确查询）
            customer_id: 客户ID列表（批量查询）
            sort_field: 排序字段
            sort_order: 排序方向（asc/desc）
            params: 扩展参数
            **kwargs: 其他参数

        Returns:
            Response 对象
        """
        if customer_id is None:
            customer_id = []
        if params is None:
            params = {}

        payload = {
            "page_no": page_no,
            "page_size": page_size,
            "order_no": order_no,
            "customer_id": customer_id,
            "sort_field": sort_field,
            "sort_order": sort_order,
            "params": params,
            **kwargs
        }

        return http.post(cls.BUSINESS_ORDER_URL, json=payload)

    @classmethod
    def get_entrust_order_by_data(cls, data: Dict[str, Any]) -> Any:
        """使用预定义数据获取委托订单"""
        return http.post(cls.ENTRUSTED_ORDER_URL, json=data)

    @classmethod
    def get_business_order_by_data(cls, data: Dict[str, Any]) -> Any:
        """使用预定义数据获取业务订单"""
        return http.post(cls.BUSINESS_ORDER_URL, json=data)

    @classmethod
    def add_order(cls, payload: Dict[str, Any] = None, bl_no: str = None) -> Any:
        """
        新增委托订单

        Args:
            payload: 自定义请求载荷
            bl_no: 自定义提单号（默认自动生成）

        Returns:
            Response 对象
        """
        if payload is None:
            payload = AddOrderData.get_add_payload(bl_no)

        return http.post(cls.ADD_ORDER_URL, json=payload)

    @classmethod
    def distribute_order(cls, order_info: Dict[str, Any], bl_no: str = None) -> Any:
        """
        订单分发

        Args:
            order_info: 新增订单响应的 data 数据（包含 order_id, supplier 等）
            bl_no: 提单号（默认使用 order_info 中的 bl_no）

        Returns:
            Response 对象
        """
        payload = DistributeOrderData.get_distribute_payload(order_info, bl_no)
        return http.post(cls.DISTRIBUTE_ORDER_URL, json=payload)

    @classmethod
    def add_and_distribute_order(cls) -> tuple:
        """
        新增订单并分发（完整流程）

        Returns:
            tuple: (add_resp, add_data, distribute_resp)
            - add_resp: 新增订单响应对象
            - add_data: 新增订单响应的 data
            - distribute_resp: 分发订单响应对象
        """
        # 1. 新增订单
        add_resp = cls.add_order()
        add_data = add_resp.json().get("data", {})

        # 2. 分发订单
        distribute_resp = cls.distribute_order(add_data)

        return add_resp, add_data, distribute_resp

    @classmethod
    def submit_order(cls, order_info: Dict[str, Any], bl_no: str = None) -> Any:
        """
        订单提交

        Args:
            order_info: 分发订单响应的 data 数据
            bl_no: 提单号（必须与新增/分发订单一致）

        Returns:
            Response 对象
        """
        payload = SubmitOrderData.get_submit_payload(order_info, bl_no)
        return http.post(cls.SUBMIT_ORDER_URL, json=payload)

    @classmethod
    def generate_sub_order(cls, order_id: str) -> Any:
        """
        生成子订单

        Args:
            order_id: 订单ID，来源于链路中使用的 order_id

        Returns:
            Response 对象
        """
        payload = {"order_id": order_id}
        return http.post(cls.GENERATE_SUB_ORDER_URL, json=payload)

    @classmethod
    def book_real_amount(
        cls,
        order_id: str,
        to_customer_fees: List[Dict[str, Any]] = None,
        to_supplier_fees: List[Dict[str, Any]] = None,
    ) -> Any:
        """
        订舱费用录费用接口

        Args:
            order_id         : 订单ID（必填）
            to_customer_fees: 应收费用行列表（从 fee.yaml 读取后传入）
            to_supplier_fees: 应付费用行列表（从 fee.yaml 读取后传入）

        Returns:
            Response 对象
        """
        payload = BookRealAmountData.get_payload(
            order_id=order_id,
            to_customer_fees=to_customer_fees,
            to_supplier_fees=to_supplier_fees,
        )
        return http.post(cls.BOOK_REAL_AMOUNT_URL, json=payload)


    @classmethod
    def stash_order(cls, order_info: Dict[str, Any], bl_no: str = None) -> Any:
        """
        订单暂存（与提交接口相同，status=1）

        Args:
            order_info: 订单信息（需包含 order_id、order_no 等）
            bl_no: 提单号

        Returns:
            Response 对象
        """
        payload = BaseOrderData.get_base_payload(bl_no)
        payload.update(SubmitRequiredFields.get_submit_fields())

        if bl_no:
            payload["bl_no"] = bl_no
        elif order_info.get("bl_no"):
            payload["bl_no"] = order_info["bl_no"]

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
        payload["action"] = "stash"
        payload["status"] = 1
        payload["entrust_status"] = 2

        if not payload.get("container"):
            payload["container"] = SubmitRequiredFields.DEFAULT_CONTAINER

        return http.post(cls.SUBMIT_ORDER_URL, json=payload)

    @classmethod
    def add_distribute_submit_workflow(cls, use_query_for_order_id: bool = True) -> Dict[str, Any]:
        """
        新增 -> 查询最新订单 -> 分发 -> 提交（完整流程）

        Args:
            use_query_for_order_id: 是否通过查询获取 order_id（默认 True）

        Returns:
            Dict: {
                "add_resp": 新增订单响应,
                "add_data": 新增订单 data,
                "latest_order": 查询到的最新订单信息,
                "distribute_resp": 分发订单响应,
                "distribute_data": 分发订单 data,
                "submit_resp": 提交订单响应,
                "bl_no": 使用的提单号,
                "order_id": 使用的订单ID
            }
        """
        # 1. 生成提单号
        bl_no = generate_bl_no()

        # 2. 新增订单
        add_resp = cls.add_order(bl_no=bl_no)
        add_data = add_resp.json()

        # 3. 查询最新的订单，获取 order_id
        create_id = ORDER_OPERATOR_CONFIG["create_id"]
        latest_order = cls.get_latest_order_by_creator(create_id)
        order_id = latest_order.get("order_id", "")

        # 4. 分发订单
        distribute_payload = DistributeOrderData.get_distribute_payload(latest_order, bl_no)
        distribute_resp = http.post(cls.DISTRIBUTE_ORDER_URL, json=distribute_payload)
        distribute_data = distribute_resp.json()

        # 5. 提交订单
        submit_payload = SubmitOrderData.get_submit_payload(latest_order, bl_no)
        submit_resp = http.post(cls.SUBMIT_ORDER_URL, json=submit_payload)

        return {
            "add_resp": add_resp,
            "add_data": add_data,
            "latest_order": latest_order,
            "distribute_resp": distribute_resp,
            "distribute_data": distribute_data,
            "submit_resp": submit_resp,
            "bl_no": bl_no,
            "order_id": order_id
        }

    @classmethod
    def generate_fee_notice(
        cls,
        order_id: str,
        finance_ids: List[str] = None,
        bank_ids: List[str] = None,
        action: str = "submit",
    ) -> Any:
        """
        生成费用通知单

        Args:
            order_id   : 业务订单ID（从链路流程获取）
            finance_ids: 费用ID列表
            bank_ids   : 账户ID列表
            action     : 操作类型

        Returns:
            Response 对象
        """
        payload = FeeNoticeData.get_generate_payload(
            order_id=order_id,
            finance_ids=finance_ids,
            bank_ids=bank_ids,
            action=action,
        )
        return http.post(cls.FEE_NOTICE_URL, json=payload)

    @classmethod
    def generate_fee_confirm(
        cls,
        order_id: str,
        finance_ids: List[str] = None,
        bank_ids: List[str] = None,
        action: str = "submit",
    ) -> Any:
        """
        生成费用确认单

        Args:
            order_id   : 业务订单ID（从链路流程获取）
            finance_ids: 费用ID列表
            bank_ids   : 账户ID列表
            action     : 操作类型

        Returns:
            Response 对象
        """
        payload = FeeConfirmData.get_generate_payload(
            order_id=order_id,
            finance_ids=finance_ids,
            bank_ids=bank_ids,
            action=action,
        )
        return http.post(cls.FEE_CONFIRM_URL, json=payload)
