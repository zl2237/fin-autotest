"""
API 层 - 应收发票上传与登记接口封装

涉及流程：发票上传与登记（LK17）
  1. POST /api/finance/receiveInvoice/invoiceAdd          - 上传应收发票
  2. POST /api/Finance/ReceiveInvoiceBatch/applyPage      - 获取发票申请ID（按提单号查询）
  3. POST /api/Finance/ReceiveInvoiceBatch/allocationInvoiceFee - 应收开票申请登记发票

所有枚举值、常量默认值统一从 data/receive_invoice_upload.yaml 读取，勿在代码中硬编码。
"""
import os
import time
from typing import Any, Dict, List

from core.http_client import http
from data.receive import _RECEIVE_INVOICE_UPLOAD_CFG


def _const(key: str, default=None):
    return _RECEIVE_INVOICE_UPLOAD_CFG.get("_constants", {}).get(key, default) if _RECEIVE_INVOICE_UPLOAD_CFG else default


def _const_for_add(key: str, default=None):
    return _RECEIVE_INVOICE_UPLOAD_CFG.get("_constants_for_add", {}).get(key, default) if _RECEIVE_INVOICE_UPLOAD_CFG else default


class InvoiceUploadApi:
    """应收发票上传与登记 API"""

    INVOICE_ADD_URL = "/api/finance/receiveInvoice/invoiceAdd"
    APPLY_PAGE_URL = "/api/Finance/ReceiveInvoiceBatch/applyPage"
    ALLOCATION_INVOICE_FEE_URL = "/api/Finance/ReceiveInvoiceBatch/allocationInvoiceFee"
    UPLOAD_FILE_URL = "/api/home/common/uploadFile"

    @classmethod
    def upload_file(cls, file_path: str, page: str = None) -> Any:
        """
        文件上传接口（Step 0）

        Args:
            file_path : 文件本地路径
            page      : 页面标识，默认从 yaml 读取（receive）

        Returns:
            Response 对象，data 包含 file_id, file_name, file_url, file_type, original_name
        """
        if page is None:
            page = _const("upload_page", "receive")
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {
                "file": (filename, f, "application/pdf"),
            }
            data = {"page": page}
            return http.post(cls.UPLOAD_FILE_URL, data=data, files=files)

    @classmethod
    def invoice_add(
        cls,
        invoice_number: str,
        invoice_type: str = None,
        invoice_type_name: str = None,
        invoice_amount: str = None,
        invoice_tax_amount: str = None,
        invoice_date: int = None,
        currency: str = None,
        usd_amount: str = None,
        invoice_exchange_rate: str = None,
        invoice_original: Dict[str, Any] = None,
        buyer_chinese_header: str = None,
        buyer_identifier_no: str = None,
        buyer_identity: str = None,
        seller_chinese_header: str = None,
        seller_identifier_no: str = None,
        seller_identity: str = None,
        invoice_image_name: str = None,
        file_path: str = None,
    ) -> Any:
        """
        上传应收发票

        响应体 data 为 dict，key = invoice_number，value = receive_invoice_id。
        例：{"API_TEST_INVOICE_202600001": "323703223292526592"}

        Args:
            invoice_number        : 发票号码（必须全局唯一，建议用时间戳+随机数）
            invoice_type          : 发票类型编码
            invoice_type_name     : 发票类型名称
            invoice_amount        : 发票金额
            invoice_tax_amount    : 发票税额
            invoice_date          : 发票日期（Unix 时间戳秒）
            currency              : 币种
            usd_amount            : USD 金额
            invoice_exchange_rate : 汇率
            invoice_original      : 发票原件（dict 包含 file_id/file_name 等）
            buyer_chinese_header  : 购买方名称
            buyer_identifier_no   : 购买方税号
            buyer_identity        : 购买方身份
            seller_chinese_header : 销售方名称
            seller_identifier_no  : 销售方税号
            seller_identity       : 销售方身份
            invoice_image_name    : 发票图片文件名
            file_path             : 发票文件路径/URL

        Returns:
            Response 对象
        """
        if invoice_type is None:
            invoice_type = _const("invoice_type", "1")
        if invoice_type_name is None:
            invoice_type_name = _const_for_add("invoice_type_name", "增值税数电普通发票")
        if invoice_amount is None:
            invoice_amount = _const("invoice_amount", "1260")
        if invoice_tax_amount is None:
            invoice_tax_amount = _const("invoice_tax_amount", "0.00")
        if invoice_date is None:
            invoice_date = int(time.time())
        if currency is None:
            currency = _const_for_add("currency", "CNY")
        if usd_amount is None:
            usd_amount = _const("usd_amount", "")
        if invoice_exchange_rate is None:
            invoice_exchange_rate = _const("invoice_exchange_rate", "1")
        if buyer_identity is None:
            buyer_identity = _const("identity_customer", "customer")
        if seller_identity is None:
            seller_identity = _const("identity_main", "main")
        if invoice_image_name is None:
            invoice_image_name = _const("invoice_image_name", "")
        if file_path is None:
            file_path = _const("file_path", "")

        payload = [{
            "invoice_number": invoice_number,
            "invoice_type": invoice_type,
            "invoice_type_name": invoice_type_name,
            "invoice_amount": invoice_amount,
            "invoice_tax_amount": invoice_tax_amount,
            "invoice_date": invoice_date,
            "currency": currency,
            "usd_amount": usd_amount,
            "invoice_exchange_rate": invoice_exchange_rate,
            "invoice_original": invoice_original or {},
            "buyer_chinese_header": buyer_chinese_header or "",
            "buyer_identifier_no": buyer_identifier_no or "",
            "buyer_identity": buyer_identity,
            "isbuyer_identity": buyer_identity,
            "seller_chinese_header": seller_chinese_header or "",
            "seller_identifier_no": seller_identifier_no or "",
            "seller_identity": seller_identity,
            "invoice_image_name": invoice_image_name,
            "file_path": file_path,
        }]

        return http.post(cls.INVOICE_ADD_URL, json=payload)

    @classmethod
    def apply_page(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
        cancel_status: List[str] = None,
        currency: List[str] = None,
        invoice_status: List[str] = None,
        writeoff_status: List[str] = None,
        sort_field: str = None,
        sort_order: str = None,
    ) -> Any:
        """
        获取发票申请分页列表（按提单号精确查询）

        响应 data.data[0].receive_invoice_apply_id 为发票申请ID。

        Args:
            bl_no              : 提单号（精确查询）
            page_no            : 页码
            page_size          : 每页条数
            create_time_start  : 创建时间开始（Unix 时间戳秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 时间戳秒，默认 1 年后）
            cancel_status      : 取消状态列表
            currency           : 币种列表
            invoice_status     : 发票状态列表
            writeoff_status   : 核销状态列表

        Returns:
            Response 对象
        """
        import datetime, logging, time
        _log = logging.getLogger(__name__)

        if create_time_start is None:
            today = datetime.date.today()
            start = today - datetime.timedelta(days=365)
            end = today + datetime.timedelta(days=365)
            create_time_start = str(int(datetime.datetime.combine(start, datetime.time.min).timestamp()))
            create_time_end = str(int(datetime.datetime.combine(end, datetime.time.max).timestamp()))
        if page_no is None:
            page_no = _const("page_no", 1)
        if page_size is None:
            page_size = _const("page_size", 20)
        if sort_field is None:
            sort_field = _const("sort_field", "create_time")
        if sort_order is None:
            sort_order = _const("sort_order_desc", "desc")
        if cancel_status is None:
            cancel_status = []
        if currency is None:
            currency = []
        if invoice_status is None:
            invoice_status = []
        if writeoff_status is None:
            writeoff_status = []

        # 重试 3 次，每次间隔 2 秒（给后端处理 apply_id 的时间）
        for attempt in range(1, 4):
            payload = {
                "page_no": page_no,
                "page_size": page_size,
                "order_no": "",
                "create_time": [
                    int(create_time_start) * 1000,
                    int(create_time_end) * 1000,
                ],
                "cancel_status": cancel_status,
                "bl_nos": [bl_no],
                "customer_id": [],
                "put_settle_object_id": [],
                "main_id": [],
                "currency": currency,
                "invoice_status": invoice_status,
                "writeoff_status": writeoff_status,
                "create_id": [],
                "sort_field": sort_field,
                "sort_order": sort_order,
                "params": {},
                "create_time_start": create_time_start,
                "create_time_end": create_time_end,
            }
            _log.info(f"[LK17 DEBUG] applyPage attempt={attempt}, bl_no={bl_no}, payload={payload}")
            resp = http.post(cls.APPLY_PAGE_URL, json=payload)
            data = resp.json()
            _log.info(f"[LK17 DEBUG] applyPage response: {data}")
            total = data.get("data", {}).get("total", 0)
            if total > 0:
                _log.info(f"[LK17 DEBUG] applyPage found {total} record(s)")
                return resp
            if attempt < 3:
                _log.warning(f"[LK17 DEBUG] applyPage attempt {attempt} returned empty, retrying in 2s...")
                time.sleep(2)
        return resp

    @classmethod
    def allocation_invoice_fee(
        cls,
        receive_invoice_apply_id: str,
        invoice_arr: List[Dict[str, Any]] = None,
        action: str = None,
    ) -> Any:
        """
        应收开票申请登记发票

        Args:
            receive_invoice_apply_id: 发票申请ID（来自 applyPage 响应）
            invoice_arr              : 发票数组，每个元素含 receive_invoice_id 和 invoice_amount_use
            action                   : 操作类型，默认 submit

        Returns:
            Response 对象
        """
        if action is None:
            action = _const("action_submit", "submit")
        if invoice_arr is None:
            invoice_arr = []

        payload = {
            "receive_invoice_apply_id": str(receive_invoice_apply_id),
            "invoice_arr": invoice_arr,
            "action": action,
        }
        return http.post(cls.ALLOCATION_INVOICE_FEE_URL, json=payload)
