"""
Workflows 层 - 业务流程编排

职责：
- 将多个 API 调用按业务顺序串联
- 自动处理步骤间的数据依赖（如新增返回的 order_id 供分发使用）
- 每个 workflow 函数返回完整上下文，供测试用例断言

使用方式：
    from workflows.order_workflow import OrderWorkflow

    result = OrderWorkflow.create_and_distribute()
    assert result["distribute_resp"].json()["code"] == 200

    result = OrderWorkflow.full_flow()
    assert result["submit_resp"].json()["code"] == 200
"""

from .order_workflow import OrderWorkflow

__all__ = ["OrderWorkflow"]
