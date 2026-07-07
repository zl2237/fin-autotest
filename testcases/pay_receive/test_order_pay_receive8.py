"""
测试链路 20：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no
from testcases.pay_receive.helpers import _build_fee_config, _assert_audit_and_fee_doc_ok, _assert_receive_account_ok


@pytest.mark.order_pay_receive8
class TestOrderPayReceive8ReceiveAccount:

    @allure.severity("critical")
    def test_order_pay_receive8_receive_account(self):
        bl_no = generate_bl_no(108)

        with allure.step("执行完整订单流程，运行至应收账户节点 receive_account"):
            result = PayReceiveWorkflow.run(
                stop_at="receive_account",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：审核及费用单据信息"):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step("校验：应收账户数据"):
            _assert_receive_account_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "receive_account"