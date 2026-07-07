"""testcases 根 fixture 入口。

pytest 的 conftest.py 只对 fixture 自动可见，普通 import 无效。
因此本文件目前为空，无公共 fixture。
后续若新增需要跨 link 复用的 fixture（如 order_workflow_setup、fee_config_for_link 等），请在这里添加。

每个测试文件都通过 import 显式引入 allure / pytest / OrderWorkflow /
BookRealAmountData 等，符合 pytest 的固定约定。
"""
