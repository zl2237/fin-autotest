"""
测试链路 24：订单+应收（receive_pay），审核生成开票申请
执行顺序：订单 1~12 步 + 应收 1~4 步
前置条件：应收 3 步完成
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
    _assert_receive_invoice_batch_audit_ok,
)

def _build_fee_config():
    return {
        "to_customer_fees": BookRealAmountData.get_customer_standard_fees(),
        "to_supplier_fees": BookRealAmountData.get_supplier_standard_fees(),
    }

@pytest.mark.order_receive_pay4
class TestOrderReceivePay4InvoiceBatchAudit:

    @allure.severity("critical")
    def test_order_receive_pay4_invoice_batch_audit(self):
        bl_no = generate_bl_no(204)

        with allure.step("执行完整订单流程，运行至审核生成开票申请节点 invoice_batch_audit"):
            result = ReceivePayWorkflow.run(
                stop_at="invoice_batch_audit",
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

        with allure.step("校验：应收开票批次审核通过"):
            _assert_receive_invoice_batch_audit_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "invoice_batch_audit"