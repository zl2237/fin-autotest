"""
Workflows 层 - 业务流程编排

职责：
- 将多个 API 调用按业务顺序串联
- 自动处理步骤间的数据依赖（如新增返回的 order_id 供分发使用）
- 每个 workflow 函数返回完整上下文，供测试用例断言

Workflow 类型：
- OrderWorkflow：订单基础流程（order1~12）
- PayReceiveWorkflow：默认 workflow，订单 → 应付 → 应收（order_pay_receive1~13）
- ReceivePayWorkflow：可选 workflow，订单 → 应收 → 应付（order_receive_pay1~13）

使用方式：
    from workflows.pay_receive_workflow import PayReceiveWorkflow
    from workflows.receive_pay_workflow import ReceivePayWorkflow

    result = PayReceiveWorkflow.run(stop_at='pay_writeoff')
    assert result["pay_writeoff_result"]["pay_writeoff_data"]["code"] == 200

    result = ReceivePayWorkflow.run(stop_at='receive_writeoff')
    assert result["receive_writeoff_result"]["writeoff_batch_data"]["code"] == 200
"""

from .order_workflow import OrderWorkflow
from .pay_receive_workflow import PayReceiveWorkflow
from .receive_pay_workflow import ReceivePayWorkflow

__all__ = ["OrderWorkflow", "PayReceiveWorkflow", "ReceivePayWorkflow"]
