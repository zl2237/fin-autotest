"""
测试链路 25：订单+应付（pay_receive），完整流程
执行顺序：订单 1~12 步 + 应付 21~22 步
前置条件：订单 12 步完成
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no
from testcases.pay_receive.helpers import _build_fee_config, _assert_audit_and_fee_doc_ok, _assert_receive_account_ok, _assert_confirm_receive_ok


@pytest.mark.order_pay_receive13
class TestOrderPayReceive13ReceiveWriteoff:

    @allure.severity("critical")
    def test_order_pay_receive13_receive_writeoff(self):
        bl_no = generate_bl_no(113)

        with allure.step("执行完整订单流程，运行至应收核销节点 receive_writeoff"):
            result = PayReceiveWorkflow.run(
                stop_at="receive_writeoff",
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step("校验：审核及费用单据信息"):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step("校验：应收账户数据"):
            _assert_receive_account_ok(result)

        with allure.step("校验：应收发票上传接口返回正常"):
            upload_result = result["invoice_upload_result"]
            assert upload_result is not None
            assert upload_result["add_resp"].status_code == 200
            assert upload_result["add_data"].get("code") == 200
            assert upload_result.get("receive_invoice_id")
            assert upload_result["alloc_resp"].status_code == 200
            assert upload_result["alloc_data"].get("code") == 200

        with allure.step("校验：应收核销相关接口返回正常"):
            writeoff_result = result["receive_writeoff_result"]
            assert writeoff_result is not None
            assert writeoff_result["fee_take_page_resp"].status_code == 200
            assert writeoff_result["fee_take_page_data"].get("code") == 200
            order_fee_real_id_list = writeoff_result.get("order_fee_real_id_list", [])
            assert order_fee_real_id_list
            writeoff_object = writeoff_result.get("writeoff_object", [])
            assert writeoff_object
            assert writeoff_result["writeoff_batch_resp"].status_code == 200
            assert writeoff_result["writeoff_batch_data"].get("code") == 200
            assert writeoff_result["writeoff_batch_data"].get("msg") == "成功"

        with allure.step("校验流程终止节点"):
            assert result["stop_at"] == "receive_writeoff"