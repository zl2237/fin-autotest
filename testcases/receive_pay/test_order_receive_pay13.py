"""
测试链路 33：订单+应收（receive_pay），付款单核销
执行顺序：订单 1~12 步 + 应收 1~6 步 + 应付 1~7 步
前置条件：应付发票已上传登记
"""

import allure
import pytest

from data.order import BookRealAmountData
from utils import generate_bl_no
from workflows.receive_pay_workflow import ReceivePayWorkflow

from testcases.receive_pay.helpers import (
    _assert_audit_and_fee_doc_ok,
    _assert_confirm_payable_ok,
    _assert_confirm_receive_ok,
    _assert_pay_demand_audit_ok,
    _assert_pay_demand_ok,
    _assert_pay_writeoff_ok,
    _assert_payable_account_ok,
    _assert_payable_invoice_apply_ok,
    _assert_receive_account_ok,
    _assert_receive_invoice_apply_ok,
    _assert_receive_invoice_batch_audit_ok,
    _assert_receive_invoice_register_ok,
    _assert_receive_writeoff_ok,
)

def _build_fee_config():
    return {
        "to_customer_fees": BookRealAmountData.get_customer_standard_fees(),
        "to_supplier_fees": BookRealAmountData.get_supplier_standard_fees(),
    }

@pytest.mark.order_receive_pay13
class TestOrderReceivePay13PayWriteoff:

    @allure.severity("critical")
    def test_order_receive_pay13_pay_writeoff(self):
        bl_no = generate_bl_no(213)

        with allure.step("执行完整订单流程，运行至付款单核销节点 pay_writeoff"):
            result = ReceivePayWorkflow.run(
                stop_at="pay_writeoff",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：审核及费用单据信息"):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step("校验：应收对账批次数据"):
            _assert_receive_account_ok(result)

        with allure.step("校验：确认应收对账结果"):
            _assert_confirm_receive_ok(result)

        with allure.step("校验：应收开票申请批次数据"):
            _assert_receive_invoice_apply_ok(result)

        with allure.step("校验：应收开票批次审核通过"):
            _assert_receive_invoice_batch_audit_ok(result)

        with allure.step("校验：应收发票登记数据"):
            _assert_receive_invoice_register_ok(result)

        with allure.step("校验：应收核销相关接口返回正常"):
            _assert_receive_writeoff_ok(result)

        with allure.step("校验：应付对账数据"):
            _assert_payable_account_ok(result)

        with allure.step("校验：确认应付对账结果"):
            _assert_confirm_payable_ok(result)

        with allure.step("校验：发起付款需求"):
            _assert_pay_demand_ok(result)

        with allure.step("校验：发起应付开票批次申请"):
            _assert_payable_invoice_apply_ok(result)

        with allure.step("校验：审核生成付款单"):
            _assert_pay_demand_audit_ok(result)

        with allure.step("校验：付款单核销"):
            _assert_pay_writeoff_ok(result)

        with allure.step("校验：付款单核销"):
            _assert_pay_writeoff_ok(result)

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "pay_writeoff"