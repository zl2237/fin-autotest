"""
测试链路 19：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no
from testcases.pay_receive.helpers import _build_fee_config, _assert_link12_prerequisite_ok, _assert_payable_account_ok, _assert_confirm_payable_ok, _assert_payable_invoice_apply_ok, _assert_payable_invoice_register_ok, _assert_pay_demand_ok, _assert_pay_demand_audit_ok, _assert_pay_writeoff_ok


@pytest.mark.order_pay_receive7
class TestOrderPayReceive7PayWriteoff:

    @allure.severity("critical")
    def test_order_pay_receive7_pay_writeoff(self):
        bl_no = generate_bl_no(107)

        with allure.step("执行完整订单流程，运行至付款核销节点 pay_writeoff"):
            result = PayReceiveWorkflow.run(
                stop_at="pay_writeoff",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：订单 1~12 前置流程全部完成"):
            _assert_link12_prerequisite_ok(result)

        with allure.step("校验：应付对账数据"):
            _assert_payable_account_ok(result)

        with allure.step("校验：确认应付对账结果"):
            _assert_confirm_payable_ok(result)

        with allure.step("校验：应付开票申请批次数据"):
            _assert_payable_invoice_apply_ok(result)

        with allure.step("校验：应付发票登记数据"):
            _assert_payable_invoice_register_ok(result)

        with allure.step("校验：付款申请数据"):
            _assert_pay_demand_ok(result)

        with allure.step("校验：付款申请审核通过"):
            _assert_pay_demand_audit_ok(result)

        with allure.step("校验：付款核销数据"):
            _assert_pay_writeoff_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "pay_writeoff"