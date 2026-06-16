"""
链路测试 - 应收发票（link15~17）

  link15 - 发起应收开票批次审批
  link16 - 审核生成开票申请
  link17 - 发票上传与登记
"""
import time as _time
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from data.order_data import BookRealAmountData


def _build_fee_config():
    return {
        'to_customer_fees': BookRealAmountData.get_customer_standard_fees(),
        'to_supplier_fees': BookRealAmountData.get_supplier_standard_fees(),
    }


def _assert_audit_and_fee_doc_ok(result):
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
    assert invoice_result['send_data']['code'] == 200
    assert invoice_result.get('audit_id')
    assert invoice_result['approve_resp'].status_code == 200
    assert invoice_result['approve_data']['code'] == 200

    advance_result = result['supplier_advance_result']
    assert advance_result is not None
    assert advance_result['send_resp'].status_code == 200
    assert advance_result['send_data']['code'] == 200
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

    receive_result = result['receive_account_result']
    assert receive_result is not None
    assert receive_result['put_list_resp'].status_code == 200
    assert receive_result['put_list_data'].get('code') == 200
    assert receive_result['check_resp'].status_code == 200
    assert receive_result['check_data'].get('code') == 200
    assert receive_result['submit_resp'].status_code == 200
    assert receive_result['submit_data'].get('code') == 200
    assert receive_result['submit_data'].get('msg') == '成功'
    assert receive_result['receive_account_id']
    assert receive_result['receive_account_no'].startswith('YSDZPC')

    confirm_result = result['confirm_account_result']
    assert confirm_result is not None
    assert confirm_result['detail_resp'].status_code == 200
    assert confirm_result['detail_data'].get('code') == 200
    assert confirm_result['confirm_list_resp'].status_code == 200
    assert confirm_result['confirm_list_data'].get('code') == 200
    confirm_list = confirm_result['confirm_list']
    assert confirm_list is not None
    assert isinstance(confirm_list, list)
    assert len(confirm_list) > 0
    assert confirm_result['submit_resp'].status_code == 200
    assert confirm_result['submit_data'].get('code') == 200
    assert confirm_result['submit_data'].get('msg') == '成功'
    assert confirm_result['page_resp'].status_code == 200
    assert confirm_result['page_data'].get('code') == 200


def _assert_invoice_batch_ok(result):
    invoice_batch_result = result['invoice_batch_result']
    assert invoice_batch_result is not None, 'invoice_batch_result 不应为空'
    put_list_data = invoice_batch_result['put_list_data']
    assert invoice_batch_result['put_list_resp'].status_code == 200
    assert put_list_data.get('code') == 200, f'查询应收款项列表失败: {put_list_data}'
    rate_data = invoice_batch_result['rate_data']
    assert invoice_batch_result['rate_resp'].status_code == 200
    assert rate_data.get('code') == 200, f'获取汇率失败: {rate_data}'
    assert invoice_batch_result.get('exchange_rate'), '汇率为空'
    sell_info_data = invoice_batch_result['sell_info_data']
    assert invoice_batch_result['sell_info_resp'].status_code == 200
    assert sell_info_data.get('code') == 200, f'获取开票方信息失败: {sell_info_data}'
    invoice_submit_data = invoice_batch_result['invoice_submit_data']
    assert invoice_batch_result['invoice_submit_resp'].status_code == 200
    assert invoice_submit_data.get('code') == 200, f'提交应收开票批次申请失败: {invoice_submit_data}'
    assert invoice_submit_data.get('msg') == '成功', f'提交应收开票批次申请 msg 不为"成功": {invoice_submit_data.get("msg")}'
    page_data = invoice_batch_result['page_data']
    assert invoice_batch_result['page_resp'].status_code == 200
    assert page_data.get('code') == 200, f'验证批次查询失败: {page_data}'
    assert page_data.get('msg') == '成功', f'批次查询 msg 不为"成功": {page_data.get("msg")}'
    return invoice_batch_result


# =============================================================================
# 链路15：新建...发起应收对账批次 → 确认应收对账 → 发起应收开票批次审批
# =============================================================================
@pytest.mark.link15
class TestLink15InvoiceBatch:
    """链路15：新建 → ... → 发起应收对账批次 → 确认应收对账 → 发起应收开票批次审批"""

    @allure.feature("链路测试")
    @allure.story("链路15：发起应收开票批次审批")
    @allure.severity("critical")
    @allure.title("链路15：发起应收对账 → 确认应收对账 → 发起应收开票批次审批")
    def test_link15_invoice_batch(self):
        """验证：完整链路（LINK14 + 发起应收开票批次审批），链路停在 invoice_batch 阶段"""
        bl_no = 'LK15_' + _time.strftime('%Y%m%d%H%M%S')

        with allure.step('执行链路（新建→...→发起应收对账批次→确认应收对账→发起应收开票批次审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_batch',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：LINK14 之前所有步骤成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：发起应收开票批次审批结果存在'):
            invoice_result = result['invoice_batch_result']
            assert invoice_result is not None, 'invoice_batch_result 不应为空'

        with allure.step('断言：financePutList 查询成功'):
            put_list_data = invoice_result['put_list_data']
            assert invoice_result['put_list_resp'].status_code == 200
            assert put_list_data.get('code') == 200, f'查询应收款项列表失败: {put_list_data}'

        with allure.step('断言：monthExchangeRate 获取汇率成功'):
            rate_data = invoice_result['rate_data']
            assert invoice_result['rate_resp'].status_code == 200
            assert rate_data.get('code') == 200, f'获取汇率失败: {rate_data}'
            assert invoice_result.get('exchange_rate'), '汇率为空'

        with allure.step('断言：getSellInfo 获取开票方信息成功'):
            sell_info_data = invoice_result['sell_info_data']
            assert invoice_result['sell_info_resp'].status_code == 200
            assert sell_info_data.get('code') == 200, f'获取开票方信息失败: {sell_info_data}'

        with allure.step('断言：batchOrderEdit 提交应收开票批次申请成功'):
            invoice_submit_data = invoice_result['invoice_submit_data']
            assert invoice_result['invoice_submit_resp'].status_code == 200
            assert invoice_submit_data.get('code') == 200, f'提交应收开票批次申请失败: {invoice_submit_data}'
            assert invoice_submit_data.get('msg') == '成功', f'提交应收开票批次申请 msg 不为"成功": {invoice_submit_data.get("msg")}'

        with allure.step('断言：batchPage 查询批次成功'):
            page_data = invoice_result['page_data']
            assert invoice_result['page_resp'].status_code == 200
            assert page_data.get('code') == 200, f'验证批次查询失败: {page_data}'
            assert page_data.get('msg') == '成功', f'批次查询 msg 不为"成功": {page_data.get("msg")}'

        with allure.step('断言：链路停在 invoice_batch 阶段'):
            assert result['stop_at'] == 'invoice_batch'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
                '生成费用确认单',
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
                '查询应收款项列表（开票）',
                '获取汇率',
                '获取开票方信息',
                '提交应收开票批次申请',
                '验证应收开票批次',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路16：新建...发起应收开票批次审批 → 审核生成开票申请
# =============================================================================
@pytest.mark.link16
class TestLink16InvoiceBatchAudit:
    """链路16：新建 → ... → 发起应收开票批次审批 → 审核生成开票申请"""

    @allure.feature("链路测试")
    @allure.story("链路16：审核生成开票申请")
    @allure.severity("critical")
    @allure.title("链路16：发起应收开票批次审批 → 审核生成开票申请")
    def test_link16_invoice_batch_audit(self):
        """验证：完整链路（LINK15 + 审核生成开票申请），链路停在 invoice_batch_audit 阶段"""
        bl_no = 'LK16_' + _time.strftime('%Y%m%d%H%M%S')

        with allure.step('执行链路（新建→...→发起应收开票批次审批→审核生成开票申请）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_batch_audit',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：LINK14 之前所有步骤成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：发起应收开票批次审批成功'):
            invoice_batch_result = _assert_invoice_batch_ok(result)
            assert invoice_batch_result.get('batch_id'), f'batch_id 不应为空: {invoice_batch_result}'

        with allure.step('断言：审核生成开票申请结果存在'):
            audit_result = result['invoice_batch_audit_result']
            assert audit_result is not None, 'invoice_batch_audit_result 不应为空'

        with allure.step('断言：auditPage 查询审批ID成功'):
            audit_query_data = audit_result['audit_query_data']
            assert audit_result['audit_query_resp'].status_code == 200
            assert audit_query_data.get('code') == 200, f'auditPage 查询失败: {audit_query_data}'
            assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'

        with allure.step('断言：auditExecute 审批通过成功'):
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_result['audit_execute_resp'].status_code == 200
            assert audit_execute_data.get('code') == 200, f'auditExecute 审批失败: {audit_execute_data}'
            assert '成功' in audit_execute_data.get('msg', ''), f'auditExecute msg 不含"成功": {audit_execute_data.get("msg")}'

        with allure.step('断言：链路停在 invoice_batch_audit 阶段'):
            assert result['stop_at'] == 'invoice_batch_audit'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
                '生成费用确认单',
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
                '查询应收款项列表（开票）',
                '获取汇率',
                '获取开票方信息',
                '提交应收开票批次申请',
                '验证应收开票批次',
                '查询应收开票批次审批ID',
                '审批通过应收开票批次',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路17：新建...审核生成开票申请 → 发票上传与登记
# =============================================================================
@pytest.mark.link17
class TestLink17InvoiceUpload:
    """链路17：新建 → ... → 审核生成开票申请 → 发票上传与登记"""

    @allure.feature("链路测试")
    @allure.story("链路17：发票上传与登记")
    @allure.severity("critical")
    @allure.title("链路17：审核生成开票申请 → 发票上传与登记")
    def test_link17_invoice_upload(self):
        """验证：完整链路（LINK16 + 发票上传与登记），链路停在 invoice_upload 阶段"""
        bl_no = 'LK17_' + _time.strftime('%Y%m%d%H%M%S')

        with allure.step('执行链路（新建→...→审核生成开票申请→发票上传与登记）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_upload',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：LINK14 之前所有步骤成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：发起应收开票批次审批成功'):
            invoice_batch_result = _assert_invoice_batch_ok(result)
            assert invoice_batch_result.get('batch_id'), f'batch_id 不应为空: {invoice_batch_result}'

        with allure.step('断言：审核生成开票申请成功'):
            audit_result = result['invoice_batch_audit_result']
            assert audit_result is not None, 'invoice_batch_audit_result 不应为空'
            audit_query_data = audit_result['audit_query_data']
            assert audit_result['audit_query_resp'].status_code == 200
            assert audit_query_data.get('code') == 200, f'auditPage 查询失败: {audit_query_data}'
            assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_result['audit_execute_resp'].status_code == 200
            assert audit_execute_data.get('code') == 200, f'auditExecute 审批失败: {audit_execute_data}'
            assert '成功' in audit_execute_data.get('msg', ''), f'auditExecute msg 不含"成功": {audit_execute_data.get("msg")}'

        with allure.step('断言：发票上传与登记结果存在'):
            upload_result = result['invoice_upload_result']
            assert upload_result is not None, 'invoice_upload_result 不应为空'

        with allure.step('断言：invoiceAdd 上传发票成功'):
            add_data = upload_result['add_data']
            assert upload_result['add_resp'].status_code == 200
            assert add_data.get('code') == 200, f'invoiceAdd 上传失败: {add_data}'
            assert add_data.get('msg') == '成功', f'invoiceAdd msg 不为"成功": {add_data.get("msg")}'
            assert upload_result.get('receive_invoice_id'), f'receive_invoice_id 不应为空: {upload_result}'

        with allure.step('断言：applyPage 获取发票申请ID成功'):
            apply_page_data = upload_result['apply_page_data']
            assert upload_result['apply_page_resp'].status_code == 200
            assert apply_page_data.get('code') == 200, f'applyPage 查询失败: {apply_page_data}'
            assert apply_page_data.get('msg') == '成功', f'applyPage msg 不为"成功": {apply_page_data.get("msg")}'
            assert upload_result.get('receive_invoice_apply_id'), f'receive_invoice_apply_id 不应为空: {upload_result}'

        with allure.step('断言：allocationInvoiceFee 登记发票成功'):
            alloc_data = upload_result['alloc_data']
            assert upload_result['alloc_resp'].status_code == 200
            assert alloc_data.get('code') == 200, f'allocationInvoiceFee 登记失败: {alloc_data}'
            assert alloc_data.get('msg') == '成功', f'allocationInvoiceFee msg 不为"成功": {alloc_data.get("msg")}'

        with allure.step('断言：链路停在 invoice_upload 阶段'):
            assert result['stop_at'] == 'invoice_upload'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
                '生成费用确认单',
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
                '查询应收款项列表（开票）',
                '获取汇率',
                '获取开票方信息',
                '提交应收开票批次申请',
                '验证应收开票批次',
                '查询应收开票批次审批ID',
                '审批通过应收开票批次',
                '上传应收发票',
                '获取发票申请ID',
                '登记发票到申请',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
