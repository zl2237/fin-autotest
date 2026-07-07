"""
测试链路 14：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no
from testcases.pay_receive.helpers import _build_fee_config, _assert_link12_prerequisite_ok, _assert_payable_account_ok, _assert_confirm_payable_ok


@pytest.mark.order_pay_receive2
class TestOrderPayReceive2ConfirmPayable:

    @allure.severity("critical")
    def test_order_pay_receive2_confirm_payable(self):
        bl_no = generate_bl_no(102)

        with allure.step("执行完整订单流程，运行至确认应付对账节点 confirm_payable"):
            result = PayReceiveWorkflow.run(
                stop_at="confirm_payable",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：订单 1~12 前置流程全部完成"):
            _assert_link12_prerequisite_ok(result)

        with allure.step("校验：应付对账数据"):
            _assert_payable_account_ok(result)

        with allure.step("校验：确认应付对账结果"):
            _assert_confirm_payable_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "confirm_payable"