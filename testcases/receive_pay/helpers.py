"""
链路测试 - receive_pay 流程公共辅助函数

适用于 order_receive_pay1 ~ order_receive_pay13 的共享断言逻辑。
"""
from data.order import BookRealAmountData


def _build_fee_config():
    return {
        'to_customer_fees': BookRealAmountData.get_customer_standard_fees(),
        'to_supplier_fees': BookRealAmountData.get_supplier_standard_fees(),
    }


def _assert_link12_prerequisite_ok(result):
    """
    order_receive_pay1 的前置链路（order1~12）断言：
    - 新建 / 分发 / 生成子订单 / 录费用 / 审批 / 费用单 / 费用确认单
    所有前置步骤必须通过。
    """
    assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'
    assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'
    gen_data = result['generate_sub_data']
    assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'
    assert len(result['record_fee_results']) == 1
    fee_1 = result['record_fee_results'][0]
    assert fee_1['resp'].status_code == 200
    assert fee_1['data']['code'] == 200
    assert fee_1.get('audit_send_resp') is not None
    assert fee_1['audit_send_resp'].status_code == 200
    assert fee_1['audit_send_data']['code'] == 200
    assert fee_1.get('audit_id')
    assert fee_1['audit_approve_resp'].status_code == 200
    assert fee_1['audit_approve_data']['code'] == 200

    lock_result = result['order_lock_result']
    assert lock_result is not None
    assert lock_result['send_resp'].status_code == 200
    assert lock_result['send_data']['code'] == 200
    assert lock_result.get('audit_id')
    assert lock_result['approve_resp'].status_code == 200
    assert lock_result['approve_data']['code'] == 200

    invoice_result = result['invoice_apply_result']
    assert invoice_result is not None
    assert invoice_result['send_resp'].status_code == 200
    assert invoice_result['send_data'].get('code') == 200
    assert invoice_result.get('audit_id')
    assert invoice_result['approve_resp'].status_code == 200
    assert invoice_result['approve_data']['code'] == 200

    advance_result = result['supplier_advance_result']
    assert advance_result is not None
    assert advance_result['send_resp'].status_code == 200
    assert advance_result['send_data'].get('code') == 200
    assert advance_result.get('audit_id')
    assert advance_result['approve_resp'].status_code == 200
    assert advance_result['approve_data']['code'] == 200

    notice_result = result['fee_notice_result']
    assert notice_result is not None
    assert notice_result['resp'].status_code == 200
    assert notice_result['data']['code'] == 200

    fee_confirm_result = result['fee_confirm_result']
    assert fee_confirm_result is not None
    assert fee_confirm_result['resp'].status_code == 200
    assert fee_confirm_result['data']['code'] == 200


def _assert_audit_and_fee_doc_ok(result):
    """order_receive_pay10~13 共用"录费用+审批+费用单据"链式断言。"""
    assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'
    assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'
    gen_data = result['generate_sub_data']
    assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'
    assert len(result['record_fee_results']) == 1
    fee_1 = result['record_fee_results'][0]
    assert fee_1['resp'].status_code == 200
    assert fee_1['data']['code'] == 200
    assert fee_1.get('audit_send_resp') is not None
    assert fee_1['audit_send_resp'].status_code == 200
    assert fee_1['audit_send_data']['code'] == 200
    assert fee_1.get('audit_id')
    assert fee_1['audit_approve_resp'].status_code == 200
    assert fee_1['audit_approve_data']['code'] == 200

    lock_result = result['order_lock_result']
    assert lock_result is not None
    assert lock_result['container']
    assert lock_result['send_resp'].status_code == 200
    assert lock_result['send_data']['code'] == 200
    assert lock_result.get('audit_id')
    assert lock_result['approve_resp'].status_code == 200
    assert lock_result['approve_data']['code'] == 200

    invoice_result = result['invoice_apply_result']
    assert invoice_result is not None
    assert invoice_result['send_resp'].status_code == 200
    assert invoice_result['send_data'].get('code') == 200
    assert invoice_result.get('audit_id')
    assert invoice_result['approve_resp'].status_code == 200
    assert invoice_result['approve_data']['code'] == 200

    advance_result = result['supplier_advance_result']
    assert advance_result is not None
    assert advance_result['send_resp'].status_code == 200
    assert advance_result['send_data'].get('code') == 200
    assert advance_result.get('audit_id')
    assert advance_result['approve_resp'].status_code == 200
    assert advance_result['approve_data']['code'] == 200

    notice_result = result['fee_notice_result']
    assert notice_result is not None
    assert notice_result['resp'].status_code == 200
    assert notice_result['data']['code'] == 200

    confirm_result = result['fee_confirm_result']
    assert confirm_result is not None
    assert confirm_result['resp'].status_code == 200
    assert confirm_result['data']['code'] == 200


def _assert_receive_account_ok(result):
    """
    order_receive_pay1 发起应收对账批次断言：financePutList + receiveAccountEdit 全部成功。
    """
    receive_result = result['receive_account_result']
    assert receive_result is not None, 'receive_account_result 不应为空'

    put_list_resp = receive_result['put_list_resp']
    put_list_data = receive_result['put_list_data']
    assert put_list_resp.status_code == 200, f'financePutList HTTP 状态码异常: {put_list_resp.status_code}'
    assert put_list_data.get('code') == 200, f'financePutList 失败: {put_list_data}'
    assert put_list_data.get('msg') == '成功', f'financePutList msg 不为"成功": {put_list_data.get("msg")}'

    select_list = receive_result['select_list']
    assert select_list, f'select_list 不应为空: {put_list_data}'

    submit_resp = receive_result['submit_resp']
    submit_data = receive_result['submit_data']
    assert submit_resp.status_code == 200, f'receiveAccountEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'receiveAccountEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'receiveAccountEdit msg 不为"成功": {submit_data.get("msg")}'

    assert receive_result.get('receive_account_id'), f'receive_account_id 不应为空: {receive_result}'
    assert receive_result.get('receive_account_no').startswith('YSDZPC'), f'receive_account_no 应以 YSDZPC 开头: {receive_result.get("receive_account_no")}'


def _assert_confirm_receive_ok(result):
    """
    order_receive_pay2 确认应收对账断言：receiveAccountDetail + receiveConfirmList + accountConfirm 全部成功。
    """
    confirm_result = result['confirm_account_result']
    assert confirm_result is not None, 'confirm_account_result 不应为空'

    detail_resp = confirm_result['detail_resp']
    detail_data = confirm_result['detail_data']
    assert detail_resp.status_code == 200, f'receiveAccountDetail HTTP 状态码异常: {detail_resp.status_code}'
    assert detail_data.get('code') == 200, f'receiveAccountDetail 失败: {detail_data}'
    assert detail_data.get('msg') == '成功', f'receiveAccountDetail msg 不为"成功": {detail_data.get("msg")}'

    confirm_list_resp = confirm_result['confirm_list_resp']
    confirm_list_data = confirm_result['confirm_list_data']
    assert confirm_list_resp.status_code == 200, f'receiveConfirmList HTTP 状态码异常: {confirm_list_resp.status_code}'
    assert confirm_list_data.get('code') == 200, f'receiveConfirmList 失败: {confirm_list_data}'
    assert confirm_list_data.get('msg') == '成功', f'receiveConfirmList msg 不为"成功": {confirm_list_data.get("msg")}'

    confirm_list = confirm_result.get('confirm_list', [])
    assert confirm_list, f'confirm_list 不应为空: {confirm_list_data}'

    submit_resp = confirm_result['submit_resp']
    submit_data = confirm_result['submit_data']
    assert submit_resp.status_code == 200, f'accountConfirm HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'accountConfirm 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {submit_data.get("msg")}'


def _assert_receive_invoice_apply_ok(result):
    """
    order_receive_pay3 发起应收开票批次申请断言：financePutList（开票）+ getOrderInfoByFeeId + batchOrderEdit 全部成功。
    """
    invoice_result = result.get('receive_invoice_apply_result') or result.get('invoice_batch_result')
    assert invoice_result is not None, 'receive_invoice_apply_result/invoice_batch_result 不应为空'

    put_list_resp = invoice_result['put_list_resp']
    put_list_data = invoice_result['put_list_data']
    assert put_list_resp.status_code == 200, f'financePutList（开票）HTTP 状态码异常: {put_list_resp.status_code}'
    assert put_list_data.get('code') == 200, f'financePutList（开票）失败: {put_list_data}'
    assert put_list_data.get('msg') == '成功', f'financePutList（开票）msg 不为"成功": {put_list_data.get("msg")}'

    main_id = (
        invoice_result.get('main_id')
        or (put_list_data.get('data') or {}).get('main_id')
        or result.get('after_submit_order', {}).get('main_id')
    )
    assert main_id, f'main_id 不应为空: invoice_result={invoice_result}, put_list_data={put_list_data}'
    order_info_records = (
        invoice_result.get('order_info_records')
        or (put_list_data.get('data', {}).get('data', []) or [])[0].get('amount_list', [])
        or []
    )
    assert order_info_records, f'order_info_records 不应为空: invoice_result={invoice_result}, put_list_data={put_list_data}'
    for rec in order_info_records:
        assert rec.get('order_fee_real_id'), f'record 中 order_fee_real_id 不应为空: {rec}'

    submit_resp = invoice_result['invoice_submit_resp']
    submit_data = invoice_result['invoice_submit_data']
    assert submit_resp.status_code == 200, f'batchOrderEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'batchOrderEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'batchOrderEdit msg 不为"成功": {submit_data.get("msg")}'


def _assert_receive_invoice_register_ok(result):
    """
    order_receive_pay4 应收发票上传与登记断言。
    """
    upload_result = result.get('receive_invoice_register_result') or result.get('invoice_upload_result')
    assert upload_result is not None, 'receive_invoice_register_result/invoice_upload_result 不应为空'

    upload_resp = upload_result['upload_resp']
    upload_data = upload_result['upload_data']
    assert upload_resp.status_code == 200, f'uploadFile HTTP 状态码异常: {upload_resp.status_code}'
    assert upload_data.get('code') == 200, f'uploadFile code 不为 200: {upload_data}'
    assert upload_result.get('uploaded_file_info', {}).get('file_id'), f'uploadFile 未返回 file_id: {upload_result}'

    add_resp = upload_result['add_resp']
    add_data = upload_result['add_data']
    assert add_resp.status_code == 200, f'invoiceAdd HTTP 状态码异常: {add_resp.status_code}'
    assert add_data.get('code') == 200, f'invoiceAdd code 不为 200: {add_data}'
    assert upload_result.get('receive_invoice_id'), f'invoiceAdd 未返回 receive_invoice_id: {upload_result}'

    apply_resp = upload_result['apply_page_resp']
    apply_data = upload_result['apply_page_data']
    assert apply_resp.status_code == 200, f'applyPage HTTP 状态码异常: {apply_resp.status_code}'
    assert apply_data.get('code') == 200, f'applyPage code 不为 200: {apply_data}'
    assert upload_result.get('receive_invoice_apply_id'), f'applyPage 未返回 receive_invoice_apply_id: {upload_result}'

    alloc_resp = upload_result['alloc_resp']
    alloc_data = upload_result['alloc_data']
    assert alloc_resp.status_code == 200, f'allocationInvoiceFee HTTP 状态码异常: {alloc_resp.status_code}'
    assert alloc_data.get('code') == 200, f'allocationInvoiceFee code 不为 200: {alloc_data}'


def _assert_receive_invoice_batch_audit_ok(result):
    """
    order_receive_pay5 审核生成开票申请断言：invoiceBatchApplication 审批通过。
    """
    audit_result = result['invoice_batch_audit_result']
    assert audit_result is not None, 'invoice_batch_audit_result 不应为空'

    audit_query_resp = audit_result.get('audit_query_resp')
    audit_query_data = audit_result.get('audit_query_data') or {}
    if audit_query_resp is not None:
        assert audit_query_resp.status_code == 200, f'查询开票批次审批 HTTP 状态码异常: {audit_query_resp.status_code}'
    assert audit_query_data.get('code') == 200, f'查询开票批次审批失败: {audit_query_data}'

    assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'

    approve_results = audit_result.get('approve_results', [])
    assert approve_results, f'approve_results 不应为空: {audit_result}'

    first_approve = approve_results[0]
    approve_resp = first_approve['approve_resp']
    approve_data = first_approve['approve_data']
    assert approve_resp.status_code == 200, f'审批通过 HTTP 状态码异常: {approve_resp.status_code}'
    assert approve_data.get('code') == 200, f'审批通过失败: {approve_data}'


def _assert_receive_writeoff_ok(result):
    """
    order_receive_pay6 应收核销断言：feeTakePage + writeoffBatch 全部成功。
    """
    writeoff_result = result['receive_writeoff_result']
    assert writeoff_result is not None, 'receive_writeoff_result 不应为空'

    fee_take_page_resp = writeoff_result['fee_take_page_resp']
    fee_take_page_data = writeoff_result['fee_take_page_data']
    assert fee_take_page_resp.status_code == 200, f'feeTakePage HTTP 状态码异常: {fee_take_page_resp.status_code}'
    assert fee_take_page_data.get('code') == 200, f'feeTakePage 失败: {fee_take_page_data}'

    order_fee_real_id_list = writeoff_result.get('order_fee_real_id_list', [])
    assert order_fee_real_id_list, f'order_fee_real_id_list 不应为空: {writeoff_result}'

    writeoff_object = writeoff_result.get('writeoff_object', [])
    assert writeoff_object, f'writeoff_object 不应为空: {writeoff_result}'

    writeoff_batch_resp = writeoff_result['writeoff_batch_resp']
    writeoff_batch_data = writeoff_result['writeoff_batch_data']
    assert writeoff_batch_resp.status_code == 200, f'writeoffBatch HTTP 状态码异常: {writeoff_batch_resp.status_code}'
    assert writeoff_batch_data.get('code') == 200, f'writeoffBatch 失败: {writeoff_batch_data}'
    assert writeoff_batch_data.get('msg') == '成功', f'writeoffBatch msg 不为"成功": {writeoff_batch_data.get("msg")}'


def _assert_payable_account_ok(result):
    """
    order_receive_pay5 发起应付对账批次断言：financePayList + orderPayAccountEdit 全部成功。
    """
    payable_result = result['payable_account_result']
    assert payable_result is not None, 'payable_account_result 不应为空'

    pay_list_resp = payable_result['pay_list_resp']
    pay_list_data = payable_result['pay_list_data']
    assert pay_list_resp.status_code == 200, f'financePayList HTTP 状态码异常: {pay_list_resp.status_code}'
    assert pay_list_data.get('code') == 200, f'financePayList 失败: {pay_list_data}'
    assert pay_list_data.get('msg') == '成功', f'financePayList msg 不为"成功": {pay_list_data.get("msg")}'

    select_list = payable_result['select_list']
    assert select_list, f'select_list 不应为空: {pay_list_data}'

    submit_resp = payable_result['submit_resp']
    submit_data = payable_result['submit_data']
    assert submit_resp.status_code == 200, f'orderPayAccountEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'orderPayAccountEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'orderPayAccountEdit msg 不为"成功": {submit_data.get("msg")}'

    assert payable_result.get('pay_account_id'), f'pay_account_id 不应为空: {payable_result}'
    assert payable_result.get('pay_account_no'), f'pay_account_no 不应为空: {payable_result}'


def _assert_confirm_payable_ok(result):
    """
    order_receive_pay6 确认应付对账断言：payAccountPage + accountConfirm 全部成功。
    """
    confirm_result = result['confirm_payable_result']
    assert confirm_result is not None, 'confirm_payable_result 不应为空'

    page_resp = confirm_result['pay_account_page_resp']
    page_data = confirm_result['pay_account_page_data']
    assert page_resp.status_code == 200, f'payAccountPage HTTP 状态码异常: {page_resp.status_code}'
    assert page_data.get('code') == 200, f'payAccountPage 查询失败: {page_data}'
    assert page_data.get('msg') == '成功', f'payAccountPage msg 不为"成功": {page_data.get("msg")}'

    assert confirm_result.get('pay_account_id'), f'pay_account_id 不应为空: {confirm_result}'
    assert confirm_result.get('pay_account_no'), f'pay_account_no 不应为空: {confirm_result}'

    confirm_resp = confirm_result['confirm_resp']
    confirm_data = confirm_result['confirm_data']
    assert confirm_resp.status_code == 200, f'accountConfirm HTTP 状态码异常: {confirm_resp.status_code}'
    assert confirm_data.get('code') == 200, f'accountConfirm 失败: {confirm_data}'
    assert confirm_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {confirm_data.get("msg")}'


def _assert_pay_demand_ok(result):
    """
    order_receive_pay7 发起付款需求断言。
    """
    demand_result = result['pay_demand_result']
    assert demand_result is not None, 'pay_demand_result 不应为空'

    pay_list_resp = demand_result['pay_list_resp']
    pay_list_data = demand_result['pay_list_data']
    assert pay_list_resp.status_code == 200, f'financePayList HTTP 状态码异常: {pay_list_resp.status_code}'
    assert pay_list_data.get('code') == 200, f'financePayList 查询失败: {pay_list_data}'
    assert pay_list_data.get('msg') == '成功', f'financePayList msg 不为"成功": {pay_list_data.get("msg")}'

    select_list = demand_result.get('select_list', [])
    assert select_list, f'select_list 不应为空: {pay_list_data}'

    cost_usd = demand_result.get('cost_usd')
    cost_cny = demand_result.get('cost_cny')
    assert cost_usd, f'cost_usd 不应为空: {demand_result}'
    assert cost_cny is not None, f'cost_cny 不应为空: {demand_result}'
    assert float(cost_usd) > 0, f'cost_usd 应大于 0: {cost_usd}'

    payment_resp = demand_result['payment_list_resp']
    payment_data = demand_result['payment_list_data']
    assert payment_resp.status_code == 200, f'paymentList HTTP 状态码异常: {payment_resp.status_code}'
    assert payment_data.get('code') == 200, f'paymentList 失败: {payment_data}'

    payment_list = demand_result.get('payment_list', [])
    assert payment_list, f'payment_list 不应为空: {payment_data}'

    submit_resp = demand_result['submit_resp']
    submit_data = demand_result['submit_data']
    assert submit_resp.status_code == 200, f'demandEditByOrder HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'demandEditByOrder 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'demandEditByOrder msg 不为"成功": {submit_data.get("msg")}'


def _assert_pay_demand_audit_ok(result):
    """
    order_receive_pay12 审核生成付款单断言。
    """
    audit_result = result['pay_demand_audit_result']
    assert audit_result is not None, 'pay_demand_audit_result 不应为空'

    audit_page_resp = audit_result['audit_page_resp']
    audit_page_data = audit_result['audit_page_data']
    assert audit_page_resp.status_code == 200, f'auditPage HTTP 状态码异常: {audit_page_resp.status_code}'
    assert audit_page_data.get('code') == 200, f'auditPage 查询失败: {audit_page_data}'

    audit_records = audit_result.get('audit_records', [])
    assert audit_records, f'audit_records 不应为空: {audit_page_data}'

    assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'
    assert audit_result.get('audit_type') == 'payDemand', f'audit_type 应为 payDemand: {audit_result.get("audit_type")}'

    approve_results = audit_result.get('approve_results', [])
    assert approve_results, f'approve_results 不应为空: {audit_result}'

    first_approve = approve_results[0]
    # invoice_batch_audit_result 同时有 approve_resp（来自 approve_results）和 audit_execute_resp（flatten 复制），
    # 优先用 approve_results 里的原始 key，保持与 _loop_approve_until_done 返回结构一致
    approve_resp = first_approve.get('approve_resp') or first_approve['audit_execute_resp']
    approve_data = first_approve.get('approve_data') or first_approve['audit_execute_data']
    assert approve_resp.status_code == 200, f'auditExecute HTTP 状态码异常: {approve_resp.status_code}'
    assert approve_data.get('code') == 200, f'auditExecute 失败: {approve_data}'


def _assert_pay_writeoff_ok(result):
    """
    order_receive_pay9 付款单核销断言。
    """
    writeoff_result = result['pay_writeoff_result']
    assert writeoff_result is not None, 'pay_writeoff_result 不应为空'

    form_page_resp = writeoff_result['form_page_resp']
    form_page_data = writeoff_result['form_page_data']
    assert form_page_resp.status_code == 200, f'formPage HTTP 状态码异常: {form_page_resp.status_code}'
    assert form_page_data.get('code') == 200, f'formPage 查询失败: {form_page_data}'

    pay_form_records = writeoff_result.get('pay_form_records', [])
    assert pay_form_records, f'pay_form_records 不应为空: {form_page_data}'
    assert writeoff_result.get('pay_form_id'), f'pay_form_id 不应为空: {writeoff_result}'

    writeoff_pay_form_list_resp = writeoff_result['writeoff_pay_form_list_resp']
    writeoff_pay_form_list_data = writeoff_result['writeoff_pay_form_list_data']
    assert writeoff_pay_form_list_resp.status_code == 200, f'writeoffPayFormList HTTP 状态码异常: {writeoff_pay_form_list_resp.status_code}'
    assert writeoff_pay_form_list_data.get('code') == 200, f'writeoffPayFormList 失败: {writeoff_pay_form_list_data}'

    order_fee_page_resp = writeoff_result['order_fee_page_resp']
    order_fee_page_data = writeoff_result['order_fee_page_data']
    assert order_fee_page_resp.status_code == 200, f'orderFeePage HTTP 状态码异常: {order_fee_page_resp.status_code}'
    assert order_fee_page_data.get('code') == 200, f'orderFeePage 失败: {order_fee_page_data}'

    writeoff_batch_resp = writeoff_result['writeoff_batch_resp']
    writeoff_batch_data = writeoff_result['writeoff_batch_data']
    assert writeoff_batch_resp.status_code == 200, f'writeoffBatch HTTP 状态码异常: {writeoff_batch_resp.status_code}'
    assert writeoff_batch_data.get('code') == 200, f'writeoffBatch 失败: {writeoff_batch_data}'


def _assert_payable_invoice_apply_ok(result):
    """
    order_receive_pay9 发起应付开票批次申请断言：
    financePayList（开票） + getOrderInfoByFeeId + batchOrderEdit 全部成功。
    """
    invoice_result = result['payable_invoice_apply_result']
    assert invoice_result is not None, 'payable_invoice_apply_result 不应为空'

    pay_list_resp = invoice_result['pay_list_invoice_resp']
    pay_list_data = invoice_result['pay_list_invoice_data']
    assert pay_list_resp.status_code == 200, f'financePayList（开票）HTTP 状态码异常: {pay_list_resp.status_code}'
    assert pay_list_data.get('code') == 200, f'financePayList（开票）失败: {pay_list_data}'
    assert pay_list_data.get('msg') == '成功', f'financePayList（开票）msg 不为"成功": {pay_list_data.get("msg")}'

    order_info_resp = invoice_result['order_info_resp']
    order_info_data = invoice_result['order_info_data']
    assert order_info_resp.status_code == 200, f'getOrderInfoByFeeId HTTP 状态码异常: {order_info_resp.status_code}'
    assert order_info_data.get('code') == 200, f'getOrderInfoByFeeId 失败: {order_info_data}'
    assert order_info_data.get('msg') == '成功', f'getOrderInfoByFeeId msg 不为"成功": {order_info_data.get("msg")}'

    order_info_records = invoice_result['order_info_records']
    assert order_info_records, f'order_info_records 不应为空: {order_info_data}'

    submit_resp = invoice_result['submit_resp']
    submit_data = invoice_result['submit_data']
    assert submit_resp.status_code == 200, f'batchOrderEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'batchOrderEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'batchOrderEdit msg 不为"成功": {submit_data.get("msg")}'

    assert invoice_result.get('main_id'), f'main_id 不应为空: {invoice_result}'
    assert invoice_result.get('pay_settle_object'), f'pay_settle_object 不应为空'
    assert invoice_result.get('cost_usd'), f'cost_usd 不应为空'


def _assert_payable_invoice_register_ok(result):
    """
    order_receive_pay10 应付发票上传与登记断言：
    uploadFile + invoiceAdd + applyPage + allocationInvoiceFee 全部成功。
    """
    upload_result = result['payable_invoice_register_result']
    assert upload_result is not None, 'payable_invoice_register_result 不应为空'

    upload_resp = upload_result['upload_resp']
    upload_data = upload_result['upload_data']
    assert upload_resp.status_code == 200, f'uploadFile HTTP 状态码异常: {upload_resp.status_code}'
    assert upload_data.get('code') == 200, f'uploadFile 失败: {upload_data}'
    uploaded_file_info = upload_result.get('uploaded_file_info', {})
    assert uploaded_file_info.get('file_id'), f'uploadFile 未返回 file_id: {upload_result}'

    add_resp = upload_result['add_resp']
    add_data = upload_result['add_data']
    assert add_resp.status_code == 200, f'invoiceAdd HTTP 状态码异常: {add_resp.status_code}'
    assert add_data.get('code') == 200, f'invoiceAdd 失败: {add_data}'
    assert upload_result.get('pay_invoice_id'), f'invoiceAdd 未返回 pay_invoice_id: {upload_result}'

    apply_resp = upload_result['apply_page_resp']
    apply_data = upload_result['apply_page_data']
    assert apply_resp.status_code == 200, f'applyPage HTTP 状态码异常: {apply_resp.status_code}'
    assert apply_data.get('code') == 200, f'applyPage 失败: {apply_data}'
    assert upload_result.get('pay_invoice_apply_id'), f'applyPage 未返回 pay_invoice_apply_id: {upload_result}'

    alloc_resp = upload_result['alloc_resp']
    alloc_data = upload_result['alloc_data']
    assert alloc_resp.status_code == 200, f'allocationInvoiceFee HTTP 状态码异常: {alloc_resp.status_code}'
    assert alloc_data.get('code') == 200, f'allocationInvoiceFee 失败: {alloc_data}'
