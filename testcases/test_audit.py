"""
链路测试 - 审批（link7~10）

  link7  - 资产推送审批（录费用后自动执行）
  link8  - 订单锁定审批
  link9  - 未放款开票申请审批
  link10 - 供应商垫付申请审批
"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from data.order import BookRealAmountData, generate_bl_no


def _build_fee_config():
    """构造 fee_configs[0]，供 link7~10 复用。"""
    return {
        'to_customer_fees': BookRealAmountData.get_customer_standard_fees(),
        'to_supplier_fees': BookRealAmountData.get_supplier_standard_fees(),
    }


def _assert_base_steps_ok(result):
    """link7~10 共用的基础步骤断言（创建/分发/生成子订单/录费用/资产推送审批）。"""
    assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'
    assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'
    gen_data = result['generate_sub_data']
    assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'
    assert len(result['record_fee_results']) == 1, f'录费用应有1次调用，实际 {len(result["record_fee_results"])}'
    fee_1 = result['record_fee_results'][0]
    assert fee_1['resp'].status_code == 200, f'录费用 HTTP 状态码异常: {fee_1["resp"].status_code}'
    assert fee_1['data']['code'] == 200, f'录费用失败: {fee_1["data"]}'
    assert fee_1.get('audit_send_resp') is not None, '资产推送发起审批结果不应为空'
    assert fee_1['audit_send_resp'].status_code == 200, f'发起审批 HTTP 状态码异常'
    assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
    assert fee_1.get('audit_id'), 'audit_id 不应为空'
    assert fee_1['audit_approve_resp'].status_code == 200, f'审批通过 HTTP 状态码异常'
    assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'
    return fee_1


def _assert_order_lock_ok(result):
    """link8+ 共用的订单锁定审批断言。"""
    lock_result = result['order_lock_result']
    assert lock_result is not None, '订单锁定审批结果不应为空'
    assert lock_result['container'], '箱型信息不应为空'
    assert lock_result['send_resp'].status_code == 200, f'订单锁定发起 HTTP 状态码异常'
    assert lock_result['send_data']['code'] == 200, f'订单锁定发起失败: {lock_result["send_data"]}'
    assert lock_result.get('audit_id'), '订单锁定 audit_id 不应为空'
    assert lock_result['approve_resp'].status_code == 200, f'订单锁定审批通过 HTTP 状态码异常'
    assert lock_result['approve_data']['code'] == 200, f'订单锁定审批通过失败: {lock_result["approve_data"]}'


# =============================================================================
# 链路7：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批
# =============================================================================
@pytest.mark.link7
class TestLink7RecordAudit:
    """链路7：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批"""

    @allure.feature("链路测试")
    @allure.story("链路7：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批")
    @allure.severity("critical")
    @allure.title("链路7：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批")
    def test_link7_record_audit(self):
        """验证：完整链路（包含资产推送审批），链路停在 record_audit 阶段"""
        bl_no = generate_bl_no(7)

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='record_audit',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：基础步骤全部成功'):
            _assert_base_steps_ok(result)

        with allure.step('断言：链路停在 record_audit 阶段'):
            assert result['stop_at'] == 'record_audit'

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
            assert '发起审批(1)' in step_names
            assert '查询审批ID(1)' in step_names
            assert '审批通过(1)' in step_names


# =============================================================================
# 链路8：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批
# =============================================================================
@pytest.mark.link8
class TestLink8OrderLock:
    """链路8：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批"""

    @allure.feature("链路测试")
    @allure.story("链路8：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批")
    @allure.severity("critical")
    @allure.title("链路8：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批")
    def test_link8_order_lock(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批），链路停在 order_lock 阶段"""
        bl_no = generate_bl_no(8)

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='order_lock',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：基础步骤全部成功'):
            _assert_base_steps_ok(result)

        with allure.step('断言：订单锁定审批成功'):
            _assert_order_lock_ok(result)

        with allure.step('断言：链路停在 order_lock 阶段'):
            assert result['stop_at'] == 'order_lock'

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
            assert '发起审批(1)' in step_names
            assert '查询审批ID(1)' in step_names
            assert '审批通过(1)' in step_names
            assert '获取箱型信息' in step_names
            assert '发起订单锁定审批' in step_names
            assert '查询订单锁定审批ID' in step_names
            assert '订单锁定审批通过' in step_names


# =============================================================================
# 链路9：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批
# =============================================================================
@pytest.mark.link9
class TestLink9InvoiceApply:
    """链路9：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批"""

    @allure.feature("链路测试")
    @allure.story("链路9：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批")
    @allure.severity("critical")
    @allure.title("链路9：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批")
    def test_link9_invoice_apply(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批），链路停在 invoice_apply 阶段"""
        bl_no = generate_bl_no(9)

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_apply',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：基础步骤全部成功'):
            _assert_base_steps_ok(result)

        with allure.step('断言：订单锁定审批成功'):
            _assert_order_lock_ok(result)

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None, '未放款开票申请审批结果不应为空'
            assert invoice_result['send_resp'].status_code == 200, f'未放款开票申请发起 HTTP 状态码异常'
            assert invoice_result['send_data']['code'] == 200, f'未放款开票申请发起失败: {invoice_result["send_data"]}'
            assert invoice_result.get('audit_id'), '未放款开票申请 audit_id 不应为空'
            assert invoice_result['approve_resp'].status_code == 200, f'未放款开票申请审批通过 HTTP 状态码异常'
            assert invoice_result['approve_data']['code'] == 200, f'未放款开票申请审批通过失败: {invoice_result["approve_data"]}'

        with allure.step('断言：链路停在 invoice_apply 阶段'):
            assert result['stop_at'] == 'invoice_apply'

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
            assert '发起审批(1)' in step_names
            assert '查询审批ID(1)' in step_names
            assert '审批通过(1)' in step_names
            assert '获取箱型信息' in step_names
            assert '发起订单锁定审批' in step_names
            assert '查询订单锁定审批ID' in step_names
            assert '订单锁定审批通过' in step_names
            assert '发起未放款开票申请审批' in step_names
            assert '查询未放款开票申请审批ID' in step_names
            assert '未放款开票申请审批通过' in step_names


# =============================================================================
# 链路10：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批
# =============================================================================
@pytest.mark.link10
class TestLink10SupplierAdvance:
    """链路10：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批"""

    @allure.feature("链路测试")
    @allure.story("链路10：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批")
    @allure.severity("critical")
    @allure.title("链路10：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批")
    def test_link10_supplier_advance(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批），链路停在 supplier_advance 阶段"""
        bl_no = generate_bl_no(10)

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批→供应商垫付申请审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='supplier_advance',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：基础步骤全部成功'):
            _assert_base_steps_ok(result)

        with allure.step('断言：订单锁定审批成功'):
            _assert_order_lock_ok(result)

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None, '未放款开票申请审批结果不应为空'
            assert invoice_result['send_resp'].status_code == 200, f'未放款开票申请发起 HTTP 状态码异常'
            assert invoice_result['send_data']['code'] == 200, f'未放款开票申请发起失败: {invoice_result["send_data"]}'
            assert invoice_result.get('audit_id'), '未放款开票申请 audit_id 不应为空'
            assert invoice_result['approve_resp'].status_code == 200, f'未放款开票申请审批通过 HTTP 状态码异常'
            assert invoice_result['approve_data']['code'] == 200, f'未放款开票申请审批通过失败: {invoice_result["approve_data"]}'

        with allure.step('断言：供应商垫付申请审批成功'):
            advance_result = result['supplier_advance_result']
            assert advance_result is not None, '供应商垫付申请审批结果不应为空'
            assert advance_result['send_resp'].status_code == 200, f'供应商垫付申请发起 HTTP 状态码异常'
            assert advance_result['send_data']['code'] == 200, f'供应商垫付申请发起失败: {advance_result["send_data"]}'
            assert advance_result.get('audit_id'), '供应商垫付申请 audit_id 不应为空'
            assert advance_result['approve_resp'].status_code == 200, f'供应商垫付申请审批通过 HTTP 状态码异常'
            assert advance_result['approve_data']['code'] == 200, f'供应商垫付申请审批通过失败: {advance_result["approve_data"]}'

        with allure.step('断言：链路停在 supplier_advance 阶段'):
            assert result['stop_at'] == 'supplier_advance'

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
            assert '发起审批(1)' in step_names
            assert '查询审批ID(1)' in step_names
            assert '审批通过(1)' in step_names
            assert '获取箱型信息' in step_names
            assert '发起订单锁定审批' in step_names
            assert '查询订单锁定审批ID' in step_names
            assert '订单锁定审批通过' in step_names
            assert '发起未放款开票申请审批' in step_names
            assert '查询未放款开票申请审批ID' in step_names
            assert '未放款开票申请审批通过' in step_names
            assert '发起供应商垫付申请审批' in step_names
            assert '查询供应商垫付申请审批ID' in step_names
            assert '供应商垫付申请审批通过' in step_names
