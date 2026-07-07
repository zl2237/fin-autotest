# -*- coding: utf-8 -*-
"""
Rewrite testcases/receive_pay/*.py following pay_receive/* style.
Only touches receive_pay/ tests. Uses a Python script to avoid encoding issues.
"""
from pathlib import Path

BASE_DIR = Path(r"d:/CODE/PyCharm/pythonProject/pr_study/testcases/receive_pay")

STOPS = [
    "receive_account",
    "confirm_account",
    "invoice_batch",
    "invoice_batch_audit",
    "invoice_upload",
    "receive_writeoff",
    "payable",
    "confirm_payable",
    "payable_invoice_apply",
    "payable_invoice_register",
    "pay_demand",
    "pay_demand_audit",
    "pay_writeoff",
]

STOP_ASSERT = {
    "receive_account": "_assert_receive_account_ok",
    "confirm_account": "_assert_confirm_receive_ok",
    "invoice_batch": "_assert_receive_invoice_apply_ok",
    "invoice_batch_audit": "_assert_receive_invoice_batch_audit_ok",
    "invoice_upload": "_assert_receive_invoice_register_ok",
    "receive_writeoff": "_assert_receive_writeoff_ok",
    "payable": "_assert_payable_account_ok",
    "confirm_payable": "_assert_confirm_payable_ok",
    "payable_invoice_apply": "_assert_pay_demand_ok",
    "payable_invoice_register": "_assert_payable_invoice_apply_ok",
    "pay_demand": "_assert_pay_demand_audit_ok",
    "pay_demand_audit": "_assert_pay_writeoff_ok",
    "pay_writeoff": "_assert_pay_writeoff_ok",
}

ZH = {
    "receive_account_run": "执行完整订单流程，运行至发起应收对账批次节点 receive_account",
    "confirm_account_run": "执行完整订单流程，运行至确认应收节点 confirm_account",
    "invoice_batch_run": "执行完整订单流程，运行至应收开票批次节点 invoice_batch",
    "invoice_batch_audit_run": "执行完整订单流程，运行至审核生成开票申请节点 invoice_batch_audit",
    "invoice_upload_run": "执行完整订单流程，运行至应收发票上传登记节点 invoice_upload",
    "receive_writeoff_run": "执行完整订单流程，运行至应收核销节点 receive_writeoff",
    "payable_run": "执行完整订单流程，运行至应付对账节点 payable",
    "confirm_payable_run": "执行完整订单流程，运行至确认应付对账节点 confirm_payable",
    "payable_invoice_apply_run": "执行完整订单流程，运行至发起应付开票批次申请节点 payable_invoice_apply",
    "payable_invoice_register_run": "执行完整订单流程，运行至应付发票上传与登记节点 payable_invoice_register",
    "pay_demand_run": "执行完整订单流程，运行至发起付款需求节点 pay_demand",
    "pay_demand_audit_run": "执行完整订单流程，运行至审核生成付款单节点 pay_demand_audit",
    "pay_writeoff_run": "执行完整订单流程，运行至付款单核销节点 pay_writeoff",
    "prerequisite_link12": "校验：订单 1~12 前置流程全部完成",
    "prerequisite_audit": "校验：审核及费用单据信息",
    "stop_at_check": "校验流程终止节点",
    "execution_order_prefix": "执行顺序：",
    "prerequisite_prefix": "前置条件：",
}

EXEC_ORDER_DESC = {
    "receive_account": "订单 1~12 步 + 应收 1~2 步",
    "confirm_account": "订单 1~12 步 + 应收 1~2 步",
    "invoice_batch": "订单 1~12 步 + 应收 1~3 步",
    "invoice_batch_audit": "订单 1~12 步 + 应收 1~4 步",
    "invoice_upload": "订单 1~12 步 + 应收 1~4 步",
    "receive_writeoff": "订单 1~12 步 + 应收 1~5 步",
    "payable": "订单 1~12 步 + 应收 1~6 步 + 应付 1 步",
    "confirm_payable": "订单 1~12 步 + 应收 1~6 步 + 应付 1~2 步",
    "payable_invoice_apply": "订单 1~12 步 + 应收 1~6 步 + 应付 1~3 步",
    "payable_invoice_register": "订单 1~12 步 + 应收 1~6 步 + 应付 1~4 步",
    "pay_demand": "订单 1~12 步 + 应收 1~6 步 + 应付 1~5 步",
    "pay_demand_audit": "订单 1~12 步 + 应收 1~6 步 + 应付 1~6 步",
    "pay_writeoff": "订单 1~12 步 + 应收 1~6 步 + 应付 1~7 步",
}

PREREQ_DESC = {
    "receive_account": "订单 12 步完成",
    "confirm_account": "应收 1 步完成",
    "invoice_batch": "应收 2 步完成",
    "invoice_batch_audit": "应收 3 步完成",
    "invoice_upload": "应收 4 步完成",
    "receive_writeoff": "应收 4 步完成",
    "payable": "应收 4 步完成",
    "confirm_payable": "应付 1 步完成",
    "payable_invoice_apply": "应付 2 步完成",
    "payable_invoice_register": "应付 2 步完成",
    "pay_demand": "应付 3 步完成",
    "pay_demand_audit": "应付 3 步完成",
    "pay_writeoff": "应付发票已上传登记",
}

LINK_DESC = {
    "receive_account": "发起应收对账批次",
    "confirm_account": "确认应收对账批次",
    "invoice_batch": "发起应收开票批次申请",
    "invoice_batch_audit": "审核生成开票申请",
    "invoice_upload": "应收发票上传与登记",
    "receive_writeoff": "应收核销",
    "payable": "发起应付对账批次",
    "confirm_payable": "确认应付对账",
    "payable_invoice_apply": "发起应付开票批次申请",
    "payable_invoice_register": "应付发票上传与登记",
    "pay_demand": "发起付款需求",
    "pay_demand_audit": "审核生成付款单",
    "pay_writeoff": "付款单核销",
}

PREREQ_ASSERT = {
    0: "_assert_link12_prerequisite_ok",
    1: "_assert_link12_prerequisite_ok",
    2: "_assert_link12_prerequisite_ok",
    3: "_assert_link12_prerequisite_ok",
    4: "_assert_link12_prerequisite_ok",
    5: "_assert_link12_prerequisite_ok",
    6: "_assert_audit_and_fee_doc_ok",
    7: "_assert_audit_and_fee_doc_ok",
    8: "_assert_audit_and_fee_doc_ok",
    9: "_assert_audit_and_fee_doc_ok",
    10: "_assert_audit_and_fee_doc_ok",
    11: "_assert_audit_and_fee_doc_ok",
    12: "_assert_audit_and_fee_doc_ok",
}

PREREQ_STEP_TEXT = {
    "_assert_link12_prerequisite_ok": "校验：订单 1~12 前置流程全部完成",
    "_assert_audit_and_fee_doc_ok": "校验：审核及费用单据信息",
}

ASSERT_STEP_TEXT = {
    "receive_account": "校验：应收对账批次数据",
    "confirm_account": "校验：确认应收对账结果",
    "invoice_batch": "校验：应收开票申请批次数据",
    "invoice_batch_audit": "校验：应收开票批次审核通过",
    "invoice_upload": "校验：应收发票登记数据",
    "receive_writeoff": "校验：应收核销相关接口返回正常",
    "payable": "校验：应付对账数据",
    "confirm_payable": "校验：确认应付对账结果",
    "payable_invoice_apply": "校验：发起付款需求",
    "payable_invoice_register": "校验：发起应付开票批次申请",
    "pay_demand": "校验：审核生成付款单",
    "pay_demand_audit": "校验：付款单核销",
    "pay_writeoff": "校验：付款单核销",
}

CLASS_SUFFIX = {
    "receive_account": "ReceiveAccount",
    "confirm_account": "ConfirmAccount",
    "invoice_batch": "InvoiceBatch",
    "invoice_batch_audit": "InvoiceBatchAudit",
    "invoice_upload": "InvoiceUpload",
    "receive_writeoff": "ReceiveWriteoff",
    "payable": "PayableAccount",
    "confirm_payable": "ConfirmPayable",
    "payable_invoice_apply": "PayableInvoiceApply",
    "payable_invoice_register": "PayableInvoiceRegister",
    "pay_demand": "PayDemand",
    "pay_demand_audit": "PayDemandAudit",
    "pay_writeoff": "PayWriteoff",
}

RUN_STEP_TEXT = {
    "receive_account": "执行完整订单流程，运行至发起应收对账批次节点 receive_account",
    "confirm_account": "执行完整订单流程，运行至确认应收节点 confirm_account",
    "invoice_batch": "执行完整订单流程，运行至应收开票批次节点 invoice_batch",
    "invoice_batch_audit": "执行完整订单流程，运行至审核生成开票申请节点 invoice_batch_audit",
    "invoice_upload": "执行完整订单流程，运行至应收发票上传登记节点 invoice_upload",
    "receive_writeoff": "执行完整订单流程，运行至应收核销节点 receive_writeoff",
    "payable": "执行完整订单流程，运行至应付对账节点 payable",
    "confirm_payable": "执行完整订单流程，运行至确认应付对账节点 confirm_payable",
    "payable_invoice_apply": "执行完整订单流程，运行至发起应付开票批次申请节点 payable_invoice_apply",
    "payable_invoice_register": "执行完整订单流程，运行至应付发票上传与登记节点 payable_invoice_register",
    "pay_demand": "执行完整订单流程，运行至发起付款需求节点 pay_demand",
    "pay_demand_audit": "执行完整订单流程，运行至审核生成付款单节点 pay_demand_audit",
    "pay_writeoff": "执行完整订单流程，运行至付款单核销节点 pay_writeoff",
}


def build_imports(needed):
    parts = [
        "import allure",
        "import pytest",
        "",
        "from data.order import BookRealAmountData",
        "from utils import generate_bl_no",
        "from workflows.receive_pay_workflow import ReceivePayWorkflow",
        "",
    ]
    if needed:
        parts.append("from testcases.receive_pay.helpers import (")
        for item in sorted(set(needed)):
            parts.append("    {},".format(item))
        parts.append(")")
        parts.append("")
    return "\n".join(parts)


def build_fee_config():
    return '''def _build_fee_config():
    return {
        "to_customer_fees": BookRealAmountData.get_customer_standard_fees(),
        "to_supplier_fees": BookRealAmountData.get_supplier_standard_fees(),
    }
'''


def build_file(index, stop_at):
    needed = {PREREQ_ASSERT[index]}
    for idx in range(index + 1):
        needed.add(STOP_ASSERT[STOPS[idx]])

    lines = []
    lines.append('"""')
    lines.append("测试链路 {}：订单+应收（receive_pay），{}".format(21 + index, LINK_DESC[stop_at]))
    lines.append("{}{}".format(ZH["execution_order_prefix"], EXEC_ORDER_DESC[stop_at]))
    lines.append("{}{}".format(ZH["prerequisite_prefix"], PREREQ_DESC[stop_at]))
    lines.append('"""')
    lines.append("")
    lines.append(build_imports(needed))
    lines.append(build_fee_config())

    class_suffix = CLASS_SUFFIX[stop_at]
    class_name = "TestOrderReceivePay{}{}".format(index + 1, class_suffix)
    method_name = "test_order_receive_pay{}_{}".format(index + 1, stop_at)
    bl_no = 201 + index
    run_text = RUN_STEP_TEXT[stop_at]

    lines.append("@pytest.mark.order_receive_pay{}".format(index + 1))
    lines.append("class {}:".format(class_name))
    lines.append("")
    lines.append("    @allure.severity(\"critical\")")
    lines.append("    def {}(self):".format(method_name))
    lines.append("        bl_no = generate_bl_no({})".format(bl_no))
    lines.append("")
    lines.append('        with allure.step("{}"):'.format(run_text))
    lines.append("            result = ReceivePayWorkflow.run(")
    lines.append('                stop_at="{}",'.format(stop_at))
    lines.append("                bl_no=bl_no,")
    lines.append("                fee_configs=[_build_fee_config()],")
    lines.append("            )")
    lines.append("")

    prereq = PREREQ_ASSERT[index]
    lines.append('        with allure.step("{}"):'.format(PREREQ_STEP_TEXT[prereq]))
    lines.append("            {}(result)".format(prereq))
    lines.append("")

    for idx in range(index + 1):
        s = STOPS[idx]
        lines.append('        with allure.step("{}"):'.format(ASSERT_STEP_TEXT[s]))
        lines.append("            {}(result)".format(STOP_ASSERT[s]))
        lines.append("")

    stop_at_check = ZH["stop_at_check"]
    lines.append('        with allure.step("{}"):'.format(stop_at_check))
    lines.append('            assert result["stop_at"] == "{}"'.format(stop_at))

    return "\n".join(lines)


def main():
    for index, stop_at in enumerate(STOPS):
        content = build_file(index, stop_at)
        path = BASE_DIR / "test_order_receive_pay{}.py".format(index + 1)
        path.write_text(content, encoding="utf-8")
        print("written: {}".format(path))


if __name__ == "__main__":
    main()
