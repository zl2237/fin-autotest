"""
链路测试 - 应收对账（link13~14）

  link13 - 发起应收对账批次
  link14 - 确认应收对账
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


def _assert_audit_and_fee_doc_ok(result):
    """link13/14 共用的"录费用+资产推送+订单锁定+开票申请+供应商垫付+费用通知+费用确认"链式断言。"""
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

    confirm_result = result['fee_confirm_result']
    assert confirm_result is not None
    assert confirm_result['resp'].status_code == 200
    assert confirm_result['data']['code'] == 200


def _assert_receive_account_ok(result):
    """link13/14 共用的"发起应收对账批次"断言。"""
    receive_result = result['receive_account_result']
    assert receive_result is not None, '应收对账批次结果不应为空'
    assert receive_result['put_list_resp'].status_code == 200
    assert receive_result['put_list_data'].get('code') == 200
    assert receive_result['check_resp'].status_code == 200
    assert receive_result['check_data'].get('code') == 200
    assert receive_result['submit_resp'].status_code == 200
    assert receive_result['submit_data'].get('code') == 200
    assert receive_result['submit_data'].get('msg') == '成功'
    assert receive_result['receive_account_id']
    assert receive_result['receive_account_no'].startswith('YSDZPC')


# =============================================================================
# 链路13：新建...生成费用确认单 → 发起应收对账批次
# =============================================================================
@pytest.mark.link13
class TestLink13ReceiveAccount:
    """链路13：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单 → 生成费用确认单 → 发起应收对账批次"""

    @allure.feature("链路测试")
    @allure.story("链路13：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单、生成费用确认单、发起应收对账批次")
    @allure.severity("critical")
    @allure.title("链路13：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单 → 生成费用确认单 → 发起应收对账批次")
    def test_link13_receive_account(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 费用通知单 + 费用确认单 + 应收对账批次），链路停在 receive_account 阶段"""
        bl_no = generate_bl_no(13)

        with allure.step('执行链路（新建→...→生成费用确认单→发起应收对账批次）'):
            result = OrderWorkflow.full_flow(
                stop_at='receive_account',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：审批与费用单据链路全部成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：应收对账批次结果存在'):
            receive_result = result['receive_account_result']
            assert receive_result is not None, '应收对账批次结果不应为空'

        with allure.step('断言：financePutList 查询成功'):
            put_list_resp = receive_result['put_list_resp']
            assert put_list_resp.status_code == 200, f'financePutList HTTP 状态码异常: {put_list_resp.status_code}'
            put_list_data = receive_result['put_list_data']
            assert put_list_data.get('code') == 200, f'financePutList code 不为 200: {put_list_data}'

        with allure.step('断言：select_list 非空'):
            select_list = receive_result['select_list']
            assert select_list is not None, 'select_list 不应为 None'
            assert isinstance(select_list, list), f'select_list 应为 list，实际: {type(select_list)}'
            assert len(select_list) > 0, f'select_list 不应为空，实际: {select_list}'

        with allure.step('断言：预校验（action=check）成功'):
            check_resp = receive_result['check_resp']
            assert check_resp.status_code == 200, f'预校验 HTTP 状态码异常: {check_resp.status_code}'
            check_data = receive_result['check_data']
            assert check_data.get('code') == 200, f'预校验 code 不为 200: {check_data}'
            assert check_data.get('msg') == '成功', f'预校验 msg 不为"成功": {check_data.get("msg")}'

        with allure.step('断言：正式提交（action=submit）成功'):
            submit_resp = receive_result['submit_resp']
            assert submit_resp.status_code == 200, f'正式提交 HTTP 状态码异常: {submit_resp.status_code}'
            submit_data = receive_result['submit_data']
            assert submit_data.get('code') == 200, f'正式提交 code 不为 200: {submit_data}'
            assert submit_data.get('msg') == '成功', f'正式提交 msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：receive_account_id 非空'):
            receive_account_id = receive_result['receive_account_id']
            assert receive_account_id, f'receive_account_id 不应为空: {receive_result}'

        with allure.step('断言：receive_account_no 非空且为字符串'):
            receive_account_no = receive_result['receive_account_no']
            assert receive_account_no, f'receive_account_no 不应为空: {receive_result}'
            assert isinstance(receive_account_no, str), f'receive_account_no 应为 str，实际: {type(receive_account_no)}'

        with allure.step('断言：receive_account_no 格式正确（以 YSDZPC 开头）'):
            assert receive_account_no.startswith('YSDZPC'), \
                f'receive_account_no 应以 YSDZPC 开头，实际: {receive_account_no}'

        with allure.step('断言：链路停在 receive_account 阶段'):
            assert result['stop_at'] == 'receive_account'

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
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路14：新建...发起应收对账批次 → 确认应收对账
# =============================================================================
@pytest.mark.link14
class TestLink14ConfirmAccount:
    """链路14：新建 → ... → 发起应收对账批次 → 确认应收对账"""

    @allure.feature("链路测试")
    @allure.story("链路14：发起应收对账批次 + 确认应收对账")
    @allure.severity("critical")
    @allure.title("链路14：发起应收对账批次 → 确认应收对账")
    def test_link14_confirm_account(self):
        """验证：完整链路（LINK13 + 确认应收对账），链路停在 confirm_account 阶段"""
        bl_no = generate_bl_no(14)

        with allure.step('执行链路（新建→...→发起应收对账批次→确认应收对账）'):
            result = OrderWorkflow.full_flow(
                stop_at='confirm_account',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：审批与费用单据链路全部成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：发起应收对账批次成功'):
            _assert_receive_account_ok(result)

        with allure.step('断言：确认应收对账结果存在'):
            confirm_result = result['confirm_account_result']
            assert confirm_result is not None, '确认应收对账结果不应为空'

        with allure.step('断言：receiveAccountDetail 查询成功'):
            detail_resp = confirm_result['detail_resp']
            assert detail_resp.status_code == 200, f'HTTP 状态码异常: {detail_resp.status_code}'
            detail_data = confirm_result['detail_data']
            assert detail_data.get('code') == 200, f'receiveAccountDetail code 不为 200: {detail_data}'
            assert detail_data.get('msg') == '成功', f'receiveAccountDetail msg 不为"成功": {detail_data.get("msg")}'

        with allure.step('断言：receiveConfirmList 查询成功'):
            confirm_list_resp = confirm_result['confirm_list_resp']
            assert confirm_list_resp.status_code == 200, f'HTTP 状态码异常: {confirm_list_resp.status_code}'
            confirm_list_data = confirm_result['confirm_list_data']
            assert confirm_list_data.get('code') == 200, f'receiveConfirmList code 不为 200: {confirm_list_data}'
            assert confirm_list_data.get('msg') == '成功', f'receiveConfirmList msg 不为"成功": {confirm_list_data.get("msg")}'

        with allure.step('断言：confirm_list 非空'):
            confirm_list = confirm_result['confirm_list']
            assert confirm_list is not None
            assert isinstance(confirm_list, list)
            assert len(confirm_list) > 0, 'confirm_list 不应为空'

        with allure.step('断言：accountConfirm 确认成功'):
            submit_resp = confirm_result['submit_resp']
            assert submit_resp.status_code == 200, f'HTTP 状态码异常: {submit_resp.status_code}'
            submit_data = confirm_result['submit_data']
            assert submit_data.get('code') == 200, f'accountConfirm code 不为 200: {submit_data}'
            assert submit_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：receiveAccountPage 查询成功'):
            page_resp = confirm_result['page_resp']
            assert page_resp.status_code == 200, f'HTTP 状态码异常: {page_resp.status_code}'
            page_data = confirm_result['page_data']
            assert page_data.get('code') == 200, f'receiveAccountPage code 不为 200: {page_data}'
            assert page_data.get('msg') == '成功', f'receiveAccountPage msg 不为"成功": {page_data.get("msg")}'

        with allure.step('断言：链路停在 confirm_account 阶段'):
            assert result['stop_at'] == 'confirm_account'

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
            ]:
                assert name in step_names, f'steps 缺少: {name}'
