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
  link13 - 新建...发起应收对账批次
  link14 - 新建...发起应收对账批次、确认应收对账
  link15 - 新建...确认应收对账、发起应收开票批次审批
  link16 - 新建...发起应收开票批次审批、审核生成开票申请
  link17 - 新建...审核生成开票申请、发票上传与登记
  link18 - 新建...发票上传与登记、应收核销（feeTakePage + writeoffBatch）
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


# =============================================================================
# 链路13：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单、生成费用确认单、发起应收对账批次
# =============================================================================
@pytest.mark.link13
class TestLink13ReceiveAccount:
    """链路13：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单 → 生成费用确认单 → 发起应收对账批次"""

    @allure.feature("链路测试")
    @allure.story("链路13：新建、分发、查询、暂存、提交、生成子订单、录费用、资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批、生成费用通知单、生成费用确认单、发起应收对账批次")
    @allure.severity("critical")
    @allure.title("链路13：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 → 订单锁定审批 → 未放款开票申请审批 → 供应商垫付申请审批 → 生成费用通知单 → 生成费用确认单 → 发起应收对账批次")
    def test_link13_receive_account(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 费用通知单 + 费用确认单 + 应收对账批次），链路停在 receive_account 阶段"""
        bl_no = 'LK13_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→生成费用确认单→发起应收对账批次）'):
            result = OrderWorkflow.full_flow(
                stop_at='receive_account',
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

        # ---------- 生成费用确认单 ----------

        with allure.step('断言：生成费用确认单成功'):
            confirm_result = result['fee_confirm_result']
            assert confirm_result is not None, '费用确认单结果不应为空'
            assert confirm_result['resp'].status_code == 200, \
                f'HTTP 状态码异常: {confirm_result["resp"].status_code}'
            data = confirm_result['data']
            assert data['code'] == 200, f'响应 code 不为 200: {data}'
            assert data.get('msg') == '成功', f'响应 msg 不为"成功": {data.get("msg")}'
            confirm_file = confirm_result['file_info']
            assert confirm_file, f'费用确认单 file_info 不应为空: {data}'
            assert confirm_file.get('file_id')
            assert confirm_file.get('file_name')
            assert confirm_file.get('file_type', '').upper() == 'PDF'
            assert confirm_file.get('file_url')
            assert confirm_file.get('original_name')

        # ---------- 发起应收对账批次（重点断言） ----------

        with allure.step('断言：应收对账批次结果存在'):
            receive_result = result['receive_account_result']
            assert receive_result is not None, '应收对账批次结果不应为空'

        with allure.step('断言：financePutList 查询成功'):
            put_list_resp = receive_result['put_list_resp']
            assert put_list_resp.status_code == 200, f'financePutList HTTP 状态码异常: {put_list_resp.status_code}'
            put_list_data = receive_result['put_list_data']
            assert put_list_data.get('code') == 200, f'financePutList code 不为 200: {put_list_data}'

        with allure.step('断言：select_list 非空'):
            select_list = receive_result['select_list']
            assert select_list is not None, 'select_list 不应为 None'
            assert isinstance(select_list, list), f'select_list 应为 list，实际: {type(select_list)}'
            assert len(select_list) > 0, f'select_list 不应为空，实际: {select_list}'

        with allure.step('断言：预校验（action=check）成功'):
            check_resp = receive_result['check_resp']
            assert check_resp.status_code == 200, f'预校验 HTTP 状态码异常: {check_resp.status_code}'
            check_data = receive_result['check_data']
            assert check_data.get('code') == 200, f'预校验 code 不为 200: {check_data}'
            assert check_data.get('msg') == '成功', f'预校验 msg 不为"成功": {check_data.get("msg")}'

        with allure.step('断言：正式提交（action=submit）成功'):
            submit_resp = receive_result['submit_resp']
            assert submit_resp.status_code == 200, f'正式提交 HTTP 状态码异常: {submit_resp.status_code}'
            submit_data = receive_result['submit_data']
            assert submit_data.get('code') == 200, f'正式提交 code 不为 200: {submit_data}'
            assert submit_data.get('msg') == '成功', f'正式提交 msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：receive_account_id 非空'):
            receive_account_id = receive_result['receive_account_id']
            assert receive_account_id, f'receive_account_id 不应为空: {receive_result}'

        with allure.step('断言：receive_account_no 非空且为字符串'):
            receive_account_no = receive_result['receive_account_no']
            assert receive_account_no, f'receive_account_no 不应为空: {receive_result}'
            assert isinstance(receive_account_no, str), f'receive_account_no 应为 str，实际: {type(receive_account_no)}'

        with allure.step('断言：receive_account_no 格式正确（以 YSDZPC 开头）'):
            assert receive_account_no.startswith('YSDZPC'), \
                f'receive_account_no 应以 YSDZPC 开头，实际: {receive_account_no}'

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 receive_account 阶段'):
            assert result['stop_at'] == 'receive_account'

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
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路14：新建...发起应收对账批次 → 确认应收对账
# =============================================================================
@pytest.mark.link14
class TestLink14ConfirmAccount:
    """链路14：新建 → ... → 发起应收对账批次 → 确认应收对账"""

    @allure.feature("链路测试")
    @allure.story("链路14：发起应收对账批次 + 确认应收对账")
    @allure.severity("critical")
    @allure.title("链路14：发起应收对账批次 → 确认应收对账")
    def test_link14_confirm_account(self):
        """验证：完整链路（LINK13 + 确认应收对账），链路停在 confirm_account 阶段"""
        bl_no = 'LK14_' + __import__('time').strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→发起应收对账批次→确认应收对账）'):
            result = OrderWorkflow.full_flow(
                stop_at='confirm_account',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK13 步骤断言 ----------

        with allure.step('断言：新建成功'):
            assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'

        with allure.step('断言：分发成功'):
            assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'

        with allure.step('断言：生成子订单成功'):
            gen_data = result['generate_sub_data']
            assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

        with allure.step('断言：录费用成功'):
            assert len(result['record_fee_results']) == 1
            fee_1 = result['record_fee_results'][0]
            assert fee_1['resp'].status_code == 200
            assert fee_1['data']['code'] == 200

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None
            assert fee_1['audit_send_resp'].status_code == 200
            assert fee_1['audit_send_data']['code'] == 200
            assert fee_1.get('audit_id')
            assert fee_1['audit_approve_resp'].status_code == 200
            assert fee_1['audit_approve_data']['code'] == 200

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None
            assert lock_result['container']
            assert lock_result['send_resp'].status_code == 200
            assert lock_result['send_data']['code'] == 200
            assert lock_result.get('audit_id')
            assert lock_result['approve_resp'].status_code == 200
            assert lock_result['approve_data']['code'] == 200

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None
            assert invoice_result['send_resp'].status_code == 200
            assert invoice_result['send_data']['code'] == 200
            assert invoice_result.get('audit_id')
            assert invoice_result['approve_resp'].status_code == 200
            assert invoice_result['approve_data']['code'] == 200

        with allure.step('断言：供应商垫付申请审批成功'):
            advance_result = result['supplier_advance_result']
            assert advance_result is not None
            assert advance_result['send_resp'].status_code == 200
            assert advance_result['send_data']['code'] == 200
            assert advance_result.get('audit_id')
            assert advance_result['approve_resp'].status_code == 200
            assert advance_result['approve_data']['code'] == 200

        with allure.step('断言：生成费用通知单成功'):
            notice_result = result['fee_notice_result']
            assert notice_result is not None
            assert notice_result['resp'].status_code == 200
            assert notice_result['data']['code'] == 200

        with allure.step('断言：生成费用确认单成功'):
            confirm_result = result['fee_confirm_result']
            assert confirm_result is not None
            assert confirm_result['resp'].status_code == 200
            assert confirm_result['data']['code'] == 200

        with allure.step('断言：发起应收对账批次成功'):
            receive_result = result['receive_account_result']
            assert receive_result is not None
            assert receive_result['put_list_resp'].status_code == 200
            assert receive_result['put_list_data'].get('code') == 200
            assert receive_result['check_resp'].status_code == 200
            assert receive_result['check_data'].get('code') == 200
            assert receive_result['submit_resp'].status_code == 200
            assert receive_result['submit_data'].get('code') == 200
            assert receive_result['submit_data'].get('msg') == '成功'
            assert receive_result['receive_account_id']
            assert receive_result['receive_account_no'].startswith('YSDZPC')

        # ---------- 确认应收对账（重点断言） ----------

        with allure.step('断言：确认应收对账结果存在'):
            confirm_result = result['confirm_account_result']
            assert confirm_result is not None, '确认应收对账结果不应为空'

        with allure.step('断言：receiveAccountDetail 查询成功'):
            detail_resp = confirm_result['detail_resp']
            assert detail_resp.status_code == 200, f'HTTP 状态码异常: {detail_resp.status_code}'
            detail_data = confirm_result['detail_data']
            assert detail_data.get('code') == 200, f'receiveAccountDetail code 不为 200: {detail_data}'
            assert detail_data.get('msg') == '成功', f'receiveAccountDetail msg 不为"成功": {detail_data.get("msg")}'

        with allure.step('断言：receiveConfirmList 查询成功'):
            confirm_list_resp = confirm_result['confirm_list_resp']
            assert confirm_list_resp.status_code == 200, f'HTTP 状态码异常: {confirm_list_resp.status_code}'
            confirm_list_data = confirm_result['confirm_list_data']
            assert confirm_list_data.get('code') == 200, f'receiveConfirmList code 不为 200: {confirm_list_data}'
            assert confirm_list_data.get('msg') == '成功', f'receiveConfirmList msg 不为"成功": {confirm_list_data.get("msg")}'

        with allure.step('断言：confirm_list 非空'):
            confirm_list = confirm_result['confirm_list']
            assert confirm_list is not None
            assert isinstance(confirm_list, list)
            assert len(confirm_list) > 0, 'confirm_list 不应为空'

        with allure.step('断言：accountConfirm 确认成功'):
            submit_resp = confirm_result['submit_resp']
            assert submit_resp.status_code == 200, f'HTTP 状态码异常: {submit_resp.status_code}'
            submit_data = confirm_result['submit_data']
            assert submit_data.get('code') == 200, f'accountConfirm code 不为 200: {submit_data}'
            assert submit_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：receiveAccountPage 查询成功'):
            page_resp = confirm_result['page_resp']
            assert page_resp.status_code == 200, f'HTTP 状态码异常: {page_resp.status_code}'
            page_data = confirm_result['page_data']
            assert page_data.get('code') == 200, f'receiveAccountPage code 不为 200: {page_data}'
            assert page_data.get('msg') == '成功', f'receiveAccountPage msg 不为"成功": {page_data.get("msg")}'

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 confirm_account 阶段'):
            assert result['stop_at'] == 'confirm_account'

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
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


@pytest.mark.link15
class TestLink15InvoiceBatch:
    """链路15：新建 → ... → 发起应收对账批次 → 确认应收对账 → 发起应收开票批次审批"""

    @allure.feature("链路测试")
    @allure.story("链路15：发起应收开票批次审批")
    @allure.severity("critical")
    @allure.title("链路15：发起应收对账 → 确认应收对账 → 发起应收开票批次审批")
    def test_link15_invoice_batch(self):
        """验证：完整链路（LINK14 + 发起应收开票批次审批），链路停在 invoice_batch 阶段"""
        import time as _time
        bl_no = 'LK15_' + _time.strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→发起应收对账批次→确认应收对账→发起应收开票批次审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_batch',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK13 步骤断言 ----------

        with allure.step('断言：新建成功'):
            assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'

        with allure.step('断言：分发成功'):
            assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'

        with allure.step('断言：生成子订单成功'):
            gen_data = result['generate_sub_data']
            assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

        with allure.step('断言：录费用成功'):
            assert len(result['record_fee_results']) == 1
            fee_1 = result['record_fee_results'][0]
            assert fee_1['resp'].status_code == 200
            assert fee_1['data']['code'] == 200

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None
            assert fee_1['audit_send_resp'].status_code == 200
            assert fee_1['audit_send_data']['code'] == 200
            assert fee_1.get('audit_id')
            assert fee_1['audit_approve_resp'].status_code == 200
            assert fee_1['audit_approve_data']['code'] == 200

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None
            assert lock_result['container']
            assert lock_result['send_resp'].status_code == 200
            assert lock_result['send_data']['code'] == 200
            assert lock_result.get('audit_id')
            assert lock_result['approve_resp'].status_code == 200
            assert lock_result['approve_data']['code'] == 200

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None
            assert invoice_result['send_resp'].status_code == 200
            assert invoice_result['send_data']['code'] == 200
            assert invoice_result.get('audit_id')
            assert invoice_result['approve_resp'].status_code == 200
            assert invoice_result['approve_data']['code'] == 200

        with allure.step('断言：供应商垫付申请审批成功'):
            advance_result = result['supplier_advance_result']
            assert advance_result is not None
            assert advance_result['send_resp'].status_code == 200
            assert advance_result['send_data']['code'] == 200
            assert advance_result.get('audit_id')
            assert advance_result['approve_resp'].status_code == 200
            assert advance_result['approve_data']['code'] == 200

        with allure.step('断言：生成费用通知单成功'):
            notice_result = result['fee_notice_result']
            assert notice_result is not None
            assert notice_result['resp'].status_code == 200
            assert notice_result['data']['code'] == 200

        with allure.step('断言：生成费用确认单成功'):
            fee_confirm_result = result['fee_confirm_result']
            assert fee_confirm_result is not None
            assert fee_confirm_result['resp'].status_code == 200
            assert fee_confirm_result['data']['code'] == 200

        with allure.step('断言：发起应收对账批次成功'):
            receive_result = result['receive_account_result']
            assert receive_result is not None
            assert receive_result['put_list_resp'].status_code == 200
            assert receive_result['put_list_data'].get('code') == 200
            assert receive_result['check_resp'].status_code == 200
            assert receive_result['check_data'].get('code') == 200
            assert receive_result['submit_resp'].status_code == 200
            assert receive_result['submit_data'].get('code') == 200
            assert receive_result['submit_data'].get('msg') == '成功'
            assert receive_result['receive_account_id']
            assert receive_result['receive_account_no'].startswith('YSDZPC')

        # ---------- LINK14 确认应收对账断言 ----------

        with allure.step('断言：确认应收对账结果存在'):
            confirm_result = result['confirm_account_result']
            assert confirm_result is not None, '确认应收对账结果不应为空'

        with allure.step('断言：receiveAccountDetail 查询成功'):
            detail_resp = confirm_result['detail_resp']
            assert detail_resp.status_code == 200, f'HTTP 状态码异常: {detail_resp.status_code}'
            detail_data = confirm_result['detail_data']
            assert detail_data.get('code') == 200, f'receiveAccountDetail code 不为 200: {detail_data}'
            assert detail_data.get('msg') == '成功', f'receiveAccountDetail msg 不为"成功": {detail_data.get("msg")}'

        with allure.step('断言：receiveConfirmList 查询成功'):
            confirm_list_resp = confirm_result['confirm_list_resp']
            assert confirm_list_resp.status_code == 200, f'HTTP 状态码异常: {confirm_list_resp.status_code}'
            confirm_list_data = confirm_result['confirm_list_data']
            assert confirm_list_data.get('code') == 200, f'receiveConfirmList code 不为 200: {confirm_list_data}'
            assert confirm_list_data.get('msg') == '成功', f'receiveConfirmList msg 不为"成功": {confirm_list_data.get("msg")}'

        with allure.step('断言：confirm_list 非空'):
            confirm_list = confirm_result['confirm_list']
            assert confirm_list is not None
            assert isinstance(confirm_list, list)
            assert len(confirm_list) > 0, 'confirm_list 不应为空'

        with allure.step('断言：accountConfirm 确认成功'):
            submit_resp = confirm_result['submit_resp']
            assert submit_resp.status_code == 200, f'HTTP 状态码异常: {submit_resp.status_code}'
            submit_data = confirm_result['submit_data']
            assert submit_data.get('code') == 200, f'accountConfirm code 不为 200: {submit_data}'
            assert submit_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：receiveAccountPage 查询成功'):
            page_resp = confirm_result['page_resp']
            assert page_resp.status_code == 200, f'HTTP 状态码异常: {page_resp.status_code}'
            page_data = confirm_result['page_data']
            assert page_data.get('code') == 200, f'receiveAccountPage code 不为 200: {page_data}'
            assert page_data.get('msg') == '成功', f'receiveAccountPage msg 不为"成功": {page_data.get("msg")}'

        # ---------- LINK15 发起应收开票批次审批断言 ----------

        with allure.step('断言：发起应收开票批次审批结果存在'):
            invoice_result = result['invoice_batch_result']
            assert invoice_result is not None, 'invoice_batch_result 不应为空'

        with allure.step('断言：financePutList 查询成功'):
            put_list_data = invoice_result['put_list_data']
            assert invoice_result['put_list_resp'].status_code == 200
            assert put_list_data.get('code') == 200, f'查询应收款项列表失败: {put_list_data}'

        with allure.step('断言：monthExchangeRate 获取汇率成功'):
            rate_data = invoice_result['rate_data']
            assert invoice_result['rate_resp'].status_code == 200
            assert rate_data.get('code') == 200, f'获取汇率失败: {rate_data}'
            assert invoice_result.get('exchange_rate'), '汇率为空'

        with allure.step('断言：getSellInfo 获取开票方信息成功'):
            sell_info_data = invoice_result['sell_info_data']
            assert invoice_result['sell_info_resp'].status_code == 200
            assert sell_info_data.get('code') == 200, f'获取开票方信息失败: {sell_info_data}'

        with allure.step('断言：batchOrderEdit 提交应收开票批次申请成功'):
            invoice_submit_data = invoice_result['invoice_submit_data']
            assert invoice_result['invoice_submit_resp'].status_code == 200
            assert invoice_submit_data.get('code') == 200, f'提交应收开票批次申请失败: {invoice_submit_data}'
            assert invoice_submit_data.get('msg') == '成功', f'提交应收开票批次申请 msg 不为"成功": {invoice_submit_data.get("msg")}'

        with allure.step('断言：batchPage 查询批次成功'):
            page_data = invoice_result['page_data']
            assert invoice_result['page_resp'].status_code == 200
            assert page_data.get('code') == 200, f'验证批次查询失败: {page_data}'
            assert page_data.get('msg') == '成功', f'批次查询 msg 不为"成功": {page_data.get("msg")}'

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 invoice_batch 阶段'):
            assert result['stop_at'] == 'invoice_batch'

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
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
                '查询应收款项列表（开票）',
                '获取汇率',
                '获取开票方信息',
                '提交应收开票批次申请',
                '验证应收开票批次',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路16：新建...发起应收开票批次审批 → 审核生成开票申请
# =============================================================================
@pytest.mark.link16
class TestLink16InvoiceBatchAudit:
    """链路16：新建 → ... → 发起应收开票批次审批 → 审核生成开票申请"""

    @allure.feature("链路测试")
    @allure.story("链路16：审核生成开票申请")
    @allure.severity("critical")
    @allure.title("链路16：发起应收开票批次审批 → 审核生成开票申请")
    def test_link16_invoice_batch_audit(self):
        """验证：完整链路（LINK15 + 审核生成开票申请），链路停在 invoice_batch_audit 阶段"""
        import time as _time
        bl_no = 'LK16_' + _time.strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→发起应收开票批次审批→审核生成开票申请）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_batch_audit',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK13 步骤断言 ----------

        with allure.step('断言：新建成功'):
            assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'

        with allure.step('断言：分发成功'):
            assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'

        with allure.step('断言：生成子订单成功'):
            gen_data = result['generate_sub_data']
            assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

        with allure.step('断言：录费用成功'):
            assert len(result['record_fee_results']) == 1
            fee_1 = result['record_fee_results'][0]
            assert fee_1['resp'].status_code == 200
            assert fee_1['data']['code'] == 200

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None
            assert fee_1['audit_send_resp'].status_code == 200
            assert fee_1['audit_send_data']['code'] == 200
            assert fee_1.get('audit_id')
            assert fee_1['audit_approve_resp'].status_code == 200
            assert fee_1['audit_approve_data']['code'] == 200

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None
            assert lock_result['container']
            assert lock_result['send_resp'].status_code == 200
            assert lock_result['send_data']['code'] == 200
            assert lock_result.get('audit_id')
            assert lock_result['approve_resp'].status_code == 200
            assert lock_result['approve_data']['code'] == 200

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None
            assert invoice_result['send_resp'].status_code == 200
            assert invoice_result['send_data']['code'] == 200
            assert invoice_result.get('audit_id')
            assert invoice_result['approve_resp'].status_code == 200
            assert invoice_result['approve_data']['code'] == 200

        with allure.step('断言：供应商垫付申请审批成功'):
            advance_result = result['supplier_advance_result']
            assert advance_result is not None
            assert advance_result['send_resp'].status_code == 200
            assert advance_result['send_data']['code'] == 200
            assert advance_result.get('audit_id')
            assert advance_result['approve_resp'].status_code == 200
            assert advance_result['approve_data']['code'] == 200

        with allure.step('断言：生成费用通知单成功'):
            notice_result = result['fee_notice_result']
            assert notice_result is not None
            assert notice_result['resp'].status_code == 200
            assert notice_result['data']['code'] == 200

        with allure.step('断言：生成费用确认单成功'):
            fee_confirm_result = result['fee_confirm_result']
            assert fee_confirm_result is not None
            assert fee_confirm_result['resp'].status_code == 200
            assert fee_confirm_result['data']['code'] == 200

        with allure.step('断言：发起应收对账批次成功'):
            receive_result = result['receive_account_result']
            assert receive_result is not None
            assert receive_result['put_list_resp'].status_code == 200
            assert receive_result['put_list_data'].get('code') == 200
            assert receive_result['check_resp'].status_code == 200
            assert receive_result['check_data'].get('code') == 200
            assert receive_result['submit_resp'].status_code == 200
            assert receive_result['submit_data'].get('code') == 200
            assert receive_result['submit_data'].get('msg') == '成功'
            assert receive_result['receive_account_id']
            assert receive_result['receive_account_no'].startswith('YSDZPC')

        # ---------- LINK14 确认应收对账断言 ----------

        with allure.step('断言：确认应收对账结果存在'):
            confirm_result = result['confirm_account_result']
            assert confirm_result is not None, '确认应收对账结果不应为空'

        with allure.step('断言：receiveAccountDetail 查询成功'):
            detail_resp = confirm_result['detail_resp']
            assert detail_resp.status_code == 200, f'HTTP 状态码异常: {detail_resp.status_code}'
            detail_data = confirm_result['detail_data']
            assert detail_data.get('code') == 200, f'receiveAccountDetail code 不为 200: {detail_data}'
            assert detail_data.get('msg') == '成功', f'receiveAccountDetail msg 不为"成功": {detail_data.get("msg")}'

        with allure.step('断言：receiveConfirmList 查询成功'):
            confirm_list_resp = confirm_result['confirm_list_resp']
            assert confirm_list_resp.status_code == 200, f'HTTP 状态码异常: {confirm_list_resp.status_code}'
            confirm_list_data = confirm_result['confirm_list_data']
            assert confirm_list_data.get('code') == 200, f'receiveConfirmList code 不为 200: {confirm_list_data}'
            assert confirm_list_data.get('msg') == '成功', f'receiveConfirmList msg 不为"成功": {confirm_list_data.get("msg")}'

        with allure.step('断言：confirm_list 非空'):
            confirm_list = confirm_result['confirm_list']
            assert confirm_list is not None
            assert isinstance(confirm_list, list)
            assert len(confirm_list) > 0, 'confirm_list 不应为空'

        with allure.step('断言：accountConfirm 确认成功'):
            submit_resp = confirm_result['submit_resp']
            assert submit_resp.status_code == 200, f'HTTP 状态码异常: {submit_resp.status_code}'
            submit_data = confirm_result['submit_data']
            assert submit_data.get('code') == 200, f'accountConfirm code 不为 200: {submit_data}'
            assert submit_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：receiveAccountPage 查询成功'):
            page_resp = confirm_result['page_resp']
            assert page_resp.status_code == 200, f'HTTP 状态码异常: {page_resp.status_code}'
            page_data = confirm_result['page_data']
            assert page_data.get('code') == 200, f'receiveAccountPage code 不为 200: {page_data}'
            assert page_data.get('msg') == '成功', f'receiveAccountPage msg 不为"成功": {page_data.get("msg")}'

        # ---------- LINK15 发起应收开票批次审批断言 ----------

        with allure.step('断言：发起应收开票批次审批结果存在'):
            invoice_batch_result = result['invoice_batch_result']
            assert invoice_batch_result is not None, 'invoice_batch_result 不应为空'

        with allure.step('断言：financePutList 查询成功'):
            put_list_data = invoice_batch_result['put_list_data']
            assert invoice_batch_result['put_list_resp'].status_code == 200
            assert put_list_data.get('code') == 200, f'查询应收款项列表失败: {put_list_data}'

        with allure.step('断言：monthExchangeRate 获取汇率成功'):
            rate_data = invoice_batch_result['rate_data']
            assert invoice_batch_result['rate_resp'].status_code == 200
            assert rate_data.get('code') == 200, f'获取汇率失败: {rate_data}'
            assert invoice_batch_result.get('exchange_rate'), '汇率为空'

        with allure.step('断言：getSellInfo 获取开票方信息成功'):
            sell_info_data = invoice_batch_result['sell_info_data']
            assert invoice_batch_result['sell_info_resp'].status_code == 200
            assert sell_info_data.get('code') == 200, f'获取开票方信息失败: {sell_info_data}'

        with allure.step('断言：batchOrderEdit 提交应收开票批次申请成功'):
            invoice_submit_data = invoice_batch_result['invoice_submit_data']
            assert invoice_batch_result['invoice_submit_resp'].status_code == 200
            assert invoice_submit_data.get('code') == 200, f'提交应收开票批次申请失败: {invoice_submit_data}'
            assert invoice_submit_data.get('msg') == '成功', f'提交应收开票批次申请 msg 不为"成功": {invoice_submit_data.get("msg")}'

        with allure.step('断言：batchPage 查询批次成功'):
            page_data = invoice_batch_result['page_data']
            assert invoice_batch_result['page_resp'].status_code == 200
            assert page_data.get('code') == 200, f'验证批次查询失败: {page_data}'
            assert page_data.get('msg') == '成功', f'批次查询 msg 不为"成功": {page_data.get("msg")}'

        with allure.step('断言：batch_id 非空'):
            batch_id = invoice_batch_result['batch_id']
            assert batch_id, f'batch_id 不应为空: {invoice_batch_result}'

        # ---------- LINK16 审核生成开票申请断言 ----------

        with allure.step('断言：审核生成开票申请结果存在'):
            audit_result = result['invoice_batch_audit_result']
            assert audit_result is not None, 'invoice_batch_audit_result 不应为空'

        with allure.step('断言：auditPage 查询审批ID成功'):
            audit_query_data = audit_result['audit_query_data']
            assert audit_result['audit_query_resp'].status_code == 200
            assert audit_query_data.get('code') == 200, f'auditPage 查询失败: {audit_query_data}'
            assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'

        with allure.step('断言：auditExecute 审批通过成功'):
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_result['audit_execute_resp'].status_code == 200
            assert audit_execute_data.get('code') == 200, f'auditExecute 审批失败: {audit_execute_data}'
            assert '成功' in audit_execute_data.get('msg', ''), f'auditExecute msg 不含"成功": {audit_execute_data.get("msg")}'

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 invoice_batch_audit 阶段'):
            assert result['stop_at'] == 'invoice_batch_audit'

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
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
                '查询应收款项列表（开票）',
                '获取汇率',
                '获取开票方信息',
                '提交应收开票批次申请',
                '验证应收开票批次',
                '查询应收开票批次审批ID',
                '审批通过应收开票批次',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路17：新建...审核生成开票申请 → 发票上传与登记
# =============================================================================
@pytest.mark.link17
class TestLink17InvoiceUpload:
    """链路17：新建 → ... → 审核生成开票申请 → 发票上传与登记"""

    @allure.feature("链路测试")
    @allure.story("链路17：发票上传与登记")
    @allure.severity("critical")
    @allure.title("链路17：审核生成开票申请 → 发票上传与登记")
    def test_link17_invoice_upload(self):
        """验证：完整链路（LINK16 + 发票上传与登记），链路停在 invoice_upload 阶段"""
        import time as _time
        bl_no = 'LK17_' + _time.strftime('%Y%m%d%H%M%S')

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→审核生成开票申请→发票上传与登记）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_upload',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK13 步骤断言 ----------

        with allure.step('断言：新建成功'):
            assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'

        with allure.step('断言：分发成功'):
            assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'

        with allure.step('断言：生成子订单成功'):
            gen_data = result['generate_sub_data']
            assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

        with allure.step('断言：录费用成功'):
            assert len(result['record_fee_results']) == 1
            fee_1 = result['record_fee_results'][0]
            assert fee_1['resp'].status_code == 200
            assert fee_1['data']['code'] == 200

        with allure.step('断言：资产推送审批成功'):
            assert fee_1.get('audit_send_resp') is not None
            assert fee_1['audit_send_resp'].status_code == 200
            assert fee_1['audit_send_data']['code'] == 200
            assert fee_1.get('audit_id')
            assert fee_1['audit_approve_resp'].status_code == 200
            assert fee_1['audit_approve_data']['code'] == 200

        with allure.step('断言：订单锁定审批成功'):
            lock_result = result['order_lock_result']
            assert lock_result is not None
            assert lock_result['container']
            assert lock_result['send_resp'].status_code == 200
            assert lock_result['send_data']['code'] == 200
            assert lock_result.get('audit_id')
            assert lock_result['approve_resp'].status_code == 200
            assert lock_result['approve_data']['code'] == 200

        with allure.step('断言：未放款开票申请审批成功'):
            invoice_result = result['invoice_apply_result']
            assert invoice_result is not None
            assert invoice_result['send_resp'].status_code == 200
            assert invoice_result['send_data']['code'] == 200
            assert invoice_result.get('audit_id')
            assert invoice_result['approve_resp'].status_code == 200
            assert invoice_result['approve_data']['code'] == 200

        with allure.step('断言：供应商垫付申请审批成功'):
            advance_result = result['supplier_advance_result']
            assert advance_result is not None
            assert advance_result['send_resp'].status_code == 200
            assert advance_result['send_data']['code'] == 200
            assert advance_result.get('audit_id')
            assert advance_result['approve_resp'].status_code == 200
            assert advance_result['approve_data']['code'] == 200

        with allure.step('断言：生成费用通知单成功'):
            notice_result = result['fee_notice_result']
            assert notice_result is not None
            assert notice_result['resp'].status_code == 200
            assert notice_result['data']['code'] == 200

        with allure.step('断言：生成费用确认单成功'):
            fee_confirm_result = result['fee_confirm_result']
            assert fee_confirm_result is not None
            assert fee_confirm_result['resp'].status_code == 200
            assert fee_confirm_result['data']['code'] == 200

        with allure.step('断言：发起应收对账批次成功'):
            receive_result = result['receive_account_result']
            assert receive_result is not None
            assert receive_result['put_list_resp'].status_code == 200
            assert receive_result['put_list_data'].get('code') == 200
            assert receive_result['check_resp'].status_code == 200
            assert receive_result['check_data'].get('code') == 200
            assert receive_result['submit_resp'].status_code == 200
            assert receive_result['submit_data'].get('code') == 200
            assert receive_result['submit_data'].get('msg') == '成功'
            assert receive_result['receive_account_id']
            assert receive_result['receive_account_no'].startswith('YSDZPC')

        # ---------- LINK14 确认应收对账断言 ----------

        with allure.step('断言：确认应收对账结果存在'):
            confirm_result = result['confirm_account_result']
            assert confirm_result is not None, '确认应收对账结果不应为空'

        with allure.step('断言：receiveAccountDetail 查询成功'):
            detail_resp = confirm_result['detail_resp']
            assert detail_resp.status_code == 200, f'HTTP 状态码异常: {detail_resp.status_code}'
            detail_data = confirm_result['detail_data']
            assert detail_data.get('code') == 200, f'receiveAccountDetail code 不为 200: {detail_data}'
            assert detail_data.get('msg') == '成功', f'receiveAccountDetail msg 不为"成功": {detail_data.get("msg")}'

        with allure.step('断言：receiveConfirmList 查询成功'):
            confirm_list_resp = confirm_result['confirm_list_resp']
            assert confirm_list_resp.status_code == 200, f'HTTP 状态码异常: {confirm_list_resp.status_code}'
            confirm_list_data = confirm_result['confirm_list_data']
            assert confirm_list_data.get('code') == 200, f'receiveConfirmList code 不为 200: {confirm_list_data}'
            assert confirm_list_data.get('msg') == '成功', f'receiveConfirmList msg 不为"成功": {confirm_list_data.get("msg")}'

        with allure.step('断言：confirm_list 非空'):
            confirm_list = confirm_result['confirm_list']
            assert confirm_list is not None
            assert isinstance(confirm_list, list)
            assert len(confirm_list) > 0, 'confirm_list 不应为空'

        with allure.step('断言：accountConfirm 确认成功'):
            submit_resp = confirm_result['submit_resp']
            assert submit_resp.status_code == 200, f'HTTP 状态码异常: {submit_resp.status_code}'
            submit_data = confirm_result['submit_data']
            assert submit_data.get('code') == 200, f'accountConfirm code 不为 200: {submit_data}'
            assert submit_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：receiveAccountPage 查询成功'):
            page_resp = confirm_result['page_resp']
            assert page_resp.status_code == 200, f'HTTP 状态码异常: {page_resp.status_code}'
            page_data = confirm_result['page_data']
            assert page_data.get('code') == 200, f'receiveAccountPage code 不为 200: {page_data}'
            assert page_data.get('msg') == '成功', f'receiveAccountPage msg 不为"成功": {page_data.get("msg")}'

        # ---------- LINK15 发起应收开票批次审批断言 ----------

        with allure.step('断言：发起应收开票批次审批结果存在'):
            invoice_batch_result = result['invoice_batch_result']
            assert invoice_batch_result is not None, 'invoice_batch_result 不应为空'

        with allure.step('断言：financePutList 查询成功'):
            put_list_data = invoice_batch_result['put_list_data']
            assert invoice_batch_result['put_list_resp'].status_code == 200
            assert put_list_data.get('code') == 200, f'查询应收款项列表失败: {put_list_data}'

        with allure.step('断言：monthExchangeRate 获取汇率成功'):
            rate_data = invoice_batch_result['rate_data']
            assert invoice_batch_result['rate_resp'].status_code == 200
            assert rate_data.get('code') == 200, f'获取汇率失败: {rate_data}'
            assert invoice_batch_result.get('exchange_rate'), '汇率为空'

        with allure.step('断言：getSellInfo 获取开票方信息成功'):
            sell_info_data = invoice_batch_result['sell_info_data']
            assert invoice_batch_result['sell_info_resp'].status_code == 200
            assert sell_info_data.get('code') == 200, f'获取开票方信息失败: {sell_info_data}'

        with allure.step('断言：batchOrderEdit 提交应收开票批次申请成功'):
            invoice_submit_data = invoice_batch_result['invoice_submit_data']
            assert invoice_batch_result['invoice_submit_resp'].status_code == 200
            assert invoice_submit_data.get('code') == 200, f'提交应收开票批次申请失败: {invoice_submit_data}'
            assert invoice_submit_data.get('msg') == '成功', f'提交应收开票批次申请 msg 不为"成功": {invoice_submit_data.get("msg")}'

        with allure.step('断言：batchPage 查询批次成功'):
            page_data = invoice_batch_result['page_data']
            assert invoice_batch_result['page_resp'].status_code == 200
            assert page_data.get('code') == 200, f'验证批次查询失败: {page_data}'
            assert page_data.get('msg') == '成功', f'批次查询 msg 不为"成功": {page_data.get("msg")}'

        with allure.step('断言：batch_id 非空'):
            batch_id = invoice_batch_result['batch_id']
            assert batch_id, f'batch_id 不应为空: {invoice_batch_result}'

        # ---------- LINK16 审核生成开票申请断言 ----------

        with allure.step('断言：审核生成开票申请结果存在'):
            audit_result = result['invoice_batch_audit_result']
            assert audit_result is not None, 'invoice_batch_audit_result 不应为空'

        with allure.step('断言：auditPage 查询审批ID成功'):
            audit_query_data = audit_result['audit_query_data']
            assert audit_result['audit_query_resp'].status_code == 200
            assert audit_query_data.get('code') == 200, f'auditPage 查询失败: {audit_query_data}'
            assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'

        with allure.step('断言：auditExecute 审批通过成功'):
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_result['audit_execute_resp'].status_code == 200
            assert audit_execute_data.get('code') == 200, f'auditExecute 审批失败: {audit_execute_data}'
            assert '成功' in audit_execute_data.get('msg', ''), f'auditExecute msg 不含"成功": {audit_execute_data.get("msg")}'

        # ---------- LINK17 发票上传与登记断言 ----------

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

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 invoice_upload 阶段'):
            assert result['stop_at'] == 'invoice_upload'

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
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
                '查询应收款项列表（开票）',
                '获取汇率',
                '获取开票方信息',
                '提交应收开票批次申请',
                '验证应收开票批次',
                '查询应收开票批次审批ID',
                '审批通过应收开票批次',
                '上传应收发票',
                '获取发票申请ID',
                '登记发票到申请',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路18：新建...发票上传与登记 → 应收核销（feeTakePage + writeoffBatch）
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
        import time as _time
        bl_no = 'LK18_' + _time.strftime('%Y%m%d%H%M%S')

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

        # ---------- 链路停止阶段 ----------

        with allure.step('断言：链路停在 receive_writeoff 阶段'):
            assert result['stop_at'] == 'receive_writeoff'

        # ---------- steps 记录完整 ----------

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '查询应收核销费用列表',
                '应收核销',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
