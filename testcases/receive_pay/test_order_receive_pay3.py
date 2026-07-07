"""
测试链路 23：订单+应收（receive_pay），发起应收开票批次申请
执行顺序：订单 1~12 步 + 应收 1~3 步
前置条件：应收 2 步完成
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
    _assert_receive_invoice_apply_ok,
)

def _build_fee_config():
    return {
        "to_customer_fees": BookRealAmountData.get_customer_standard_fees(),
        "to_supplier_fees": BookRealAmountData.get_supplier_standard_fees(),
    }

@pytest.mark.order_receive_pay3
class TestOrderReceivePay3InvoiceBatch:

    @allure.severity("critical")
    def test_order_receive_pay3_invoice_batch(self):
        bl_no = generate_bl_no(203)

        with allure.step("执行完整订单流程，运行至应收开票批次节点 invoice_batch"):
            result = ReceivePayWorkflow.run(
                stop_at="invoice_batch",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：订单 1~12 前置流程全部完成"):
            _assert_link12_prerequisite_ok(result)

        with allure.step("校验：应收对账批次数据"):
            _assert_receive_account_ok(result)

        with allure.step("校验：确认应收对账结果"):
            _assert_confirm_receive_ok(result)

        with allure.step("校验：应收开票申请批次数据"):
            _assert_receive_invoice_apply_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "invoice_batch"