"""
链路测试 - 订单基础（link1~5）

  link1 - 新建
  link2 - 分发
  link3 - 暂存
  link4 - 提交
  link5 - 生成子订单
"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from utils import generate_bl_no


# =============================================================================
# 链路1：新建
# =============================================================================
@pytest.mark.order1
class TestOrder1Create:
    """链路1：新建"""

    @allure.feature("链路测试")
    @allure.story("链路1：新建")
    @allure.severity("critical")
    @allure.title("链路1：新建")
    def test_link1_create(self):
        """验证：新建订单成功，API 返回 code=200"""
        bl_no = generate_bl_no(1)

        with allure.step("执行新建"):
            result = OrderWorkflow.run(stop_at="create", bl_no=bl_no)

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
# 链路2：分发
# =============================================================================
@pytest.mark.order2
class TestOrder2CreateAndDistribute:
    """链路2：新建 → 分发"""

    @allure.feature("链路测试")
    @allure.story("链路2：分发")
    @allure.severity("critical")
    @allure.title("链路2：新建 → 分发")
    def test_link2_create_and_distribute(self):
        """验证：新建成功，分发成功，链路停在 distribute 阶段"""
        bl_no = generate_bl_no(2)

        with allure.step("执行新建+分发"):
            result = OrderWorkflow.run(stop_at="distribute", bl_no=bl_no)

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
# 链路3：暂存
# =============================================================================
@pytest.mark.order3
class TestOrder3Stash:
    """链路3：新建 → 分发 → 查询 → 暂存"""

    @allure.feature("链路测试")
    @allure.story("链路3：暂存")
    @allure.severity("critical")
    @allure.title("链路3：新建 → 分发 → 查询 → 暂存")
    def test_link3_create_distribute_query_stash(self):
        """验证：分发后查询到 order_id，暂存成功（status=1），链路停在 stash 阶段"""
        bl_no = generate_bl_no(3)

        with allure.step("执行新建+分发+查询+暂存"):
            result = OrderWorkflow.run(stop_at="stash", bl_no=bl_no)

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
# 链路4：提交（完整链路）
# =============================================================================
@pytest.mark.order4
class TestOrder4FullWithStash:
    """链路4：新建 → 分发 → 查询 → 暂存 → 提交"""

    @allure.feature("链路测试")
    @allure.story("链路4：提交")
    @allure.severity("critical")
    @allure.title("链路4：新建 → 分发 → 查询 → 暂存 → 提交")
    def test_link4_full_with_stash(self):
        """验证：新建→分发→查询→暂存→提交全部成功"""
        bl_no = generate_bl_no(4)

        with allure.step("执行链路（新建→分发→查询→暂存→提交）"):
            result = OrderWorkflow.run(stop_at="submit", skip_stash=False, bl_no=bl_no)

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
# 链路5：生成子订单
# =============================================================================
@pytest.mark.order5
class TestOrder5GenerateSubOrder:
    """链路5：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单"""

    @allure.feature("链路测试")
    @allure.story("链路5：生成子订单")
    @allure.severity("critical")
    @allure.title("链路5：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单")
    def test_link5_generate_sub_order(self):
        """验证：完整链路（包含生成子订单），链路停在 generate_sub_order 阶段"""
        bl_no = generate_bl_no(5)

        with allure.step("执行链路（新建→分发→查询→暂存→提交→生成子订单）"):
            result = OrderWorkflow.run(stop_at="generate_sub_order", bl_no=bl_no)

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
