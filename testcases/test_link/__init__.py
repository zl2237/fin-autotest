"""test_link 子包 - 按业务域拆分的链路测试。

与 workflows/steps/ 子包镜像：
  test_order_basic.py        ↔ order_steps      (link1~5)
  test_fee.py                ↔ fee_steps        (link6)
  test_audit.py              ↔ audit_steps      (link7~10)
  test_fee_notice_confirm.py ↔ fee_steps        (link11~12)
  test_billing.py            ↔ billing_steps    (link13~14)
  test_invoice.py            ↔ invoice_steps    (link15~17)
  test_writeoff.py           ↔ writeoff_steps   (link18)

每个测试文件以 `import allure / pytest / OrderWorkflow / BookRealAmountData`
即可工作；这里把所有测试共享的导入集中在 conftest.py，仅作为统一入口。
"""
