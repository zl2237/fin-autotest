"""
API 层 - 应付对账批次接口封装

涉及流程：
  发起应付对账批次（LK19）：
    1. POST /api/finance/accountFee/financePayList         - 按 bl_no 查询应付项列表
    2. POST /api/finance/payAccount/orderPayAccountEdit    - 发起应付对账批次

  确认应付对账（LK20）：
    3. POST /api/finance/payAccount/payAccountPage         - 确认前查询应付对账批次
    4. POST /api/finance/payAccount/accountConfirm         - 确认应付对账

  发起应付开票申请（LK21）：
    5. POST /api/finance/accountFee/financePayList         - 查询应付开票项（开票模式）
    6. POST /api/Finance/payInvoiceBatch/getOrderInfoByFeeId  - 查询开票订单信息
    7. POST /api/Finance/payInvoiceBatch/batchOrderEdit    - 发起应付开票批次申请（apply_type=2）

  应付发票上传与登记（LK22）：
    8. POST /api/home/common/uploadFile                    - 上传发票文件（通用接口）
    9. POST /api/finance/payInvoice/invoiceAdd             - 登记应付发票
    10. POST /api/finance/payInvoice/invoicePage          - 按 bl_no 查询应付发票登记ID
    11. POST /api/finance/payInvoice/allocationInvoiceFee - 分配发票到费用

所有枚举值、常量默认值统一从 data/pay/*.yaml 读取，勿在代码中硬编码。
"""
from typing import Any, Dict, List

from core.http_client import http
from data.pay import (
    OPERATE_TYPE_BILL_OF_LADING,
    ACCOUNT_TYPE_CROSS_CUSTOMER,
    PAGE_NO_DEFAULT,
    PAGE_SIZE_STANDARD,
    PAY_ACCOUNT_ACTION_SUBMIT,
    ACCOUNT_CONFIRM_TYPE,
    ACCOUNT_CONFIRM_QUICK_STATUS,
    PayableAccountData,
    PayableInvoiceData,
)


class PayableApi:
    """应付对账批次 API"""

    FINANCE_PAY_LIST_URL = "/api/finance/accountFee/financePayList"
    ORDER_PAY_ACCOUNT_EDIT_URL = "/api/finance/payAccount/orderPayAccountEdit"
    PAY_ACCOUNT_PAGE_URL = "/api/finance/payAccount/payAccountPage"
    ACCOUNT_CONFIRM_URL = "/api/finance/payAccount/accountConfirm"
    PAY_GET_ORDER_INFO_BY_FEE_ID_URL = "/api/Finance/payInvoiceBatch/getOrderInfoByFeeId"
    PAY_BATCH_ORDER_EDIT_URL = "/api/Finance/payInvoiceBatch/batchOrderEdit"
    # -- link22 应付发票上传与登记 --
    PAY_UPLOAD_FILE_URL = "/api/home/common/uploadFile"
    PAY_INVOICE_ADD_URL = "/api/finance/payInvoice/invoiceAdd"
    PAY_APPLY_PAGE_URL = "/api/Finance/PayInvoiceBatch/applyPage"
    PAY_ALLOCATION_INVOICE_FEE_URL = "/api/Finance/payInvoiceBatch/allocationInvoiceFee"

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

    @classmethod
    def query_pay_account_page(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
        account_status: List[str] = None,
    ) -> Any:
        """
        查询应付对账批次分页列表（payAccountPage，用于确认前验证状态）

        响应 data.data[0].pay_account_id 为应付对账批次ID。

        Args:
            bl_no              : 提单号（精确查询，来自上游链路）
            page_no            : 页码（默认 PAGE_NO_DEFAULT）
            page_size          : 每页数量（默认 PAGE_SIZE_STANDARD）
            create_time_start  : 创建时间开始（Unix 秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 秒，默认 1 年后）
            account_status     : 账户状态列表（默认 ["1"]=对账中）

        Returns:
            Response 对象
        """
        payload = PayableAccountData.get_pay_account_page_payload(
            bl_no=bl_no,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
            account_status=account_status,
        )
        return http.post(cls.PAY_ACCOUNT_PAGE_URL, json=payload)

    @classmethod
    def confirm_pay_account(
        cls,
        pay_account_id: str,
        confirm_type: int = None,
        quick_status: int = None,
    ) -> Any:
        """
        确认应付对账（accountConfirm）

        响应 data 为空，code=200 即确认成功。

        Args:
            pay_account_id : 应付对账批次ID（来自 payAccountPage 查询或 orderPayAccountEdit 响应）
            confirm_type   : 确认类型（默认 0=待确认）
            quick_status   : 快捷确认标识（默认 1）

        Returns:
            Response 对象
        """
        payload = PayableAccountData.get_account_confirm_payload(
            pay_account_id=pay_account_id,
            confirm_type=confirm_type,
            quick_status=quick_status,
        )
        return http.post(cls.ACCOUNT_CONFIRM_URL, json=payload)

    @classmethod
    def query_finance_pay_list_for_invoice(
        cls,
        bl_no: str,
        main_id: str = None,
        pay_settle_object_id: str = None,
        pay_settle_object: str = None,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Any:
        """
        查询应付开票项列表（financePayList，开票模式）

        与对账模式共用同一接口，仅 search_style/batch_type 不同。
        用于 LK21 发起应付开票申请。

        注意：main_id / pay_settle_object_id / pay_settle_object 三个字段**必填**。
        优先级：显式入参 > YAML 默认值；都没有则抛 AssertionError。

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
            Response 对象
        """
        payload = PayableInvoiceData.get_finance_pay_list_invoice_payload(
            bl_no=bl_no,
            main_id=main_id,
            pay_settle_object_id=pay_settle_object_id,
            pay_settle_object=pay_settle_object,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
        )
        return http.post(cls.FINANCE_PAY_LIST_URL, json=payload)

    @classmethod
    def get_order_info_by_fee_id(
        cls,
        order_fee_real_ids: List[str],
        exchange_rate: Any = None,
        usd_invoice_remark: int = None,
        style: int = None,
    ) -> Any:
        """
        查询开票订单信息（getOrderInfoByFeeId）

        响应 data 为列表，每项包含 book_supplier_id / book_supplier_name /
        order_sub_id / real_amount / fee_real_name 等字段，
        用于构建 batchOrderEdit 请求体。

        Args:
            order_fee_real_ids : 费用实付 ID 列表
            exchange_rate      : 汇率（默认 GOBI_DEFAULT_EXCHANGE_RATE）
            usd_invoice_remark : 备注模式（默认 GOBI_USD_INVOICE_REMARK=0）
            style              : 模式（默认 GOBI_STYLE=1）

        Returns:
            Response 对象
        """
        payload = PayableInvoiceData.get_order_info_by_fee_id_payload(
            order_fee_real_ids=order_fee_real_ids,
            exchange_rate=exchange_rate,
            usd_invoice_remark=usd_invoice_remark,
            style=style,
        )
        return http.post(cls.PAY_GET_ORDER_INFO_BY_FEE_ID_URL, json=payload)

    @classmethod
    def submit_pay_invoice_batch(
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
    ) -> Any:
        """
        发起应付开票批次申请（batchOrderEdit，apply_type=2）

        应付方向：提交即生效，无需审批（无 link16 等价步骤）。
        响应 data 为空，code=200 即开票批次创建成功，
        后续可用于 link22 应付开票登记。

        Args:
            order_info_data_list : getOrderInfoByFeeId 响应 data 列表
            finance_pay_records  : financePayList（开票模式）响应 data 列表
            main_id              : 主体ID
            main_name            : 主体名称
            pay_settle_object    : 付款结算对象名称
            pay_settle_object_id : 付款结算对象ID
            exchange_rate        : 汇率
            customer_id          : 客户ID（可选，自动从 finance_pay_records 取）
            customer_name        : 客户名称
            batch_order_remark   : 批次备注
            action               : 操作类型（默认 submit）

        Returns:
            Response 对象
        """
        payload = PayableInvoiceData.build_batch_order_edit_pay_payload(
            order_info_data_list=order_info_data_list,
            finance_pay_records=finance_pay_records,
            main_id=main_id,
            main_name=main_name,
            pay_settle_object=pay_settle_object,
            pay_settle_object_id=pay_settle_object_id,
            exchange_rate=exchange_rate,
            customer_id=customer_id,
            customer_name=customer_name,
            batch_order_remark=batch_order_remark,
            action=action,
        )
        return http.post(cls.PAY_BATCH_ORDER_EDIT_URL, json=payload)

    # =====================================================================
    # LK22：应付发票上传与登记
    # =====================================================================

    @classmethod
    def upload_pay_invoice_file(
        cls,
        file_path: str,
        page: str = None,
    ) -> Any:
        """
        上传发票文件（uploadFile，通用接口）

        用于 LK22 Step 1。

        Args:
            file_path : 文件本地路径（完整路径）
            page      : 页面标识（默认从 YAML 读取：pay）

        Returns:
            Response 对象，data 包含 file_id, file_name, file_url, file_type, original_name
        """
        import os as _os
        from data.pay import PIUP_INVOICE_FILENAME

        if page is None:
            page = "pay"
        filename = _os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {
                "file": (filename, f, "application/pdf"),
            }
            data = {"page": page}
            return http.post(cls.PAY_UPLOAD_FILE_URL, data=data, files=files)

    @classmethod
    def invoice_add(
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
    ) -> Any:
        """
        登记应付发票（invoiceAdd）

        用于 LK22 Step 2。

        Args:
            file_id               : 上传后的文件ID
            file_name             : 上传后的文件名
            file_url              : 上传后的文件URL
            original_name          : 原始文件名
            invoice_number        : 发票号码（必须唯一，由调用方生成）
            invoice_amount        : 发票金额（默认从 YAML 读取）
            buyer_chinese_header  : 购买方名称（默认从 YAML 读取）
            buyer_identifier_no   : 购买方税号（默认从 YAML 读取）
            seller_chinese_header : 销售方名称（默认从 YAML 读取）
            seller_identifier_no  : 销售方税号（默认从 YAML 读取）

        Returns:
            Response 对象
        """
        from data.pay import PayableInvoiceUploadData

        payload = PayableInvoiceUploadData.build_invoice_add_payload(
            file_id=file_id,
            file_name=file_name,
            file_url=file_url,
            original_name=original_name,
            invoice_number=invoice_number,
            invoice_amount=invoice_amount,
            buyer_chinese_header=buyer_chinese_header,
            buyer_identifier_no=buyer_identifier_no,
            seller_chinese_header=seller_chinese_header,
            seller_identifier_no=seller_identifier_no,
        )
        return http.post(cls.PAY_INVOICE_ADD_URL, json=payload)

    @classmethod
    def apply_page(
        cls,
        bl_nos: List[str],
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Any:
        """
        按 bl_nos 查询应付开票申请ID（applyPage）

        用于 LK22 Step 3，从响应 data.data 中提取 pay_invoice_apply_id。

        Args:
            bl_nos             : 提单号列表（**必填**）
            page_no            : 页码（默认 1）
            page_size          : 每页数量（默认 20）
            create_time_start  : 创建时间开始（Unix 秒）
            create_time_end    : 创建时间结束（Unix 秒）

        Returns:
            Response 对象，data.data[0] 含 pay_invoice_apply_id
        """
        from data.pay import PayableInvoiceUploadData

        payload = PayableInvoiceUploadData.build_apply_page_payload(
            bl_nos=bl_nos,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
        )
        return http.post(cls.PAY_APPLY_PAGE_URL, json=payload)

    @classmethod
    def allocation_invoice_fee(
        cls,
        pay_invoice_apply_id: str,
        pay_invoice_id: str,
        un_amount: str,
        action: str = "submit",
    ) -> Any:
        """
        分配发票到费用（allocationInvoiceFee）

        用于 LK22 Step 4。

        Args:
            pay_invoice_apply_id : 应付开票申请ID（来自 applyPage 响应，**必填**）
            pay_invoice_id        : 应付发票ID（来自 invoiceAdd 响应，**必填**）
            un_amount            : 未分配金额（来自 applyPage 响应，**必填**）
            action               : 操作类型（默认 submit）

        Returns:
            Response 对象
        """
        from data.pay import PayableInvoiceUploadData

        payload = PayableInvoiceUploadData.build_allocation_payload(
            pay_invoice_apply_id=pay_invoice_apply_id,
            pay_invoice_id=pay_invoice_id,
            un_amount=un_amount,
            action=action,
        )
        return http.post(cls.PAY_ALLOCATION_INVOICE_FEE_URL, json=payload)
