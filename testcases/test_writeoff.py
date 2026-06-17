"""
链路测试 - 应收核销（link18）

  link18 - 应收核销（feeTakePage + writeoffBatch）
"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from data.order import BookRealAmountData, generate_bl_no


# =============================================================================
# 链路18：新建...发票上传与登记 → 应收核销
# =============================================================================
@pytest.mark.link18
class TestLink18ReceiveWriteoff:
    """链路18：新建 → ... → 发票上传与登记 → 应收核销"""

    @allure.feature("链路测试")
    @allure.story("链路18：应收核销")
    @allure.severity("critical")
    @allure.title("链路18：发票上传与登记 → 应收核销（feeTakePage + writeoffBatch）")
    def test_link18_receive_writeoff(self):
        """验证：完整链路（LINK17 + 应收核销），链路停在 receive_writeoff 阶段"""
        bl_no = generate_bl_no(18)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→发票上传与登记→应收核销）'):
            result = OrderWorkflow.full_flow(
                stop_at='receive_writeoff',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK17 步骤断言 ----------

        with allure.step('断言：发票上传与登记结果存在'):
            upload_result = result['invoice_upload_result']
            assert upload_result is not None, 'invoice_upload_result 不应为空'

        with allure.step('断言：invoiceAdd 上传发票成功'):
            add_data = upload_result['add_data']
            assert upload_result['add_resp'].status_code == 200
            assert add_data.get('code') == 200, f'invoiceAdd 上传失败: {add_data}'
            assert add_data.get('msg') == '成功', f'invoiceAdd msg 不为"成功": {add_data.get("msg")}'
            assert upload_result.get('receive_invoice_id'), f'receive_invoice_id 不应为空: {upload_result}'

        with allure.step('断言：applyPage 获取发票申请ID成功'):
            apply_page_data = upload_result['apply_page_data']
            assert upload_result['apply_page_resp'].status_code == 200
            assert apply_page_data.get('code') == 200, f'applyPage 查询失败: {apply_page_data}'
            assert apply_page_data.get('msg') == '成功', f'applyPage msg 不为"成功": {apply_page_data.get("msg")}'
            assert upload_result.get('receive_invoice_apply_id'), f'receive_invoice_apply_id 不应为空: {upload_result}'

        with allure.step('断言：allocationInvoiceFee 登记发票成功'):
            alloc_data = upload_result['alloc_data']
            assert upload_result['alloc_resp'].status_code == 200
            assert alloc_data.get('code') == 200, f'allocationInvoiceFee 登记失败: {alloc_data}'
            assert alloc_data.get('msg') == '成功', f'allocationInvoiceFee msg 不为"成功": {alloc_data.get("msg")}'

        # ---------- LINK18 应收核销断言 ----------

        with allure.step('断言：应收核销结果存在'):
            writeoff_result = result['receive_writeoff_result']
            assert writeoff_result is not None, 'receive_writeoff_result 不应为空'

        with allure.step('断言：feeTakePage 查询应收核销费用列表成功'):
            fee_take_page_resp = writeoff_result['fee_take_page_resp']
            fee_take_page_data = writeoff_result['fee_take_page_data']
            assert fee_take_page_resp.status_code == 200, f'HTTP 状态码异常: {fee_take_page_resp.status_code}'
            assert fee_take_page_data.get('code') == 200, f'feeTakePage 查询失败: {fee_take_page_data}'
            assert fee_take_page_data.get('msg') == '成功', f'feeTakePage msg 不为"成功": {fee_take_page_data.get("msg")}'

        with allure.step('断言：order_fee_real_id_list 非空'):
            order_fee_real_id_list = writeoff_result.get('order_fee_real_id_list', [])
            assert order_fee_real_id_list, f'order_fee_real_id_list 不应为空: {fee_take_page_data}'

        with allure.step('断言：writeoff_object 非空'):
            writeoff_object = writeoff_result.get('writeoff_object', [])
            assert writeoff_object, 'writeoff_object 不应为空'
            for item in writeoff_object:
                assert item.get('order_fee_real_id'), f'writeoff_object 中存在 order_fee_real_id 为空的项: {item}'
                assert item.get('un_writeoff_amount') is not None, f'writeoff_object 中存在 un_writeoff_amount 为空的项: {item}'

        with allure.step('断言：writeoffBatch 应收核销成功'):
            writeoff_batch_resp = writeoff_result['writeoff_batch_resp']
            writeoff_batch_data = writeoff_result['writeoff_batch_data']
            assert writeoff_batch_resp.status_code == 200, f'HTTP 状态码异常: {writeoff_batch_resp.status_code}'
            assert writeoff_batch_data.get('code') == 200, f'writeoffBatch 失败: {writeoff_batch_data}'
            assert writeoff_batch_data.get('msg') == '成功', f'writeoffBatch msg 不为"成功": {writeoff_batch_data.get("msg")}'

        with allure.step('断言：链路停在 receive_writeoff 阶段'):
            assert result['stop_at'] == 'receive_writeoff'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '查询应收核销费用列表',
                '应收核销',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
