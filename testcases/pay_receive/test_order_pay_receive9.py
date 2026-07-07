"""
测试链路 21：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no
from testcases.pay_receive.helpers import _build_fee_config, _assert_audit_and_fee_doc_ok, _assert_receive_account_ok, _assert_confirm_receive_ok


@pytest.mark.order_pay_receive9
class TestOrderPayReceive9ConfirmReceive:

    @allure.severity("critical")
    def test_order_pay_receive9_confirm_receive(self):
        bl_no = generate_bl_no(109)

        with allure.step("执行完整订单流程，运行至确认应收节点 confirm_account"):
            result = PayReceiveWorkflow.run(
                stop_at="confirm_account",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：审核及费用单据信息"):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step("校验：应收账户数据"):
            _assert_receive_account_ok(result)

        with allure.step("校验：确认应收对账结果"):
            _assert_confirm_receive_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "confirm_account"