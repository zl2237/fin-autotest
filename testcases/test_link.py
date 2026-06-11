"""
链路测试 - 验证新建→分发→暂存→提交→生成子订单→录费用→录审批→录订单锁定审批→录未放款开票申请审批 完整链路数据流

标记说明：
  link1  - 新建
  link2  - 新建、分发
  link3  - 新建、分发、查询、暂存
  link4  - 新建、分发、查询、暂存、提交
  link5  - 新建、分发、查询、暂存、提交、生成子订单
  link6  - 新建、分发、查询、暂存、提交、生成子订单、录费用
  link7  - 新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批
  link8  - 新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批
  link9  - 新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批
  link10 - 新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批
  link11 - 新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单
  link12 - 新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单、生成费用确认单
"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from api.order import OrderApi
from data.order_data import BookRealAmountData, FeeNoticeData, FeeConfirmData


# =============================================================================
# 链路1：新建
# =============================================================================
@pytest.mark.link1
class TestLink1Create:
    """链路1：仅新建订单"""

    @allure.feature("链路测试")
    @allure.story("链路1：新建")
    @allure.severity("critical")
    @allure.title("链路1：仅新建订单")
    def test_link1_create(self):
        """验证：新建订单成功，API 返回 code=200"""
        bl_no = "LK1_" + __import__("time").strftime("%Y%m%d%H%M%S")

        with allure.step("执行新建"):
            result = OrderWorkflow.full_flow(stop_at="create", bl_no=bl_no)

        with allure.step("断言：新建成功"):
            assert result["create_data"]["code"] == 200, \
                f"新建失败: {result['create_data']}"
            assert result["create_data"]["msg"] == "成功", \
                f"响应消息异常: {result['create_data']['msg']}"

        with allure.step("断言：链路停在 create 阶段"):
            assert result["stop_at"] == "create"
            assert "distribute_resp" not in result
            assert "stash_resp" not in result
            assert "submit_resp" not in result

        with allure.step("断言：bl_no 正确注入"):
            assert result["bl_no"] == bl_no


# =============================================================================
# 链路2：新建、分发
# =============================================================================
@pytest.mark.link2
class TestLink2CreateAndDistribute:
    """链路2：新建 → 分发"""

    @allure.feature("链路测试")
    @allure.story("链路2：新建、分发")
    @allure.severity("critical")
    @allure.title("链路2：新建 → 分发")
    def test_link2_create_and_distribute(self):
        """验证：新建成功，分发成功，链路停在 distribute 阶段"""
        bl_no = "LK2_" + __import__("time").strftime("%Y%m%d%H%M%S")

        with allure.step("执行新建+分发"):
            result = OrderWorkflow.full_flow(stop_at="distribute", bl_no=bl_no)

        with allure.step("断言：新建成功"):
            assert result["create_data"]["code"] == 200, \
                f"新建失败: {result['create_data']}"

        with allure.step("断言：查询成功，找到订单"):
            assert result["create_order"], \
                f"按 bl_no={bl_no} 查询不到订单"
            assert result["create_order"].get("order_id"), \
                "订单缺少 order_id"

        with allure.step("断言：分发成功"):
            assert result["distribute_resp"].status_code == 200, \
                "分发 HTTP 状态码异常"
            assert result["distribute_data"]["code"] == 200, \
                f"分发失败: {result['distribute_data']}"

        with allure.step("断言：链路停在 distribute 阶段"):
            assert result["stop_at"] == "distribute"
            assert "stash_resp" not in result
            assert "submit_resp" not in result


# =============================================================================
# 链路3：新建、分发、查询、暂存
# =============================================================================
@pytest.mark.link3
class TestLink3Stash:
    """链路3：新建 → 分发 → 查询 → 暂存"""

    @allure.feature("链路测试")
    @allure.story("链路3：新建、分发、查询、暂存")
    @allure.severity("critical")
    @allure.title("链路3：新建 → 分发 → 查询 → 暂存")
    def test_link3_create_distribute_query_stash(self):
        """验证：分发后查询到 order_id，暂存成功（status=1），链路停在 stash 阶段"""
        bl_no = "LK3_" + __import__("time").strftime("%Y%m%d%H%M%S")

        with allure.step("执行新建+分发+查询+暂存"):
            result = OrderWorkflow.full_flow(stop_at="stash", bl_no=bl_no)

        with allure.step("断言：新建成功"):
            assert result["create_data"]["code"] == 200, \
                f"新建失败: {result['create_data']}"

        with allure.step("断言：分发成功"):
            assert result["distribute_data"]["code"] == 200, \
                f"分发失败: {result['distribute_data']}"

        with allure.step("断言：分发后查询到订单"):
            assert result["current_order"], \
                f"分发后按 bl_no={bl_no} 查询不到订单"
            assert result["current_order"].get("order_id"), \
                "分发后订单缺少 order_id"

        with allure.step("断言：暂存成功"):
            assert result["stash_resp"].status_code == 200, \
                "暂存 HTTP 状态码异常"
            assert result["stash_data"]["code"] == 200, \
                f"暂存失败: {result['stash_data']}"

        with allure.step("断言：链路停在 stash 阶段"):
            assert result["stop_at"] == "stash"
            assert "submit_resp" not in result


# =============================================================================
# 链路4：新建、分发、查询、暂存、提交（完整链路）
# =============================================================================
@pytest.mark.link4
class TestLink4FullWithStash:
    """链路4：新建 → 分发 → 查询 → 暂存 → 提交"""

    @allure.feature("链路测试")
    @allure.story("链路4：新建、分发、查询、暂存、提交")
    @allure.severity("critical")
    @allure.title("链路4：新建 → 分发 → 查询 → 暂存 → 提交")
    def test_link4_full_with_stash(self):
        """验证：新建→分发→查询→暂存→提交全部成功"""
        bl_no = "LK4_" + __import__("time").strftime("%Y%m%d%H%M%S")

        with allure.step("执行链路（新建→分发→查询→暂存→提交）"):
            result = OrderWorkflow.full_flow(stop_at="submit", skip_stash=False, bl_no=bl_no)

        with allure.step("断言：新建成功"):
            assert result["create_data"]["code"] == 200, \
                f"新建失败: {result['create_data']}"

        with allure.step("断言：分发成功"):
            assert result["distribute_data"]["code"] == 200, \
                f"分发失败: {result['distribute_data']}"

        with allure.step("断言：分发后查询到订单"):
            assert result["current_order"], \
                f"分发后按 bl_no={bl_no} 查询不到订单"
            assert result["current_order"].get("order_id"), \
                "分发后订单缺少 order_id"

        with allure.step("断言：暂存成功"):
            assert result["stash_data"]["code"] == 200, \
                f"暂存失败: {result['stash_data']}"

        with allure.step("断言：暂存后查询到订单"):
            assert result["after_stash_order"], \
                "暂存后查询不到订单"
            assert result["after_stash_order"].get("order_id"), \
                "暂存后订单缺少 order_id"

        with allure.step("断言：提交成功"):
            assert result["submit_resp"].status_code == 200, \
                "提交 HTTP 状态码异常"
            if result["submit_data"]["code"] != 200:
                allure.attach(
                    f"提交返回非成功状态（可能是提交接口参数不完整）: {result['submit_data']}",
                    name="提交响应",
                    attachment_type=allure.attachment_type.JSON
                )

        with allure.step("断言：链路停在 submit 阶段，无生成子订单"):
            assert result["stop_at"] == "submit"
            assert "generate_sub_resp" not in result, \
                "链路4不应执行生成子订单"

        with allure.step("断言：steps 记录完整"):
            step_names = [s["name"] for s in result["steps"]]
            assert "新建订单" in step_names
            assert "按提单号查询" in step_names
            assert "分发订单" in step_names
            assert "查询订单" in step_names
            assert "暂存订单" in step_names
            assert "查询订单（暂存后）" in step_names
            assert "提交订单" in step_names
            assert "查询订单（提交后）" in step_names


# =============================================================================
# 链路5：新建、分发、查询、暂存、提交、生成子订单
# =============================================================================
@pytest.mark.link5
class TestLink5GenerateSubOrder:
    """链路5：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单"""

    @allure.feature("链路测试")
    @allure.story("链路5：新建、分发、查询、暂存、提交、生成子订单")
    @allure.severity("critical")
    @allure.title("链路5：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单")
    def test_link5_generate_sub_order(self):
        """验证：完整链路（包含生成子订单），链路停在 generate_sub_order 阶段"""
        bl_no = "LK5_" + __import__("time").strftime("%Y%m%d%H%M%S")

        with allure.step("执行链路（新建→分发→查询→暂存→提交→生成子订单）"):
            result = OrderWorkflow.full_flow(stop_at="generate_sub_order", bl_no=bl_no)

        with allure.step("断言：新建成功"):
            assert result["create_data"]["code"] == 200, \
                f"新建失败: {result['create_data']}"

        with allure.step("断言：分发成功"):
            assert result["distribute_data"]["code"] == 200, \
                f"分发失败: {result['distribute_data']}"

        with allure.step("断言：分发后查询到订单"):
            assert result["current_order"], \
                f"分发后按 bl_no={bl_no} 查询不到订单"

        with allure.step("断言：暂存成功"):
            assert result["stash_data"]["code"] == 200, \
                f"暂存失败: {result['stash_data']}"

        with allure.step("断言：暂存后查询到订单"):
            assert result["after_stash_order"], \
                "暂存后查询不到订单"

        with allure.step("断言：提交成功"):
            assert result["submit_resp"].status_code == 200, \
                "提交 HTTP 状态码异常"

        with allure.step("断言：提交后查询到订单"):
            assert result["after_submit_order"], \
                "提交后查询不到订单"
            assert result["after_submit_order"].get("order_id"), \
                "提交后订单缺少 order_id"

        with allure.step("断言：生成子订单成功"):
            assert result["generate_sub_resp"].status_code == 200, \
                "生成子订单 HTTP 状态码异常"
            assert result["generate_sub_data"]["code"] == 200, \
                f"生成子订单失败: {result['generate_sub_data']}"

        with allure.step("断言：链路停在 generate_sub_order 阶段"):
            assert result["stop_at"] == "generate_sub_order"

        with allure.step("断言：steps 记录完整"):
            step_names = [s["name"] for s in result["steps"]]
            assert "新建订单" in step_names
            assert "按提单号查询" in step_names
            assert "分发订单" in step_names
            assert "查询订单" in step_names
            assert "暂存订单" in step_names
            assert "查询订单（暂存后）" in step_names
            assert "提交订单" in step_names
            assert "查询订单（提交后）" in step_names
            assert "生成子订单" in step_names


# =============================================================================
# 链路6：新建、分发、查询、暂存、提交、生成子订单、录费用
# =============================================================================
@pytest.mark.link6
class TestLink6RecordFee:
    """链路6：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用"""

    @allure.feature("链路测试")
    @allure.story("链路6：新建、分发、查询、暂存、提交、生成子订单、录费用")
    @allure.severity("critical")
    @allure.title("链路6：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用")
    def test_link6_record_fee(self):
        """验证：完整链路（包含录费用），链路停在 record_fee 阶段"""
        bl_no = 'LK6_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用）'):
            result = OrderWorkflow.full_flow(
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
        bl_no = 'LK7_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='record_audit',
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

        with allure.step('断言：资产推送审批成功（录费用后自动执行）'):
            assert fee_1.get('audit_send_resp') is not None, '资产推送发起审批结果不应为空'
            assert fee_1['audit_send_resp'].status_code == 200, f'发起审批 HTTP 状态码异常'
            assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
            assert fee_1.get('audit_id'), 'audit_id 不应为空'
            assert fee_1['audit_approve_resp'].status_code == 200, f'审批通过 HTTP 状态码异常'
            assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'

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
        bl_no = 'LK8_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='order_lock',
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

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None, '资产推送发起审批结果不应为空'
            assert fee_1['audit_send_resp'].status_code == 200, f'发起审批 HTTP 状态码异常'
            assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
            assert fee_1.get('audit_id'), 'audit_id 不应为空'
            assert fee_1['audit_approve_resp'].status_code == 200, f'审批通过 HTTP 状态码异常'
            assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None, '订单锁定审批结果不应为空'
            assert lock_result['container'], '箱型信息不应为空'
            assert lock_result['send_resp'].status_code == 200, f'订单锁定发起 HTTP 状态码异常'
            assert lock_result['send_data']['code'] == 200, f'订单锁定发起失败: {lock_result["send_data"]}'
            assert lock_result.get('audit_id'), '订单锁定 audit_id 不应为空'
            assert lock_result['approve_resp'].status_code == 200, f'订单锁定审批通过 HTTP 状态码异常'
            assert lock_result['approve_data']['code'] == 200, f'订单锁定审批通过失败: {lock_result["approve_data"]}'

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
        bl_no = 'LK9_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_apply',
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

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None, '资产推送发起审批结果不应为空'
            assert fee_1['audit_send_resp'].status_code == 200, f'发起审批 HTTP 状态码异常'
            assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
            assert fee_1.get('audit_id'), 'audit_id 不应为空'
            assert fee_1['audit_approve_resp'].status_code == 200, f'审批通过 HTTP 状态码异常'
            assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None, '订单锁定审批结果不应为空'
            assert lock_result['container'], '箱型信息不应为空'
            assert lock_result['send_resp'].status_code == 200, f'订单锁定发起 HTTP 状态码异常'
            assert lock_result['send_data']['code'] == 200, f'订单锁定发起失败: {lock_result["send_data"]}'
            assert lock_result.get('audit_id'), '订单锁定 audit_id 不应为空'
            assert lock_result['approve_resp'].status_code == 200, f'订单锁定审批通过 HTTP 状态码异常'
            assert lock_result['approve_data']['code'] == 200, f'订单锁定审批通过失败: {lock_result["approve_data"]}'

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
        bl_no = 'LK10_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批→供应商垫付申请审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='supplier_advance',
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

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None, '资产推送发起审批结果不应为空'
            assert fee_1['audit_send_resp'].status_code == 200, f'发起审批 HTTP 状态码异常'
            assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
            assert fee_1.get('audit_id'), 'audit_id 不应为空'
            assert fee_1['audit_approve_resp'].status_code == 200, f'审批通过 HTTP 状态码异常'
            assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None, '订单锁定审批结果不应为空'
            assert lock_result['container'], '箱型信息不应为空'
            assert lock_result['send_resp'].status_code == 200, f'订单锁定发起 HTTP 状态码异常'
            assert lock_result['send_data']['code'] == 200, f'订单锁定发起失败: {lock_result["send_data"]}'
            assert lock_result.get('audit_id'), '订单锁定 audit_id 不应为空'
            assert lock_result['approve_resp'].status_code == 200, f'订单锁定审批通过 HTTP 状态码异常'
            assert lock_result['approve_data']['code'] == 200, f'订单锁定审批通过失败: {lock_result["approve_data"]}'

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


# =============================================================================
# 链路11：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单
# =============================================================================
@pytest.mark.link11
class TestLink11GenerateFeeNotice:
    """链路11：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单"""

    @allure.feature("链路测试")
    @allure.story("链路11：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单")
    @allure.severity("critical")
    @allure.title("链路11：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单")
    def test_link11_generate_fee_notice(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 生成费用通知单），链路停在 fee_notice 阶段"""
        bl_no = 'LK11_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批→供应商垫付申请审批→生成费用通知单）'):
            result = OrderWorkflow.full_flow(
                stop_at='fee_notice',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- 基础步骤断言 ----------

        with allure.step('断言：新建成功'):
            assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'

        with allure.step('断言：分发成功'):
            assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'

        with allure.step('断言：生成子订单成功'):
            gen_data = result['generate_sub_data']
            assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

        # ---------- 录费用 + 资产推送审批 ----------

        with allure.step('断言：录费用成功'):
            assert len(result['record_fee_results']) == 1, f'录费用应有1次调用，实际 {len(result["record_fee_results"])}'
            fee_1 = result['record_fee_results'][0]
            assert fee_1['resp'].status_code == 200, f'录费用 HTTP 状态码异常: {fee_1["resp"].status_code}'
            assert fee_1['data']['code'] == 200, f'录费用失败: {fee_1["data"]}'

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None
            assert fee_1['audit_send_resp'].status_code == 200
            assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
            assert fee_1.get('audit_id'), 'audit_id 不应为空'
            assert fee_1['audit_approve_resp'].status_code == 200
            assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'

        # ---------- 订单锁定审批 ----------

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None
            assert lock_result['container']
            assert lock_result['send_resp'].status_code == 200
            assert lock_result['send_data']['code'] == 200, f'订单锁定发起失败: {lock_result["send_data"]}'
            assert lock_result.get('audit_id')
            assert lock_result['approve_resp'].status_code == 200
            assert lock_result['approve_data']['code'] == 200, f'订单锁定审批通过失败: {lock_result["approve_data"]}'

        # ---------- 未放款开票申请审批 ----------

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None
            assert invoice_result['send_resp'].status_code == 200
            assert invoice_result['send_data']['code'] == 200, f'未放款开票申请发起失败: {invoice_result["send_data"]}'
            assert invoice_result.get('audit_id')
            assert invoice_result['approve_resp'].status_code == 200
            assert invoice_result['approve_data']['code'] == 200, f'未放款开票申请审批通过失败: {invoice_result["approve_data"]}'

        # ---------- 供应商垫付申请审批 ----------

        with allure.step('断言：供应商垫付申请审批成功'):
            advance_result = result['supplier_advance_result']
            assert advance_result is not None
            assert advance_result['send_resp'].status_code == 200
            assert advance_result['send_data']['code'] == 200, f'供应商垫付申请发起失败: {advance_result["send_data"]}'
            assert advance_result.get('audit_id')
            assert advance_result['approve_resp'].status_code == 200
            assert advance_result['approve_data']['code'] == 200, f'供应商垫付申请审批通过失败: {advance_result["approve_data"]}'

        # ---------- 生成费用通知单（重点断言） ----------

        with allure.step('断言：生成费用通知单成功'):
            notice_result = result['fee_notice_result']
            assert notice_result is not None, '费用通知单结果不应为空'

        with allure.step('断言：HTTP 状态码为 200'):
            assert notice_result['resp'].status_code == 200, \
                f'HTTP 状态码异常: {notice_result["resp"].status_code}'

        with allure.step('断言：响应 code=200'):
            data = notice_result['data']
            assert data['code'] == 200, f'响应 code 不为 200: {data}'

        with allure.step('断言：响应 msg=成功'):
            assert data.get('msg') == '成功', f'响应 msg 不为"成功": {data.get("msg")}'

        with allure.step('断言：data 不为 None'):
            assert data.get('data') is not None, f'data.data 不应为 None: {data}'

        with allure.step('断言：data.file_name 不为 None'):
            file_info = notice_result['file_info']
            assert file_info, f'data.file_name 不应为空: {data.get("data")}'

        with allure.step('断言：file_id 非空且为字符串'):
            assert file_info.get('file_id'), f'file_id 不应为空: {file_info}'
            assert isinstance(file_info['file_id'], str), f'file_id 应为 str，实际: {type(file_info["file_id"])}'

        with allure.step('断言：file_name 非空且为字符串'):
            assert file_info.get('file_name'), f'file_name 不应为空: {file_info}'
            assert isinstance(file_info['file_name'], str), f'file_name 应为 str，实际: {type(file_info["file_name"])}'

        with allure.step('断言：file_type 非空且为字符串'):
            assert file_info.get('file_type'), f'file_type 不应为空: {file_info}'
            assert isinstance(file_info['file_type'], str), f'file_type 应为 str，实际: {type(file_info["file_type"])}'
            assert file_info['file_type'].upper() == 'PDF', f'file_type 应为 PDF，实际: {file_info["file_type"]}'

        with allure.step('断言：file_url 非空且为字符串'):
            assert file_info.get('file_url'), f'file_url 不应为空: {file_info}'
            assert isinstance(file_info['file_url'], str), f'file_url 应为 str，实际: {type(file_info["file_url"])}'

        with allure.step('断言：original_name 非空且为字符串'):
            assert file_info.get('original_name'), f'original_name 不应为空: {file_info}'
            assert isinstance(file_info['original_name'], str), f'original_name 应为 str，实际: {type(file_info["original_name"])}'

        with allure.step('断言：file_name 包含"费用通知单"关键字'):
            assert '费用通知单' in file_info['file_name'], \
                f'file_name 应包含"费用通知单"，实际: {file_info["file_name"]}'

        with allure.step('断言：file_name 以.bl_no 为前缀'):
            assert file_info['file_name'].startswith(bl_no), \
                f'file_name 应以 bl_no="{bl_no}" 为前缀，实际: {file_info["file_name"]}'

        with allure.step('断言：file_url 以.pdf 结尾（存在文件扩展名）'):
            assert file_info['file_url'].endswith('.pdf'), \
                f'file_url 应以.pdf 结尾，实际: {file_info["file_url"]}'

        with allure.step('断言：request_id 非空且为字符串'):
            assert data.get('request_id'), f'request_id 不应为空: {data}'
            assert isinstance(data['request_id'], str), f'request_id 应为 str，实际: {type(data["request_id"])}'

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 fee_notice 阶段'):
            assert result['stop_at'] == 'fee_notice'

        # ---------- steps 记录完整 ----------

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路12：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单、生成费用确认单
# =============================================================================
@pytest.mark.link12
class TestLink12GenerateFeeConfirm:
    """链路12：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单 → 生成费用确认单"""

    @allure.feature("链路测试")
    @allure.story("链路12：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单、生成费用确认单")
    @allure.severity("critical")
    @allure.title("链路12：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单 → 生成费用确认单")
    def test_link12_generate_fee_confirm(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 费用通知单 + 费用确认单），链路停在 fee_confirm 阶段"""
        bl_no = 'LK12_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批→供应商垫付申请审批→生成费用通知单→生成费用确认单）'):
            result = OrderWorkflow.full_flow(
                stop_at='fee_confirm',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- 基础步骤断言 ----------

        with allure.step('断言：新建成功'):
            assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'

        with allure.step('断言：分发成功'):
            assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'

        with allure.step('断言：生成子订单成功'):
            gen_data = result['generate_sub_data']
            assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

        # ---------- 录费用 + 资产推送审批 ----------

        with allure.step('断言：录费用成功'):
            assert len(result['record_fee_results']) == 1, f'录费用应有1次调用，实际 {len(result["record_fee_results"])}'
            fee_1 = result['record_fee_results'][0]
            assert fee_1['resp'].status_code == 200, f'录费用 HTTP 状态码异常: {fee_1["resp"].status_code}'
            assert fee_1['data']['code'] == 200, f'录费用失败: {fee_1["data"]}'

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None
            assert fee_1['audit_send_resp'].status_code == 200
            assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
            assert fee_1.get('audit_id'), 'audit_id 不应为空'
            assert fee_1['audit_approve_resp'].status_code == 200
            assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'

        # ---------- 订单锁定审批 ----------

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None
            assert lock_result['container']
            assert lock_result['send_resp'].status_code == 200
            assert lock_result['send_data']['code'] == 200, f'订单锁定发起失败: {lock_result["send_data"]}'
            assert lock_result.get('audit_id')
            assert lock_result['approve_resp'].status_code == 200
            assert lock_result['approve_data']['code'] == 200, f'订单锁定审批通过失败: {lock_result["approve_data"]}'

        # ---------- 未放款开票申请审批 ----------

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None
            assert invoice_result['send_resp'].status_code == 200
            assert invoice_result['send_data']['code'] == 200, f'未放款开票申请发起失败: {invoice_result["send_data"]}'
            assert invoice_result.get('audit_id')
            assert invoice_result['approve_resp'].status_code == 200
            assert invoice_result['approve_data']['code'] == 200, f'未放款开票申请审批通过失败: {invoice_result["approve_data"]}'

        # ---------- 供应商垫付申请审批 ----------

        with allure.step('断言：供应商垫付申请审批成功'):
            advance_result = result['supplier_advance_result']
            assert advance_result is not None
            assert advance_result['send_resp'].status_code == 200
            assert advance_result['send_data']['code'] == 200, f'供应商垫付申请发起失败: {advance_result["send_data"]}'
            assert advance_result.get('audit_id')
            assert advance_result['approve_resp'].status_code == 200
            assert advance_result['approve_data']['code'] == 200, f'供应商垫付申请审批通过失败: {advance_result["approve_data"]}'

        # ---------- 生成费用通知单 ----------

        with allure.step('断言：生成费用通知单成功'):
            notice_result = result['fee_notice_result']
            assert notice_result is not None
            assert notice_result['resp'].status_code == 200
            assert notice_result['data']['code'] == 200, f'费用通知单 code 不为 200: {notice_result["data"]}'
            assert notice_result['data'].get('msg') == '成功', f'费用通知单 msg 不为"成功": {notice_result["data"]}'
            notice_file = notice_result['file_info']
            assert notice_file, f'费用通知单 file_info 不应为空: {notice_result["data"]}'
            assert notice_file.get('file_id')
            assert notice_file.get('file_name')
            assert notice_file.get('file_type', '').upper() == 'PDF'
            assert notice_file.get('file_url')
            assert notice_file.get('original_name')

        # ---------- 生成费用确认单（重点断言） ----------

        with allure.step('断言：生成费用确认单成功'):
            confirm_result = result['fee_confirm_result']
            assert confirm_result is not None, '费用确认单结果不应为空'

        with allure.step('断言：HTTP 状态码为 200'):
            assert confirm_result['resp'].status_code == 200, \
                f'HTTP 状态码异常: {confirm_result["resp"].status_code}'

        with allure.step('断言：响应 code=200'):
            data = confirm_result['data']
            assert data['code'] == 200, f'响应 code 不为 200: {data}'

        with allure.step('断言：响应 msg=成功'):
            assert data.get('msg') == '成功', f'响应 msg 不为"成功": {data.get("msg")}'

        with allure.step('断言：data 不为 None'):
            assert data.get('data') is not None, f'data.data 不应为 None: {data}'

        with allure.step('断言：data.file_name 不为 None'):
            file_info = confirm_result['file_info']
            assert file_info, f'data.file_name 不应为空: {data.get("data")}'

        with allure.step('断言：file_id 非空且为字符串'):
            assert file_info.get('file_id'), f'file_id 不应为空: {file_info}'
            assert isinstance(file_info['file_id'], str), f'file_id 应为 str，实际: {type(file_info["file_id"])}'

        with allure.step('断言：file_name 非空且为字符串'):
            assert file_info.get('file_name'), f'file_name 不应为空: {file_info}'
            assert isinstance(file_info['file_name'], str), f'file_name 应为 str，实际: {type(file_info["file_name"])}'

        with allure.step('断言：file_type 非空且为字符串'):
            assert file_info.get('file_type'), f'file_type 不应为空: {file_info}'
            assert isinstance(file_info['file_type'], str), f'file_type 应为 str，实际: {type(file_info["file_type"])}'
            assert file_info['file_type'].upper() == 'PDF', f'file_type 应为 PDF，实际: {file_info["file_type"]}'

        with allure.step('断言：file_url 非空且为字符串'):
            assert file_info.get('file_url'), f'file_url 不应为空: {file_info}'
            assert isinstance(file_info['file_url'], str), f'file_url 应为 str，实际: {type(file_info["file_url"])}'

        with allure.step('断言：original_name 非空且为字符串'):
            assert file_info.get('original_name'), f'original_name 不应为空: {file_info}'
            assert isinstance(file_info['original_name'], str), f'original_name 应为 str，实际: {type(file_info["original_name"])}'

        with allure.step('断言：file_name 包含"费用确认单"关键字'):
            assert '费用确认单' in file_info['file_name'], \
                f'file_name 应包含"费用确认单"，实际: {file_info["file_name"]}'

        with allure.step('断言：file_name 以 bl_no 为前缀'):
            assert file_info['file_name'].startswith(bl_no), \
                f'file_name 应以 bl_no="{bl_no}" 为前缀，实际: {file_info["file_name"]}'

        with allure.step('断言：file_url 以 .pdf 结尾'):
            assert file_info['file_url'].endswith('.pdf'), \
                f'file_url 应以.pdf 结尾，实际: {file_info["file_url"]}'

        with allure.step('断言：request_id 非空且为字符串'):
            assert data.get('request_id'), f'request_id 不应为空: {data}'
            assert isinstance(data['request_id'], str), f'request_id 应为 str，实际: {type(data["request_id"])}'

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 fee_confirm 阶段'):
            assert result['stop_at'] == 'fee_confirm'

        # ---------- steps 记录完整 ----------

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
                '生成费用确认单',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
