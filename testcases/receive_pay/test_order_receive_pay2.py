"""
测试链路 22：订单+应收（receive_pay），确认应收对账批次
执行顺序：订单 1~12 步 + 应收 1~2 步
前置条件：应收 1 步完成
"""

import allure
import pytest

from data.order import BookRealAmountData
from utils import generate_bl_no
from workflows.receive_pay_workflow import ReceivePayWorkflow

from testcases.receive_pay.helpers import (
    _assert_confirm_receive_ok,
    _assert_link12_prerequisite_ok,
    _assert_receive_account_ok,
)

def _build_fee_config():
    return {
        "to_customer_fees": BookRealAmountData.get_customer_standard_fees(),
        "to_supplier_fees": BookRealAmountData.get_supplier_standard_fees(),
    }

@pytest.mark.order_receive_pay2
class TestOrderReceivePay2ConfirmAccount:

    @allure.severity("critical")
    def test_order_receive_pay2_confirm_account(self):
        bl_no = generate_bl_no(202)

        with allure.step("执行完整订单流程，运行至确认应收节点 confirm_account"):
            result = ReceivePayWorkflow.run(
                stop_at="confirm_account",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：订单 1~12 前置流程全部完成"):
            _assert_link12_prerequisite_ok(result)

        with allure.step("校验：应收对账批次数据"):
            _assert_receive_account_ok(result)

        with allure.step("校验：确认应收对账结果"):
            _assert_confirm_receive_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "confirm_account"