"""
API 层 - 应付发票上传与登记相关接口封装

涉及流程：应付发票上传与登记（LK22）
  1. POST /api/home/common/uploadFile                    - 上传发票文件（通用接口）
  2. POST /api/finance/payInvoice/invoiceAdd             - 登记应付发票
  3. POST /api/finance/payInvoice/invoicePage            - 按 bl_no 查询应付发票登记ID
  4. POST /api/Finance/PayInvoiceBatch/applyPage         - 按 bl_no 查询应付开票申请ID
  5. POST /api/finance/payInvoice/allocationInvoiceFee    - 分配发票到费用

所有枚举值、常量默认值统一从 data/pay/payable_invoice_upload.yaml 读取，勿在代码中硬编码。
"""
import os
from typing import Any, Dict, List

from core.http_client import http
from data.pay import PIUP_INVOICE_FILENAME, PayableInvoiceUploadData


class PayInvoiceRegisterApi:
    """应付发票上传与登记相关 API"""

    PAY_UPLOAD_FILE_URL = "/api/home/common/uploadFile"
    PAY_INVOICE_ADD_URL = "/api/finance/payInvoice/invoiceAdd"
    PAY_INVOICE_PAGE_URL = "/api/finance/payInvoice/invoicePage"
    PAY_APPLY_PAGE_URL = "/api/Finance/PayInvoiceBatch/applyPage"
    PAY_ALLOCATION_INVOICE_FEE_URL = "/api/Finance/payInvoiceBatch/allocationInvoiceFee"

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
            page      : 页面标识（默认 pay）

        Returns:
            Response 对象，data 包含 file_id, file_name, file_url, file_type, original_name
        """
        if page is None:
            page = "pay"
        filename = os.path.basename(file_path)
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
    def invoice_page(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Any:
        """
        按 bl_no 查询应付发票登记ID（invoicePage）

        用于 LK22 Step 3（发票登记ID）。

        Args:
            bl_no              : 提单号（精确查询）
            page_no            : 页码（默认 1）
            page_size          : 每页数量（默认 20）
            create_time_start  : 创建时间开始（Unix 秒）
            create_time_end    : 创建时间结束（Unix 秒）

        Returns:
            Response 对象，data 含 pay_invoice_id
        """
        payload = PayableInvoiceUploadData.build_invoice_page_payload(
            bl_no=bl_no,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
        )
        return http.post(cls.PAY_INVOICE_PAGE_URL, json=payload)

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

        用于 LK22 Step 3（开票申请ID）。

        Args:
            bl_nos             : 提单号列表（**必填**）
            page_no            : 页码（默认 1）
            page_size          : 每页数量（默认 20）
            create_time_start  : 创建时间开始（Unix 秒）
            create_time_end    : 创建时间结束（Unix 秒）

        Returns:
            Response 对象，data.data[0] 含 pay_invoice_apply_id
        """
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
        payload = PayableInvoiceUploadData.build_allocation_payload(
            pay_invoice_apply_id=pay_invoice_apply_id,
            pay_invoice_id=pay_invoice_id,
            un_amount=un_amount,
            action=action,
        )
        return http.post(cls.PAY_ALLOCATION_INVOICE_FEE_URL, json=payload)
