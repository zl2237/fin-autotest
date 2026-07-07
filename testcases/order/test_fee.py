"""
链路测试 - 费用（link6）

  link6 - 录费用
"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no


# =============================================================================
# 链路6：录费用
# =============================================================================
@pytest.mark.order6
class TestOrder6RecordFee:
    """链路6：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用"""

    @allure.feature("链路测试")
    @allure.story("链路6：录费用")
    @allure.severity("critical")
    @allure.title("链路6：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用")
    def test_link6_record_fee(self):
        """验证：完整链路（包含录费用），链路停在 record_fee 阶段"""
        bl_no = generate_bl_no(6)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用）'):
            result = OrderWorkflow.run(
                stop_at='record_fee',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        with allure.step('断言：新建成功'):
            assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'

        with allure.step('断言：分发成功'):
            assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'

        with allure.step('断言：生成子订单成功'):
            gen_data = result['generate_sub_data']
            assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

        with allure.step('断言：录费用成功'):
            assert len(result['record_fee_results']) == 1, f'录费用应有1次调用，实际 {len(result["record_fee_results"])}'
            fee_1 = result['record_fee_results'][0]
            assert fee_1['resp'].status_code == 200, f'录费用 HTTP 状态码异常: {fee_1["resp"].status_code}'
            assert fee_1['data']['code'] == 200, f'录费用失败: {fee_1["data"]}'

        with allure.step('断言：链路停在 record_fee 阶段'):
            assert result['stop_at'] == 'record_fee'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            assert '新建订单' in step_names
            assert '按提单号查询' in step_names
            assert '分发订单' in step_names
            assert '查询订单' in step_names
            assert '暂存订单' in step_names
            assert '查询订单（暂存后）' in step_names
            assert '提交订单' in step_names
            assert '查询订单（提交后）' in step_names
            assert '生成子订单' in step_names
            assert '录费用(1)' in step_names
