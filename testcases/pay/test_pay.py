"""
链路测试 - 应付对账（link19 / link20 / link21 / link22 / link23 / link24 / link25）

  link19 - 发起应付对账批次（link18 + financePayList + orderPayAccountEdit）
  link20 - 确认应付对账（link19 + payAccountPage + accountConfirm）
  link21 - 发起应付开票批次申请（link20 + financePayList(开票) + getOrderInfoByFeeId + batchOrderEdit submit）
  link22 - 应付发票上传与登记（link21 + uploadFile + invoiceAdd + applyPage + allocationInvoiceFee）
  link23 - 发起付款需求（link22 + financePayList + paymentList + demandEditByOrder）
  link24 - 审核生成付款单（link23 + auditPage + auditExecute）
  link25 - 付款单核销（link24 + formPage + writeoffPayFormList + orderFeePage + writeoffBatch）
"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from data.order import BookRealAmountData, generate_bl_no


def _build_fee_config():
    return {
        'to_customer_fees': BookRealAmountData.get_customer_standard_fees(),
        'to_supplier_fees': BookRealAmountData.get_supplier_standard_fees(),
    }


def _assert_link18_prerequisite_ok(result):
    """
    link19 的前置链路（link18）断言：
    - 新建 / 分发 / 生成子订单 / 录费用 / 审批 / 费用单 / 应收对账 / 发票 / 应收核销
    所有前置步骤必须通过。
    """
    assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'
    assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'
    gen_data = result['generate_sub_data']
    assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

    # 录费用
    assert len(result['record_fee_results']) == 1
    fee_1 = result['record_fee_results'][0]
    assert fee_1['resp'].status_code == 200
    assert fee_1['data']['code'] == 200

    # 资产推送审批
    assert fee_1.get('audit_send_resp') is not None
    assert fee_1['audit_send_resp'].status_code == 200
    assert fee_1['audit_send_data']['code'] == 200
    assert fee_1.get('audit_id')
    assert fee_1['audit_approve_resp'].status_code == 200
    assert fee_1['audit_approve_data']['code'] == 200

    # 订单锁定审批
    lock_result = result['order_lock_result']
    assert lock_result is not None
    assert lock_result['send_resp'].status_code == 200
    assert lock_result['send_data']['code'] == 200
    assert lock_result.get('audit_id')
    assert lock_result['approve_resp'].status_code == 200
    assert lock_result['approve_data']['code'] == 200

    # 未放款开票申请审批
    invoice_result = result['invoice_apply_result']
    assert invoice_result is not None
    assert invoice_result['send_resp'].status_code == 200
    assert invoice_result['send_data']['code'] == 200
    assert invoice_result.get('audit_id')
    assert invoice_result['approve_resp'].status_code == 200
    assert invoice_result['approve_data']['code'] == 200

    # 供应商垫付申请审批
    advance_result = result['supplier_advance_result']
    assert advance_result is not None
    assert advance_result['send_resp'].status_code == 200
    assert advance_result['send_data']['code'] == 200
    assert advance_result.get('audit_id')
    assert advance_result['approve_resp'].status_code == 200
    assert advance_result['approve_data']['code'] == 200

    # 费用通知单
    notice_result = result['fee_notice_result']
    assert notice_result is not None
    assert notice_result['resp'].status_code == 200
    assert notice_result['data']['code'] == 200

    # 费用确认单
    fee_confirm_result = result['fee_confirm_result']
    assert fee_confirm_result is not None
    assert fee_confirm_result['resp'].status_code == 200
    assert fee_confirm_result['data']['code'] == 200

    # 应收对账批次
    receive_result = result['receive_account_result']
    assert receive_result is not None
    assert receive_result['put_list_resp'].status_code == 200
    assert receive_result['put_list_data'].get('code') == 200
    assert receive_result['submit_resp'].status_code == 200
    assert receive_result['submit_data'].get('code') == 200
    assert receive_result['submit_data'].get('msg') == '成功'
    assert receive_result['receive_account_id']
    assert receive_result['receive_account_no'].startswith('YSDZPC')

    # 确认应收对账
    confirm_result = result['confirm_account_result']
    assert confirm_result is not None
    assert confirm_result['confirm_list_resp'].status_code == 200
    assert confirm_result['confirm_list_data'].get('code') == 200
    assert confirm_result['submit_resp'].status_code == 200
    assert confirm_result['submit_data'].get('code') == 200
    assert confirm_result['submit_data'].get('msg') == '成功'

    # 发票批次
    invoice_batch_result = result['invoice_batch_result']
    assert invoice_batch_result is not None
    assert invoice_batch_result['invoice_submit_resp'].status_code == 200
    assert invoice_batch_result['invoice_submit_data'].get('code') == 200

    # 发票批次审核
    audit_result = result['invoice_batch_audit_result']
    assert audit_result is not None
    assert audit_result['audit_query_resp'].status_code == 200
    assert audit_result.get('audit_id')
    assert audit_result['audit_execute_resp'].status_code == 200
    assert audit_result['audit_execute_data'].get('code') == 200

    # 发票上传与登记
    upload_result = result['invoice_upload_result']
    assert upload_result is not None
    assert upload_result['add_resp'].status_code == 200
    assert upload_result['add_data'].get('code') == 200
    assert upload_result.get('receive_invoice_id')
    assert upload_result['apply_page_resp'].status_code == 200
    assert upload_result['apply_page_data'].get('code') == 200
    assert upload_result.get('receive_invoice_apply_id')
    assert upload_result['alloc_resp'].status_code == 200
    assert upload_result['alloc_data'].get('code') == 200

    # 应收核销
    writeoff_result = result['receive_writeoff_result']
    assert writeoff_result is not None
    assert writeoff_result['fee_take_page_resp'].status_code == 200
    assert writeoff_result['fee_take_page_data'].get('code') == 200
    order_fee_real_id_list = writeoff_result.get('order_fee_real_id_list', [])
    assert order_fee_real_id_list, f'应收核销 order_fee_real_id_list 不应为空'
    assert writeoff_result['writeoff_batch_resp'].status_code == 200
    assert writeoff_result['writeoff_batch_data'].get('code') == 200


def _assert_payable_account_ok(result):
    """
    link19 应付对账断言：financePayList + orderPayAccountEdit 全部成功。
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

    amount_list_flat = payable_result.get('amount_list_flat', [])
    assert amount_list_flat, f'amount_list_flat 不应为空（financePayList 响应: {pay_list_data}）'
    for item in amount_list_flat:
        assert item.get('order_fee_real_id'), f'amount_list 中存在 order_fee_real_id 为空的项: {item}'

    submit_resp = payable_result['submit_resp']
    submit_data = payable_result['submit_data']
    assert submit_resp.status_code == 200, f'orderPayAccountEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'orderPayAccountEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'orderPayAccountEdit msg 不为"成功": {submit_data.get("msg")}'

    assert payable_result.get('pay_account_id'), f'pay_account_id 不应为空: {payable_result}'
    assert payable_result.get('pay_account_no'), f'pay_account_no 不应为空: {payable_result}'


def _assert_confirm_payable_ok(result):
    """
    link20 确认应付对账断言：payAccountPage + accountConfirm 全部成功。
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


def _assert_payable_invoice_apply_ok(result):
    """
    link21 发起应付开票批次申请断言：financePayList（开票）+ getOrderInfoByFeeId + batchOrderEdit 全部成功。
    """
    invoice_result = result['payable_invoice_apply_result']
    assert invoice_result is not None, 'payable_invoice_apply_result 不应为空'

    pay_list_resp = invoice_result['pay_list_invoice_resp']
    pay_list_data = invoice_result['pay_list_invoice_data']
    assert pay_list_resp.status_code == 200, f'financePayList（开票）HTTP 状态码异常: {pay_list_resp.status_code}'
    assert pay_list_data.get('code') == 200, f'financePayList（开票）失败: {pay_list_data}'
    assert pay_list_data.get('msg') == '成功', f'financePayList（开票）msg 不为"成功": {pay_list_data.get("msg")}'

    assert invoice_result.get('main_id'), f'main_id 不应为空: {invoice_result}'
    assert invoice_result.get('pay_settle_object'), f'pay_settle_object 不应为空: {invoice_result}'

    order_info_records = invoice_result['order_info_records']
    assert order_info_records, f'order_info_records 不应为空: {invoice_result["order_info_data"]}'
    for rec in order_info_records:
        assert rec.get('order_fee_real_id'), f'record 中 order_fee_real_id 不应为空: {rec}'
        assert rec.get('book_supplier_id'), f'record 中 book_supplier_id 不应为空: {rec}'

    submit_resp = invoice_result['submit_resp']
    submit_data = invoice_result['submit_data']
    assert submit_resp.status_code == 200, f'batchOrderEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'batchOrderEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'batchOrderEdit msg 不为"成功": {submit_data.get("msg")}'


# =============================================================================
# 链路19：新建...应收核销 → 发起应付对账批次
# =============================================================================
@pytest.mark.link19
class TestLink19PayableAccount:
    """链路19：新建 → ... → 应收核销 → 发起应付对账批次"""

    @allure.feature("链路测试")
    @allure.story("链路19：发起应付对账批次")
    @allure.severity("critical")
    @allure.title("链路19：应收核销 → 发起应付对账批次（financePayList + orderPayAccountEdit）")
    def test_link19_payable_account(self):
        """验证：完整链路（LINK18 + 发起应付对账批次），链路停在 payable 阶段"""
        bl_no = generate_bl_no(19)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→应收核销→发起应付对账批次）'):
            result = OrderWorkflow.full_flow(
                stop_at='payable',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK18 前置步骤断言（全部通过才执行 LK19） ----------
        with allure.step('断言：LINK18 前置链路全部成功'):
            _assert_link18_prerequisite_ok(result)

        # ---------- LINK19 发起应付对账批次断言 ----------

        with allure.step('断言：应付对账批次结果存在'):
            payable_result = result['payable_account_result']
            assert payable_result is not None, 'payable_account_result 不应为空'

        with allure.step('断言：financePayList 查询应付项列表成功'):
            pay_list_resp = payable_result['pay_list_resp']
            pay_list_data = payable_result['pay_list_data']
            assert pay_list_resp.status_code == 200, f'HTTP 状态码异常: {pay_list_resp.status_code}'
            assert pay_list_data.get('code') == 200, f'financePayList 查询失败: {pay_list_data}'
            assert pay_list_data.get('msg') == '成功', f'financePayList msg 不为"成功": {pay_list_data.get("msg")}'

        with allure.step('断言：select_list 非空（来自 financePayList 响应）'):
            select_list = payable_result['select_list']
            assert select_list, f'select_list 不应为空: {pay_list_data}'

        with allure.step('断言：amount_list_flat 包含 order_fee_real_id'):
            amount_list_flat = payable_result.get('amount_list_flat', [])
            assert amount_list_flat, f'amount_list_flat 不应为空（financePayList 响应: {pay_list_data}）'
            for item in amount_list_flat:
                assert item.get('order_fee_real_id'), f'amount_list 中存在 order_fee_real_id 为空的项: {item}'

        with allure.step('断言：orderPayAccountEdit 发起应付对账批次成功'):
            submit_resp = payable_result['submit_resp']
            submit_data = payable_result['submit_data']
            assert submit_resp.status_code == 200, f'HTTP 状态码异常: {submit_resp.status_code}'
            assert submit_data.get('code') == 200, f'orderPayAccountEdit 失败: {submit_data}'
            assert submit_data.get('msg') == '成功', f'orderPayAccountEdit msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：pay_account_id 和 pay_account_no 非空'):
            assert payable_result.get('pay_account_id'), f'pay_account_id 不应为空: {payable_result}'
            assert payable_result.get('pay_account_no'), f'pay_account_no 不应为空: {payable_result}'

        with allure.step('断言：bl_no 来自上游 link18（未被覆盖）'):
            assert result['bl_no'] == bl_no, f'bl_no 应为链路生成的: {bl_no}，实际: {result["bl_no"]}'

        with allure.step('断言：链路停在 payable 阶段'):
            assert result['stop_at'] == 'payable'


# =============================================================================
# 链路20：新建...发起应付对账批次 → 确认应付对账
# =============================================================================
@pytest.mark.link20
class TestLink20ConfirmPayable:
    """链路20：新建 → ... → 发起应付对账批次 → 确认应付对账"""

    @allure.feature("链路测试")
    @allure.story("链路20：确认应付对账")
    @allure.severity("critical")
    @allure.title("链路20：发起应付对账批次 → 确认应付对账（payAccountPage + accountConfirm）")
    def test_link20_confirm_payable(self):
        """验证：完整链路（LINK19 + 确认应付对账），链路停在 confirm_payable 阶段"""
        bl_no = generate_bl_no(20)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→发起应付对账批次→确认应付对账）'):
            result = OrderWorkflow.full_flow(
                stop_at='confirm_payable',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK19 前置步骤断言 ----------
        with allure.step('断言：LINK19 前置链路全部成功'):
            _assert_link18_prerequisite_ok(result)

        # ----- link19 发起应付对账 -----
        with allure.step('断言：发起应付对账批次成功'):
            payable_result = result['payable_account_result']
            assert payable_result is not None, 'payable_account_result 不应为空'
            pay_list_data = payable_result['pay_list_data']
            assert payable_result['pay_list_resp'].status_code == 200
            assert pay_list_data.get('code') == 200
            select_list = payable_result['select_list']
            assert select_list, f'select_list 不应为空: {pay_list_data}'
            assert payable_result['submit_resp'].status_code == 200
            assert payable_result['submit_data'].get('code') == 200
            assert payable_result.get('pay_account_id'), f'pay_account_id 不应为空'
            assert payable_result.get('pay_account_no'), f'pay_account_no 不应为空'

        # ---------- LINK20 确认应付对账断言 ----------

        with allure.step('断言：确认应付对账结果存在'):
            confirm_result = result['confirm_payable_result']
            assert confirm_result is not None, 'confirm_payable_result 不应为空'

        with allure.step('断言：payAccountPage 查询应付对账批次成功'):
            page_resp = confirm_result['pay_account_page_resp']
            page_data = confirm_result['pay_account_page_data']
            assert page_resp.status_code == 200, f'HTTP 状态码异常: {page_resp.status_code}'
            assert page_data.get('code') == 200, f'payAccountPage 查询失败: {page_data}'
            assert page_data.get('msg') == '成功', f'payAccountPage msg 不为"成功": {page_data.get("msg")}'

        with allure.step('断言：pay_account_id 非空'):
            assert confirm_result.get('pay_account_id'), f'pay_account_id 不应为空: {confirm_result}'
            assert confirm_result.get('pay_account_no'), f'pay_account_no 不应为空: {confirm_result}'

        with allure.step('断言：accountConfirm 确认应付对账成功'):
            confirm_resp = confirm_result['confirm_resp']
            confirm_data = confirm_result['confirm_data']
            assert confirm_resp.status_code == 200, f'HTTP 状态码异常: {confirm_resp.status_code}'
            assert confirm_data.get('code') == 200, f'accountConfirm 失败: {confirm_data}'
            assert confirm_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {confirm_data.get("msg")}'

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 confirm_payable 阶段'):
            assert result['stop_at'] == 'confirm_payable'



# =============================================================================
# 链路21：新建...确认应付对账 → 发起应付开票批次申请
# =============================================================================
@pytest.mark.link21
class TestLink21PayableInvoiceApply:
    """链路21：新建 → ... → 确认应付对账 → 发起应付开票批次申请"""

    @allure.feature("链路测试")
    @allure.story("链路21：发起应付开票批次申请")
    @allure.severity("critical")
    @allure.title("链路21：确认应付对账 → 发起应付开票批次申请（financePayList 开票 + getOrderInfoByFeeId + batchOrderEdit submit）")
    def test_link21_payable_invoice_apply(self):
        """验证：完整链路（LINK20 + 发起应付开票批次申请），链路停在 payable_invoice_apply 阶段"""
        bl_no = generate_bl_no(21)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→确认应付对账→发起应付开票批次申请）'):
            result = OrderWorkflow.full_flow(
                stop_at='payable_invoice_apply',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK20 前置步骤断言 ----------
        with allure.step('断言：LINK20 前置链路全部成功'):
            _assert_link18_prerequisite_ok(result)

        # ----- link19 应付对账 -----
        with allure.step('断言：发起应付对账批次成功'):
            payable_result = result['payable_account_result']
            assert payable_result is not None, 'payable_account_result 不应为空'
            assert payable_result['pay_list_resp'].status_code == 200
            assert payable_result['pay_list_data'].get('code') == 200
            assert payable_result['select_list'], f'select_list 不应为空'
            assert payable_result['submit_resp'].status_code == 200
            assert payable_result['submit_data'].get('code') == 200
            assert payable_result.get('pay_account_id')
            assert payable_result.get('pay_account_no')

        # ----- link20 确认应付对账 -----
        with allure.step('断言：确认应付对账成功'):
            confirm_result = result['confirm_payable_result']
            assert confirm_result is not None, 'confirm_payable_result 不应为空'
            assert confirm_result['pay_account_page_resp'].status_code == 200
            assert confirm_result['pay_account_page_data'].get('code') == 200
            assert confirm_result.get('pay_account_id')
            assert confirm_result['confirm_resp'].status_code == 200
            assert confirm_result['confirm_data'].get('code') == 200
            assert confirm_result['confirm_data'].get('msg') == '成功'

        # ---------- LINK21 发起应付开票批次申请断言 ----------

        with allure.step('断言：发起应付开票批次申请结果存在'):
            invoice_result = result['payable_invoice_apply_result']
            assert invoice_result is not None, 'payable_invoice_apply_result 不应为空'

        with allure.step('断言：financePayList（开票模式）查询成功'):
            pay_list_resp = invoice_result['pay_list_invoice_resp']
            pay_list_data = invoice_result['pay_list_invoice_data']
            assert pay_list_resp.status_code == 200
            assert pay_list_data.get('code') == 200
            assert pay_list_data.get('msg') == '成功'

        with allure.step('断言：main_id / pay_settle_object 已提取'):
            assert invoice_result.get('main_id'), f'main_id 不应为空: {invoice_result}'
            assert invoice_result.get('pay_settle_object'), f'pay_settle_object 不应为空'

        with allure.step('断言：getOrderInfoByFeeId 返回记录'):
            order_info_records = invoice_result['order_info_records']
            assert order_info_records, f'order_info_records 不应为空: {invoice_result["order_info_data"]}'
            for rec in order_info_records:
                assert rec.get('order_fee_real_id'), f'record 中 order_fee_real_id 不应为空: {rec}'
                assert rec.get('book_supplier_id'), f'record 中 book_supplier_id 不应为空: {rec}'

        with allure.step('断言：batchOrderEdit 应付开票批次提交成功'):
            submit_resp = invoice_result['submit_resp']
            submit_data = invoice_result['submit_data']
            assert submit_resp.status_code == 200
            assert submit_data.get('code') == 200
            assert submit_data.get('msg') == '成功', f'batchOrderEdit msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 payable_invoice_apply 阶段'):
            assert result['stop_at'] == 'payable_invoice_apply'



# =============================================================================
# 链路22：新建...发起应付开票批次申请 → 应付发票上传与登记
# =============================================================================
@pytest.mark.link22
class TestLink22PayableInvoiceRegister:
    """链路22：新建 → ... → 发起应付开票批次申请 → 应付发票上传与登记"""

    @allure.feature("链路测试")
    @allure.story("链路22：发起应付开票批次申请 + 应付发票上传与登记")
    @allure.severity("critical")
    @allure.title("链路22：发起应付开票批次申请 → 应付发票上传与登记")
    def test_link22_payable_invoice_register(self):
        """验证：完整链路（LINK21 + 应付发票上传与登记），链路停在 payable_invoice_register 阶段"""
        bl_no = generate_bl_no(22)

        with allure.step('执行链路（新建→...→发起应付开票批次申请→应付发票上传与登记）'):
            result = OrderWorkflow.full_flow(
                stop_at='payable_invoice_register',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link21）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result['payable_invoice_register_result']
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：uploadFile 成功'):
            upload_resp = upload_result['upload_resp']
            assert upload_resp.status_code == 200, (
                f'uploadFile HTTP 状态码异常: {upload_resp.status_code}'
            )
            upload_data = upload_result['upload_data']
            assert upload_data.get('code') == 200, (
                f'uploadFile code 不为 200: {upload_data}'
            )
            uploaded_file_info = upload_result['uploaded_file_info']
            assert uploaded_file_info.get('file_id'), (
                f'uploadFile 未返回 file_id: {uploaded_file_info}'
            )

        with allure.step('断言：invoiceAdd 成功'):
            add_resp = upload_result['add_resp']
            assert add_resp.status_code == 200, (
                f'invoiceAdd HTTP 状态码异常: {add_resp.status_code}'
            )
            add_data = upload_result['add_data']
            assert add_data.get('code') == 200, (
                f'invoiceAdd code 不为 200: {add_data}'
            )
            pay_invoice_id = upload_result['pay_invoice_id']
            assert pay_invoice_id, f'invoiceAdd 未返回 pay_invoice_id: {upload_result}'

        with allure.step('断言：applyPage 成功'):
            apply_resp = upload_result['apply_page_resp']
            assert apply_resp.status_code == 200, (
                f'applyPage HTTP 状态码异常: {apply_resp.status_code}'
            )
            apply_data = upload_result['apply_page_data']
            assert apply_data.get('code') == 200, (
                f'applyPage code 不为 200: {apply_data}'
            )
            pay_invoice_apply_id = upload_result['pay_invoice_apply_id']
            assert pay_invoice_apply_id, (
                f'applyPage 未返回 pay_invoice_apply_id: {upload_result}'
            )

        with allure.step('断言：allocationInvoiceFee 成功'):
            alloc_resp = upload_result['alloc_resp']
            assert alloc_resp.status_code == 200, (
                f'allocationInvoiceFee HTTP 状态码异常: {alloc_resp.status_code}'
            )
            alloc_data = upload_result['alloc_data']
            assert alloc_data.get('code') == 200, (
                f'allocationInvoiceFee code 不为 200: {alloc_data}'
            )

        with allure.step('断言：链路停在 payable_invoice_register 阶段'):
            assert result['stop_at'] == 'payable_invoice_register'



# =============================================================================
# 链路23：新建...应付发票上传与登记 → 发起付款需求
# =============================================================================
@pytest.mark.link23
class TestLink23PayDemand:
    """链路23：新建 → ... → 应付发票上传与登记 → 发起付款需求"""

    @allure.feature("链路测试")
    @allure.story("链路23：发起付款需求")
    @allure.severity("critical")
    @allure.title("链路23：应付发票上传与登记 → 发起付款需求")
    def test_link23_pay_demand(self):
        """验证：完整链路（LINK22 + 发起付款需求），链路停在 pay_demand 阶段"""
        bl_no = generate_bl_no(23)

        with allure.step('执行链路（新建→...→应付发票上传与登记→发起付款需求）'):
            result = OrderWorkflow.full_flow(
                stop_at='pay_demand',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link22）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result.get('payable_invoice_register_result')
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：发起付款需求结果存在'):
            demand_result = result['pay_demand_result']
            assert demand_result is not None, 'pay_demand_result 不应为空'

        with allure.step('断言：financePayList 查询应付费用列表成功'):
            pay_list_resp = demand_result['pay_list_resp']
            pay_list_data = demand_result['pay_list_data']
            assert pay_list_resp.status_code == 200, (
                f'financePayList HTTP 状态码异常: {pay_list_resp.status_code}'
            )
            assert pay_list_data.get('code') == 200, (
                f'financePayList 查询失败: {pay_list_data}'
            )
            assert pay_list_data.get('msg') == '成功', (
                f'financePayList msg 不为"成功": {pay_list_data.get("msg")}'
            )

        with allure.step('断言：select_list 非空'):
            select_list = demand_result.get('select_list', [])
            assert select_list, f'select_list 不应为空: {pay_list_data}'

        with allure.step('断言：cost_usd / cost_cny 已计算'):
            cost_usd = demand_result.get('cost_usd')
            cost_cny = demand_result.get('cost_cny')
            assert cost_usd, f'cost_usd 不应为空: {demand_result}'
            assert cost_cny is not None, f'cost_cny 不应为空: {demand_result}'
            assert float(cost_usd) > 0, f'cost_usd 应大于 0: {cost_usd}'

        with allure.step('断言：paymentList 付款需求预览成功'):
            payment_resp = demand_result['payment_list_resp']
            payment_data = demand_result['payment_list_data']
            assert payment_resp.status_code == 200, (
                f'paymentList HTTP 状态码异常: {payment_resp.status_code}'
            )
            assert payment_data.get('code') == 200, (
                f'paymentList 失败: {payment_data}'
            )

        with allure.step('断言：payment_list 非空'):
            payment_list = demand_result.get('payment_list', [])
            assert payment_list, f'payment_list 不应为空: {payment_data}'

        with allure.step('断言：demandEditByOrder 提交付款需求成功'):
            submit_resp = demand_result['submit_resp']
            submit_data = demand_result['submit_data']
            assert submit_resp.status_code == 200, (
                f'demandEditByOrder HTTP 状态码异常: {submit_resp.status_code}'
            )
            assert submit_data.get('code') == 200, (
                f'demandEditByOrder 失败: {submit_data}'
            )
            assert submit_data.get('msg') == '成功', (
                f'demandEditByOrder msg 不为"成功": {submit_data.get("msg")}'
            )

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 pay_demand 阶段'):
            assert result['stop_at'] == 'pay_demand'



# =============================================================================
# 链路24：新建...发起付款需求 → 审核生成付款单
# =============================================================================
@pytest.mark.link24
class TestLink24PayDemandAudit:
    """链路24：新建 → ... → 发起付款需求 → 审核生成付款单"""

    @allure.feature("链路测试")
    @allure.story("链路24：审核生成付款单")
    @allure.severity("critical")
    @allure.title("链路24：发起付款需求 → 审核生成付款单")
    def test_link24_pay_demand_audit(self):
        """验证：完整链路（LINK23 + 审核生成付款单），链路停在 pay_demand_audit 阶段"""
        bl_no = generate_bl_no(24)

        with allure.step('执行链路（新建→...→发起付款需求→审核生成付款单）'):
            result = OrderWorkflow.full_flow(
                stop_at='pay_demand_audit',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link23）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result.get('payable_invoice_register_result')
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：发起付款需求结果存在'):
            demand_result = result.get('pay_demand_result')
            assert demand_result is not None, 'pay_demand_result 不应为空'

        with allure.step('断言：审核生成付款单结果存在'):
            audit_result = result['pay_demand_audit_result']
            assert audit_result is not None, 'pay_demand_audit_result 不应为空'

        with allure.step('断言：auditPage 查询待审核列表成功'):
            audit_page_resp = audit_result['audit_page_resp']
            audit_page_data = audit_result['audit_page_data']
            assert audit_page_resp.status_code == 200, (
                f'auditPage HTTP 状态码异常: {audit_page_resp.status_code}'
            )
            assert audit_page_data.get('code') == 200, (
                f'auditPage 查询失败: {audit_page_data}'
            )

        with allure.step('断言：audit_records 非空'):
            audit_records = audit_result.get('audit_records', [])
            assert audit_records, f'audit_records 不应为空: {audit_page_data}'

        with allure.step('断言：audit_id 非空'):
            audit_id = audit_result.get('audit_id')
            assert audit_id, f'audit_id 不应为空: {audit_result}'

        with allure.step('断言：audit_type 为 payDemand'):
            audit_type = audit_result.get('audit_type')
            assert audit_type == 'payDemand', f'audit_type 应为 payDemand: {audit_type}'

        with allure.step('断言：auditExecute 执行审批成功'):
            audit_execute_resp = audit_result['audit_execute_resp']
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_execute_resp.status_code == 200, (
                f'auditExecute HTTP 状态码异常: {audit_execute_resp.status_code}'
            )
            assert audit_execute_data.get('code') == 200, (
                f'auditExecute 失败: {audit_execute_data}'
            )

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 pay_demand_audit 阶段'):
            assert result['stop_at'] == 'pay_demand_audit'



# =============================================================================
# 链路25：新建...审核生成付款单 → 付款单核销
# =============================================================================
@pytest.mark.link25
class TestLink25PayWriteoff:
    """链路25：新建 → ... → 审核生成付款单 → 付款单核销"""

    @allure.feature("链路测试")
    @allure.story("链路25：付款单核销")
    @allure.severity("critical")
    @allure.title("链路25：审核生成付款单 → 付款单核销")
    def test_link25_pay_writeoff(self):
        """验证：完整链路（LINK24 + 付款单核销），链路停在 pay_writeoff 阶段"""
        bl_no = generate_bl_no(25)

        with allure.step('执行链路（新建→...→审核生成付款单→付款单核销）'):
            result = OrderWorkflow.full_flow(
                stop_at='pay_writeoff',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link24）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result.get('payable_invoice_register_result')
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：发起付款需求结果存在'):
            demand_result = result.get('pay_demand_result')
            assert demand_result is not None, 'pay_demand_result 不应为空'

        with allure.step('断言：审核生成付款单结果存在'):
            audit_result = result.get('pay_demand_audit_result')
            assert audit_result is not None, 'pay_demand_audit_result 不应为空'

        with allure.step('断言：付款单核销结果存在'):
            writeoff_result = result['pay_writeoff_result']
            assert writeoff_result is not None, 'pay_writeoff_result 不应为空'

        with allure.step('断言：formPage 查询付款单列表成功'):
            form_page_resp = writeoff_result['form_page_resp']
            form_page_data = writeoff_result['form_page_data']
            assert form_page_resp.status_code == 200, (
                f'formPage HTTP 状态码异常: {form_page_resp.status_code}'
            )
            assert form_page_data.get('code') == 200, (
                f'formPage 查询失败: {form_page_data}'
            )

        with allure.step('断言：pay_form_records 非空'):
            pay_form_records = writeoff_result.get('pay_form_records', [])
            assert pay_form_records, f'pay_form_records 不应为空: {form_page_data}'

        with allure.step('断言：pay_form_id 非空'):
            pay_form_id = writeoff_result.get('pay_form_id')
            assert pay_form_id, f'pay_form_id 不应为空: {writeoff_result}'

        with allure.step('断言：writeoffPayFormList 成功'):
            writeoff_pay_form_list_resp = writeoff_result['writeoff_pay_form_list_resp']
            writeoff_pay_form_list_data = writeoff_result['writeoff_pay_form_list_data']
            assert writeoff_pay_form_list_resp.status_code == 200, (
                f'writeoffPayFormList HTTP 状态码异常: {writeoff_pay_form_list_resp.status_code}'
            )
            assert writeoff_pay_form_list_data.get('code') == 200, (
                f'writeoffPayFormList 失败: {writeoff_pay_form_list_data}'
            )

        with allure.step('断言：orderFeePage 查询成功'):
            order_fee_page_resp = writeoff_result['order_fee_page_resp']
            order_fee_page_data = writeoff_result['order_fee_page_data']
            assert order_fee_page_resp.status_code == 200, (
                f'orderFeePage HTTP 状态码异常: {order_fee_page_resp.status_code}'
            )
            assert order_fee_page_data.get('code') == 200, (
                f'orderFeePage 失败: {order_fee_page_data}'
            )

        with allure.step('断言：writeoffBatch 执行核销成功'):
            writeoff_batch_resp = writeoff_result['writeoff_batch_resp']
            writeoff_batch_data = writeoff_result['writeoff_batch_data']
            assert writeoff_batch_resp.status_code == 200, (
                f'writeoffBatch HTTP 状态码异常: {writeoff_batch_resp.status_code}'
            )
            assert writeoff_batch_data.get('code') == 200, (
                f'writeoffBatch 失败: {writeoff_batch_data}'
            )

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 pay_writeoff 阶段'):
            assert result['stop_at'] == 'pay_writeoff'


