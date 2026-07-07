"""
测试链路 24：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no
from testcases.pay_receive.helpers import _build_fee_config, _assert_audit_and_fee_doc_ok, _assert_receive_account_ok, _assert_confirm_receive_ok


@pytest.mark.order_pay_receive12
class TestOrderPayReceive12InvoiceUpload:

    @allure.severity("critical")
    def test_order_pay_receive12_invoice_upload(self):
        bl_no = generate_bl_no(112)

        with allure.step("执行完整订单流程，运行至应收发票上传登记节点 invoice_upload"):
            result = PayReceiveWorkflow.run(
                stop_at="invoice_upload",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：审核及费用单据信息"):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step("校验：应收账户数据"):
            _assert_receive_account_ok(result)

        with allure.step("校验：确认应收对账结果"):
            _assert_confirm_receive_ok(result)

        with allure.step("校验：应收开票批次审核接口返回正常"):
            audit_result = result["invoice_batch_audit_result"]
            assert audit_result is not None
            assert audit_result["audit_query_resp"].status_code == 200
            assert audit_result["audit_query_data"].get("code") == 200
            assert audit_result["audit_execute_resp"].status_code == 200
            assert audit_result["audit_execute_data"].get("code") == 200

        with allure.step("校验：应收发票上传登记相关接口返回正常"):
            upload_result = result["invoice_upload_result"]
            assert upload_result is not None
            assert upload_result["add_resp"].status_code == 200
            assert upload_result["add_data"].get("code") == 200
            assert upload_result.get("receive_invoice_id")
            assert upload_result["apply_page_resp"].status_code == 200
            assert upload_result["apply_page_data"].get("code") == 200
            assert upload_result.get("receive_invoice_apply_id")
            assert upload_result["alloc_resp"].status_code == 200
            assert upload_result["alloc_data"].get("code") == 200

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "invoice_upload"