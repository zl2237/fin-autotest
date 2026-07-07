"""
Workflows 层 - 应收发票上传与登记步骤（LK17）

  record_invoice_upload
      uploadFile → invoiceAdd → applyPage → allocationInvoiceFee

LK17 = LK16 + 发票上传与登记。
"""
import time as _time
from typing import Any, Dict

import allure

from api.receive.receive_invoice_register_api import InvoiceUploadApi
from data.receive import _RECEIVE_INVOICE_UPLOAD_CFG
from utils.generate import generate_invoice_no


def record_invoice_upload(
    bl_no: str,
    receive_invoice_batch_id: str = None,
    file_id: str = None,
    file_name: str = None,
    file_url: str = None,
    original_name: str = None,
    invoice_amount: str = None,
    invoice_number: str = None,
    buyer_chinese_header: str = None,
    buyer_identifier_no: str = None,
    seller_chinese_header: str = None,
    seller_identifier_no: str = None,
    fee_file_info: Dict[str, Any] = None,
    invoice_file_path: str = None,
) -> Dict[str, Any]:
    """
    发票上传与登记

    流程：uploadFile（Step 0）→ invoiceAdd（Step 1）→ applyPage（Step 2）→ allocationInvoiceFee（Step 3）

    Args:
        bl_no                    : 提单号
        receive_invoice_batch_id : 开票批次ID（来自 record_invoice_batch，可选）
        file_id                  : 发票文件ID（已废弃，推荐用 invoice_file_path）
        file_name                : 发票文件名（已废弃，推荐用 invoice_file_path）
        file_url                 : 发票文件URL（已废弃，推荐用 invoice_file_path）
        original_name            : 原始文件名（已废弃，推荐用 invoice_file_path）
        invoice_amount           : 发票金额
        invoice_number           : 发票号码（自动生成唯一值）
        buyer_chinese_header    : 购买方名称
        buyer_identifier_no     : 购买方税号
        seller_chinese_header   : 销售方名称
        seller_identifier_no    : 销售方税号
        fee_file_info           : 费用通知单的文件信息 dict（file_id/file_name/file_url/original_name）
        invoice_file_path        : 本地发票文件路径，传入则自动执行 Step 0 上传并提取 file 信息

    Returns:
        {
            'add_resp' / 'add_data' / 'receive_invoice_id' / 'invoice_number': ...,
            'apply_page_resp' / 'apply_page_data' / 'receive_invoice_apply_id': ...,
            'alloc_resp' / 'alloc_data': ...,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {"bl_no": bl_no, "steps": []}

    # Step 0: uploadFile - 上传发票文件，获取真实的 file 信息
    uploaded_file_info: Dict[str, Any] = {}
    if invoice_file_path:
        with allure.step('上传发票文件（uploadFile）'):
            upload_resp = InvoiceUploadApi.upload_file(file_path=invoice_file_path)
            upload_data = upload_resp.json()
            result['upload_resp'] = upload_resp
            result['upload_data'] = upload_data
            uploaded_file_info = upload_data.get("data", {}) or {}
            result['uploaded_file_info'] = uploaded_file_info
            result['steps'].append({
                'name': '上传发票文件',
                'code': upload_data.get('code'),
                'msg': upload_data.get('msg'),
                'file_id': uploaded_file_info.get('file_id'),
                'file_name': uploaded_file_info.get('file_name'),
                'file_url': uploaded_file_info.get('file_url'),
                'file_type': uploaded_file_info.get('file_type'),
                'original_name': uploaded_file_info.get('original_name'),
            })
            if not uploaded_file_info.get('file_id'):
                raise AssertionError(f'uploadFile 响应中未找到 file_id: {upload_data}')

    # 从 YAML 读取默认值
    cfg = _RECEIVE_INVOICE_UPLOAD_CFG or {}
    buyer_cfg = cfg.get("buyer", {})
    seller_cfg = cfg.get("seller", {})
    file_cfg = cfg.get("invoice_file", {})
    buyer_chinese_header = buyer_chinese_header or buyer_cfg.get("chinese_header", "")
    buyer_identifier_no = buyer_identifier_no or buyer_cfg.get("identifier_no", "")
    seller_chinese_header = seller_chinese_header or seller_cfg.get("chinese_header", "")
    seller_identifier_no = seller_identifier_no or seller_cfg.get("identifier_no", "")
    # 填充文件字段：Step 0 最高 > fee_file_info > 显式参数 > file_cfg
    if uploaded_file_info:
        file_id = uploaded_file_info.get('file_id', '') or "9999999999"
        file_name = uploaded_file_info.get('file_name', '') or ""
        file_url = uploaded_file_info.get('file_url', '') or ""
        original_name = uploaded_file_info.get('original_name', '') or ""
    elif fee_file_info:
        file_id = file_id or fee_file_info.get('file_id', '') or "9999999999"
        file_name = file_name or fee_file_info.get('file_name', '') or ""
        file_url = file_url or fee_file_info.get('file_url', '') or ""
        original_name = original_name or fee_file_info.get('original_name', '') or ""
    else:
        file_id = file_id or file_cfg.get("file_id", "") or "9999999999"
        file_name = file_name or file_cfg.get("file_name", "") or ""
        file_url = file_url or file_cfg.get("file_url", "") or ""
        original_name = original_name or file_cfg.get("original_name", "") or ""

    # Step 1: invoiceAdd - 上传应收发票
    if invoice_number is None:
        invoice_number = generate_invoice_no("AR")
    if invoice_amount is None:
        invoice_amount = cfg.get("_constants", {}).get("invoice_amount", "1500")

    invoice_original = {
        "file_id": file_id,
        "file_name": file_name,
        "file_type": "pdf",
        "original_name": original_name,
        "file_url": file_url,
    }

    with allure.step('上传应收发票（invoiceAdd）'):
        add_resp = InvoiceUploadApi.invoice_add(
            invoice_number=invoice_number,
            invoice_amount=invoice_amount,
            invoice_original=invoice_original,
            buyer_chinese_header=buyer_chinese_header,
            buyer_identifier_no=buyer_identifier_no,
            seller_chinese_header=seller_chinese_header,
            seller_identifier_no=seller_identifier_no,
            invoice_image_name=file_name or "",
            file_path=file_url or "",
        )
        add_data = add_resp.json()
        result['add_resp'] = add_resp
        result['add_data'] = add_data
        result['invoice_number'] = invoice_number

        add_data_records = add_data.get("data", {}) or {}
        receive_invoice_id = add_data_records.get(invoice_number, "")
        result['receive_invoice_id'] = receive_invoice_id
        result['steps'].append({
            'name': '上传应收发票',
            'code': add_data.get('code'),
            'msg': add_data.get('msg'),
            'invoice_number': invoice_number,
            'receive_invoice_id': receive_invoice_id,
        })

        if not receive_invoice_id:
            raise AssertionError(f'invoiceAdd 响应中未找到 receive_invoice_id: {add_data}')

    # Step 2: applyPage - 按提单号查询发票申请ID
    with allure.step('获取发票申请ID（applyPage）'):
        apply_page_resp = InvoiceUploadApi.apply_page(bl_no=bl_no)
        apply_page_data = apply_page_resp.json()
        result['apply_page_resp'] = apply_page_resp
        result['apply_page_data'] = apply_page_data

        records = apply_page_data.get("data", {}).get("data", []) or []
        first = records[0] if records else {}
        receive_invoice_apply_id = first.get("receive_invoice_apply_id", "")
        result['receive_invoice_apply_id'] = receive_invoice_apply_id
        result['steps'].append({
            'name': '获取发票申请ID',
            'code': apply_page_data.get('code'),
            'msg': apply_page_data.get('msg'),
            'receive_invoice_apply_id': receive_invoice_apply_id,
            'record_count': len(records),
        })

        if not receive_invoice_apply_id:
            raise AssertionError(f'applyPage 响应中未找到 receive_invoice_apply_id: {apply_page_data}')

    # Step 3: allocationInvoiceFee - 登记发票到申请
    with allure.step('登记发票到申请（allocationInvoiceFee）'):
        # un_amount 来自 applyPage 第一条记录的 invoice_unused_amount
        un_amount = first.get("invoice_unused_amount") or first.get("turn_cost_cny") or invoice_amount
        invoice_arr = [{
            "receive_invoice_id": str(receive_invoice_id),
            "invoice_amount_use": str(un_amount),
        }]
        alloc_resp = InvoiceUploadApi.allocation_invoice_fee(
            receive_invoice_apply_id=receive_invoice_apply_id,
            invoice_arr=invoice_arr,
        )
        alloc_data = alloc_resp.json()
        result['alloc_resp'] = alloc_resp
        result['alloc_data'] = alloc_data
        result['steps'].append({
            'name': '登记发票到申请',
            'code': alloc_data.get('code'),
            'msg': alloc_data.get('msg'),
            'receive_invoice_apply_id': receive_invoice_apply_id,
        })

    # Step 3.5: 等待服务端把 receive_invoice_id 关联到 fee 行（invoice_status 1）
    # 后端异步处理需要几秒时间，writeoffBatch 依赖 fee.invoice_status = "1"
    from api.receive.receive_writeoff_api import ReceiveWriteoffApi as _RWA
    for _attempt in range(1, 6):
        _time.sleep(2)
        _fee_resp = _RWA.query_order_fee_real_id_list(bl_no=bl_no)
        _fee_data = _fee_resp.json().get("data", {}).get("data", []) or []
        _all_invoiced = bool(_fee_data) and all(
            str((f.get("invoice_status") or "")) in ("1", "2") and (f.get("invoice_ids") or "")
            for f in _fee_data
        )
        if _all_invoiced:
            result['fee_status_after_upload'] = {
                'attempt': _attempt,
                'invoice_ids': [f.get("invoice_ids") for f in _fee_data],
            }
            break
    else:
        result['fee_status_after_upload'] = {
            'attempt': 5,
            'pending': [f.get("order_fee_real_id") for f in _fee_data],
        }
        raise AssertionError(
            f'登记发票后 5 次轮询（每次 2s）fee.invoice_status 仍非已开票，无法继续核销: '
            f'{[{"order_fee_real_id": f.get("order_fee_real_id"), "invoice_status": f.get("invoice_status"), "invoice_ids": f.get("invoice_ids")} for f in _fee_data]}'
        )

    return result
