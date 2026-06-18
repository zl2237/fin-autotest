"""
链路测试 - 应付对账（link19）

  link19 - 发起应付对账批次（link18 + financePayList + orderPayAccountEdit）
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
                '查询应收核销费用列表',
                '应收核销',
                '查询应付项列表',
                '发起应付对账批次',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
