"""testcases/test_link 公共 fixture 入口。

pytest 的 conftest.py 只对 fixture 自动可见，对普通 import 无效。
故本文件目前为空（无共享 fixture），未来如果抽出公共 fixture（如
`order_workflow_setup`、`fee_config_for_link` 等）会加在这里。

每个测试文件仍需自行 import 其依赖（allure / pytest / OrderWorkflow /
BookRealAmountData），这是 pytest 的固定约束。
"""
