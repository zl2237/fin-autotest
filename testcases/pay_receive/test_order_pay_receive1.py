"""
测试链路 13：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from data.order import BookRealAmountData
from testcases.pay_receive.helpers import (
    _assert_link12_prerequisite_ok,
    _assert_payable_account_ok,
)
from utils import generate_bl_no
from workflows.pay_receive_workflow import PayReceiveWorkflow


def _build_fee_config():
    return {
        "to_customer_fees": BookRealAmountData.get_customer_standard_fees(),
        "to_supplier_fees": BookRealAmountData.get_supplier_standard_fees(),
    }


@pytest.mark.order_pay_receive1
class TestOrderPayReceive1PayableAccount:

    @allure.severity("critical")
    def test_order_pay_receive1_payable_account(self):
        bl_no = generate_bl_no(101)

        with allure.step("执行完整订单流程，运行至应付对账节点 payable"):
            result = PayReceiveWorkflow.run(
                stop_at="payable",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：订单 1~12 前置流程全部完成"):
            _assert_link12_prerequisite_ok(result)

        with allure.step("校验：应付对账数据"):
            _assert_payable_account_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "payable"
