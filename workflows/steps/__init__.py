"""
订单流程业务子模块

把 OrderWorkflow 原本的内联 18 个 record_* 方法按业务域拆到本子包的 6 个模块，
主文件 workflows/order_workflow.py 保留 _attach_context / full_flow / run / run_until_xxx
作为编排门面，对外 API 不变。

子模块：
- order_steps     订单基础：create_and_distribute / stash / submit / generate_sub_order
- audit_steps     审批：record_audit / record_order_lock / record_invoice_apply / record_supplier_advance
- fee_steps       费用：record_fee / record_generate_fee_notice / record_generate_fee_confirm
- billing_steps   应收对账：record_receive_account / record_confirm_account
- invoice_steps   发票：record_invoice_batch / record_invoice_batch_audit / record_invoice_upload
- writeoff_steps  核销：record_receive_writeoff
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
from .billing_steps import (
    record_receive_account,
    record_confirm_account,
)
from .invoice_steps import (
    record_invoice_batch,
    record_invoice_batch_audit,
    record_invoice_upload,
)
from .writeoff_steps import (
    record_receive_writeoff,
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
    "record_receive_account",
    "record_confirm_account",
    "record_invoice_batch",
    "record_invoice_batch_audit",
    "record_invoice_upload",
    "record_receive_writeoff",
]
