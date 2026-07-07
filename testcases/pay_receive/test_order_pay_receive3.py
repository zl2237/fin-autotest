"""
测试链路 15：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no
from testcases.pay_receive.helpers import _build_fee_config, _assert_link12_prerequisite_ok, _assert_payable_account_ok, _assert_confirm_payable_ok, _assert_payable_invoice_apply_ok


@pytest.mark.order_pay_receive3
class TestOrderPayReceive3InvoiceApply:

    @allure.severity("critical")
    def test_order_pay_receive3_invoice_apply(self):
        bl_no = generate_bl_no(103)

        with allure.step("执行完整订单流程，运行至应付开票申请节点 payable_invoice_apply"):
            result = PayReceiveWorkflow.run(
                stop_at="payable_invoice_apply",
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

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "payable_invoice_apply"