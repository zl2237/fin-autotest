"""
订单流程业务子模块（workflows/order/）

本子包（非应收链路）：
- order_steps     订单基础：create_and_distribute / stash / submit / generate_sub_order
- audit_steps     审批：record_audit / record_order_lock / record_invoice_apply / record_supplier_advance
- fee_steps       费用：record_fee / record_generate_fee_notice / record_generate_fee_confirm

应收链路在 workflows/receive/ 子包：
- receive_account_steps      应收对账：record_receive_account / record_confirm_account
- receive_apply_steps        开票申请：record_invoice_batch / record_invoice_batch_audit
- receive_invoice_register_steps 发票登记：record_invoice_upload
- receive_writeoff_steps    核销：    record_receive_writeoff

主文件 workflows/order_workflow.py 保留 _attach_context / run / run_until_xxx
作为编排门面，对外 API 不变。

历史说明：原 workflows/steps/ 已重命名为 workflows/order/（"steps" 太通用，
不能体现业务域；"order" 与 api/order/、data/order/、testcases/ 根目录的 test_order_*.py
保持同构）。
"""

from .order_steps import (
    create_and_distribute,
    stash,
    submit,
    generate_sub_order,
)
from .audit_steps import (
    record_audit,
    record_order_lock,
    record_invoice_apply,
    record_supplier_advance,
)
from .fee_steps import (
    record_fee,
    record_generate_fee_notice,
    record_generate_fee_confirm,
)

__all__ = [
    "create_and_distribute",
    "stash",
    "submit",
    "generate_sub_order",
    "record_audit",
    "record_order_lock",
    "record_invoice_apply",
    "record_supplier_advance",
    "record_fee",
    "record_generate_fee_notice",
    "record_generate_fee_confirm",
]
