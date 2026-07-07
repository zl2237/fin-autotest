"""
Workflows 层 - 应付发票上传与登记步骤（LK22）

  record_payable_invoice_upload
      uploadFile → invoiceAdd → applyPage → allocationInvoiceFee

LK22 = LK21 + 应付发票上传与登记。
"""
from typing import Any, Dict, List

import allure

from api.pay.pay_invoice_register_api import PayInvoiceRegisterApi
from data.pay import PayableInvoiceUploadData, _UPLOAD_CFG
from utils.generate import generate_invoice_no


def record_payable_invoice_upload(
    bl_no: str,
    invoice_number: str = None,
    invoice_amount: str = None,
    buyer_chinese_header: str = None,
    buyer_identifier_no: str = None,
    seller_chinese_header: str = None,
    seller_identifier_no: str = None,
) -> Dict[str, Any]:
    """
    应付发票上传与登记（LK22）

    流程：uploadFile（Step 1）→ invoiceAdd（Step 2）→ applyPage（Step 3）→ allocationInvoiceFee（Step 4）

    Step 1 uploadFile：从 YAML 配置读取发票文件名，自动拼接完整路径上传，
                       响应含 file_id/file_name/file_url 供 Step 2 使用。

    Step 2 invoiceAdd：使用 Step 1 响应 + 上游 link21 响应数据构造发票登记请求体，
                        invoice_number 必须唯一（调用方生成或自动生成）。

    Step 3 applyPage：按 bl_nos 查询应付开票申请ID，提取 pay_invoice_apply_id。

    Step 4 allocationInvoiceFee：pay_invoice_id 来自 Step 2，pay_invoice_apply_id 来自 Step 3。

    Args:
        bl_no                  : 提单号（链路中传递）
        invoice_number         : 发票号码（可选，默认自动生成唯一值）
        invoice_amount        : 发票金额（默认从 YAML 读取）
        buyer_chinese_header  : 购买方名称（默认从 YAML 读取）
        buyer_identifier_no   : 购买方税号（默认从 YAML 读取）
        seller_chinese_header : 销售方名称（默认从 YAML 读取）
        seller_identifier_no  : 销售方税号（默认从 YAML 读取）

    Returns:
        {
            'bl_no': str,
            'upload_resp' / 'upload_data' / 'uploaded_file_info': ...,
            'add_resp' / 'add_data' / 'pay_invoice_id' / 'invoice_number': ...,
            'apply_page_resp' / 'apply_page_data' / 'pay_invoice_apply_id': ...,
            'alloc_resp' / 'alloc_data': ...,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {"bl_no": bl_no, "steps": []}

    # Step 1: uploadFile - 上传发票文件
    with allure.step('上传应付发票文件（uploadFile）'):
        invoice_file_path = PayableInvoiceUploadData.get_invoice_file_path()
        upload_resp = PayInvoiceRegisterApi.upload_pay_invoice_file(file_path=invoice_file_path)
        upload_data = upload_resp.json()
        result['upload_resp'] = upload_resp
        result['upload_data'] = upload_data
        uploaded_file_info = upload_data.get("data", {}) or {}
        result['uploaded_file_info'] = uploaded_file_info
        result['steps'].append({
            'name': '上传应付发票文件',
            'code': upload_data.get('code'),
            'msg': upload_data.get('msg'),
            'file_id': uploaded_file_info.get('file_id'),
            'file_name': uploaded_file_info.get('file_name'),
            'file_url': uploaded_file_info.get('file_url'),
            'file_type': uploaded_file_info.get('file_type'),
            'original_name': uploaded_file_info.get('original_name'),
        })

        assert upload_resp.status_code == 200, (
            f'uploadFile HTTP 状态码异常: {upload_resp.status_code}'
        )
        assert upload_data.get('code') == 200, (
            f'uploadFile 失败: {upload_data}'
        )
        if not uploaded_file_info.get('file_id'):
            raise AssertionError(f'uploadFile 响应中未找到 file_id: {upload_data}')

    # Step 2: invoiceAdd - 登记应付发票
    if invoice_number is None:
        invoice_number = generate_invoice_no("AP")
    if invoice_amount is None:
        invoice_amount = _UPLOAD_CFG.get("_constants", {}).get("invoice_amount", "1260")

    with allure.step('登记应付发票（invoiceAdd）'):
        add_resp = PayInvoiceRegisterApi.invoice_add(
            file_id=uploaded_file_info.get('file_id', ''),
            file_name=uploaded_file_info.get('file_name', ''),
            file_url=uploaded_file_info.get('file_url', ''),
            original_name=uploaded_file_info.get('original_name', ''),
            invoice_number=invoice_number,
            invoice_amount=invoice_amount,
            buyer_chinese_header=buyer_chinese_header,
            buyer_identifier_no=buyer_identifier_no,
            seller_chinese_header=seller_chinese_header,
            seller_identifier_no=seller_identifier_no,
        )
        add_data = add_resp.json()
        result['add_resp'] = add_resp
        result['add_data'] = add_data
        result['invoice_number'] = invoice_number

        add_data_inner = add_data.get("data", {}) or {}
        # 响应格式：data = {invoice_number: pay_invoice_id}
        pay_invoice_id = str(
            add_data_inner.get(invoice_number)
            or ""
        )
        result['pay_invoice_id'] = pay_invoice_id

        result['steps'].append({
            'name': '登记应付发票',
            'code': add_data.get('code'),
            'msg': add_data.get('msg'),
            'invoice_number': invoice_number,
            'pay_invoice_id': pay_invoice_id,
        })

        assert add_resp.status_code == 200, (
            f'invoiceAdd HTTP 状态码异常: {add_resp.status_code}'
        )
        assert add_data.get('code') == 200, (
            f'invoiceAdd 失败: {add_data}'
        )
        if not pay_invoice_id:
            raise AssertionError(f'invoiceAdd 响应中未找到 pay_invoice_id: {add_data}')

    # Step 3: applyPage - 按 bl_nos 查询应付开票申请ID
    with allure.step('查询应付开票申请ID（applyPage）'):
        apply_resp = PayInvoiceRegisterApi.apply_page(bl_nos=[bl_no])
        apply_data = apply_resp.json()
        result['apply_page_resp'] = apply_resp
        result['apply_page_data'] = apply_data

        records = apply_data.get("data", {}).get("data", []) or []
        first_record = records[0] if records else {}
        pay_invoice_apply_id = str(
            first_record.get("pay_invoice_apply_id") or ""
        )
        # 从 applyPage 记录中取未分配金额，供 Step 4 使用
        un_amount = (
            first_record.get("invoice_unused_amount")
            or first_record.get("un_writeoff_amount")
            or invoice_amount
        )
        result['pay_invoice_apply_id'] = pay_invoice_apply_id
        result['un_amount'] = un_amount

        result['steps'].append({
            'name': '查询应付开票申请ID',
            'code': apply_data.get('code'),
            'msg': apply_data.get('msg'),
            'pay_invoice_apply_id': pay_invoice_apply_id,
            'un_amount': un_amount,
            'record_count': len(records),
        })

        assert apply_resp.status_code == 200, (
            f'applyPage HTTP 状态码异常: {apply_resp.status_code}'
        )
        assert apply_data.get('code') == 200, (
            f'applyPage 失败: {apply_data}'
        )
        if not pay_invoice_apply_id:
            raise AssertionError(f'applyPage 响应中未找到 pay_invoice_apply_id: {apply_data}')

    # Step 4: allocationInvoiceFee - 分配发票到费用
    # pay_invoice_id 来自 Step 2，pay_invoice_apply_id / un_amount 来自 Step 3
    with allure.step('分配发票到费用（allocationInvoiceFee）'):
        alloc_resp = PayInvoiceRegisterApi.allocation_invoice_fee(
            pay_invoice_apply_id=pay_invoice_apply_id,
            pay_invoice_id=pay_invoice_id,
            un_amount=str(un_amount),
        )
        alloc_data = alloc_resp.json()
        result['alloc_resp'] = alloc_resp
        result['alloc_data'] = alloc_data
        result['steps'].append({
            'name': '分配发票到费用',
            'code': alloc_data.get('code'),
            'msg': alloc_data.get('msg'),
            'pay_invoice_id': pay_invoice_id,
            'un_amount': un_amount,
        })

        assert alloc_resp.status_code == 200, (
            f'allocationInvoiceFee HTTP 状态码异常: {alloc_resp.status_code}'
        )
        assert alloc_data.get('code') == 200, (
            f'allocationInvoiceFee 失败: {alloc_data}'
        )

    return result
