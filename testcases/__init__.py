"""Testcases 层 - 测试用例根包

按业务域分目录：
  testcases/order/    订单基础、录费用、费用通知单/确认单、审批流
  testcases/pay/    应付对账（link19/20）、应付开票申请（link21）、应付发票上传与登记（link22）
  testcases/receive/ 应收对账（link13/14）、应收发票（link15/16/17）、应收核销（link18）

与目录层级对应：api/order/、api/pay/、api/receive/
"""

# 各子包通过子目录 __init__.py 组织，此文件仅作为根包标识
