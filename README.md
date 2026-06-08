# PR Study - 接口自动化测试框架

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试。

## 项目简介

本项目是一套面向物流管理系统的接口自动化测试框架，采用分层设计（API 层、数据层、用例层），支持订单的新增、查询、分发、提交等全流程测试。

**核心能力：**
- 完整的订单生命周期测试（新增 → 分发 → 提交）
- 支持多种运行方式（全部运行、按标记运行、单独运行）
- 测试结果自动写入 JSON，企微机器人通知
- 全局登录会话管理

---

## 目录结构

```
pr_study/
├── api/                          # API 层
│   └── order.py                  # 订单相关接口封装
│
├── config/                       # 配置层
│   └── settings.py               # 全局配置（加载 .env）
│
├── core/                         # 核心模块
│   └── http_client.py            # HTTP 客户端封装
│
├── data/                         # 数据层
│   ├── __init__.py               # 包初始化
│   └── order_data.py             # 订单测试数据（字段分层设计）
│
├── testcases/                    # 测试用例层
│   └── test_order.py             # 订单接口测试用例
│
├── utils/                        # 工具模块
│   ├── logger.py                 # 日志工具
│   └── file_util.py              # 文件操作工具
│
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git 忽略配置
├── .gitlab-ci.yml                # GitLab CI/CD 配置
├── conftest.py                   # pytest 全局配置（登录、报告生成）
├── notify.py                     # 企微机器人通知脚本
├── pytest.ini                    # pytest 配置文件
├── requirements.txt              # Python 依赖
└── README.md                     # 项目文档
```

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| pytest | ≥7.4.0 | 测试框架 |
| requests | ≥2.31.0 | HTTP 客户端 |
| loguru | ≥0.7.2 | 日志记录 |
| allure-pytest | ≥2.13.2 | 测试结果收集 |
| python-dotenv | ≥1.0.0 | 环境变量（可选） |

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

#### 方式一：使用 .env 文件（推荐，保护敏感数据）

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env，填入你的真实配置
```

#### 方式二：直接修改 settings.py（不推荐，敏感数据可能泄露）

编辑 `config/settings.py` 中的默认值。

#### 配置说明

| 配置项 | 说明 | 敏感程度 |
|--------|------|----------|
| `BASE_URL` | API 基础域名 | 低 |
| `USERNAME` | 登录账号 | 高 |
| `PASSWORD` | 登录密码 | 高 |
| `TOKEN_FIELD` | Token 字段路径 | 低 |
| `ORDER_CREATE_ID` | 操作员用户ID | 中 |

> **注意**：`.env` 文件已被 `.gitignore` 忽略，不会推送到仓库。

### 3. 运行测试

```bash
# 运行全部测试（需指定标记组合）
pytest -m "entrust or business or validation or add or distribute or submit or workflow"

# 运行指定测试类
pytest testcases/test_order.py::TestEntrustedOrder

# 运行指定测试用例
pytest testcases/test_order.py::TestEntrustedOrder::test_entrust_order_normal

# 运行带特定标记的测试（见标记使用章节）
pytest -m entrust
pytest -m "add or distribute"
```

### 4. 测试结果

pytest 运行结束后：

- **本地**：终端输出汇总（通过/失败/跳过数量），失败用例详情
- **JSON**：测试摘要写入 `report/allure-results/test_summary.json`（由 `conftest.py` 生成）
- **企微通知**：CI 环境下自动调用 `notify.py` 发送机器人消息

> 本地运行时不发企微通知（`notify.py` 依赖 CI 环境变量），手动验证可跳过。

---

## 数据层设计

### 字段分层架构

```
BaseOrderData (基础字段)
    │
    ├── 新增订单：直接使用基础字段
    │       └── AddOrderData.get_add_payload(bl_no)
    │
    ├── 分发订单：基础字段 + order_info
    │       └── DistributeOrderData.get_distribute_payload(order_info, bl_no)
    │
    └── 提交订单：基础字段 + SubmitRequiredFields (提交必填字段)
            └── SubmitOrderData.get_submit_payload(order_info, bl_no)
```

### 核心数据类

| 类名 | 用途 | 说明 |
|------|------|------|
| `BaseOrderData` | 基础字段 | 所有订单操作都需要的公共字段 |
| `SubmitRequiredFields` | 提交必填字段 | 仅提交时需要的业务字段，新增/分发时默认置空 |
| `AddOrderData` | 新增订单数据 | 基于 BaseOrderData |
| `DistributeOrderData` | 分发订单数据 | 基于 BaseOrderData + order_info |
| `SubmitOrderData` | 提交订单数据 | BaseOrderData + SubmitRequiredFields 合并 |

### 使用示例

```python
from data.order_data import (
    AddOrderData,
    DistributeOrderData,
    SubmitOrderData,
    BaseOrderData,
    SubmitRequiredFields,
    generate_bl_no
)

# ============== 新增订单 ==============
# 方式1: 仅基础字段（提交必填字段为空）
payload = AddOrderData.get_add_payload()

# 方式2: 基础字段 + 预填部分提交字段
payload = AddOrderData.get_add_payload_with_submit_fields(
    trade_term="FOB",
    carrier="MSC"
)

# 方式3: 完全自定义
payload = BaseOrderData.get_base_payload_with_overrides(
    trade_term="CIF",
    customer_id="12345"
)

# ============== 提交订单 ==============
# 标准提交
payload = SubmitOrderData.get_submit_payload(order_info, bl_no)

# 自定义部分提交字段
payload = SubmitOrderData.get_submit_payload_with_overrides(
    order_info,
    bl_no,
    trade_term="FOB",
    shipper="自定义发货人"
)
```

---

## pytest 标记使用

### 预定义标记

每个测试类对应一个独立标记，全部测试默认通过 `-m` 指定标记组合运行：

| 标记 | 对应测试类 | 说明 |
|------|-----------|------|
| `entrust` | `TestEntrustedOrder` | 委托订单列表查询、分页、排序 |
| `business` | `TestBusinessOrder` | 业务订单列表查询、分页、排序 |
| `validation` | `TestOrderDataValidation` | 订单数据完整性验证 |
| `add` | `TestAddOrder` | 新增订单接口 |
| `distribute` | `TestAddAndDistribute` | 订单分发流程 |
| `submit` | `TestSubmitOrder` | 订单提交接口 |
| `workflow` | `TestFullWorkflow` | 完整订单流程（新增→分发→提交） |

### 运行方式

**CI 默认命令（执行全部用例）：**
```bash
pytest -m "entrust or business or validation or add or distribute or submit or workflow"
```

**常用运行场景：**

```bash
# 运行全部测试
pytest -m "entrust or business or validation or add or distribute or submit or workflow"

# 仅查询类（委托+业务）
pytest -m "entrust or business"

# 仅新增+分发
pytest -m "add or distribute"

# 仅完整流程
pytest -m "workflow"

# 排除提交相关（适合接口不稳定时）
pytest -m "not submit"

# 指定测试类
pytest testcases/test_order.py::TestEntrustedOrder

# 指定测试用例
pytest testcases/test_order.py::TestEntrustedOrder::test_entrust_order_normal
```

---

## API 接口说明

### 订单 API (`api/order.py`)

| 方法 | 接口 | 说明 |
|------|------|------|
| `get_entrust_order_list()` | GET /api/order/orderEntrust/orderPage | 委托订单列表 |
| `get_business_order_list()` | GET /api/order/order/orderPage | 业务订单列表 |
| `get_order_by_bl_no()` | - | 按提单号查询订单 |
| `add_order()` | POST /api/order/orderEntrust/orderAdd | 新增订单 |
| `distribute_order()` | POST /api/order/orderEntrust/orderAdd | 分发订单 |
| `submit_order()` | POST /api/order/order/orderAdd | 提交订单 |

### 使用示例

```python
from api.order import OrderApi

# 查询委托订单列表
resp = OrderApi.get_entrust_order_list(page_no=1, page_size=20)

# 新增订单
resp = OrderApi.add_order(bl_no="TEST_BL_001")

# 按提单号查询
order_info = OrderApi.get_order_by_bl_no("TEST_BL_001")

# 分发订单
resp = OrderApi.distribute_order(order_info, bl_no="TEST_BL_001")

# 提交订单
resp = OrderApi.submit_order(order_info, bl_no="TEST_BL_001")
```

---

## 测试用例说明

### 用例类列表

| 类名 | 测试范围 |
|------|----------|
| `TestEntrustedOrder` | 委托订单列表查询、分页、排序 |
| `TestBusinessOrder` | 业务订单列表查询、分页、排序 |
| `TestOrderDataValidation` | 订单数据完整性验证 |
| `TestAddOrder` | 新增订单接口测试 |
| `TestAddAndDistribute` | 新增并分发流程测试 |
| `TestSubmitOrder` | 提交订单接口测试 |
| `TestFullWorkflow` | 完整订单流程测试 |

---

## 日志与报告

### 日志输出

- 位置：`report/logs/auto_test_YYYYMMDD_HHMMSS.log`
- 保留天数：7 天

### 测试结果

- 结果目录：`report/allure-results/`（Allure JSON 格式）
- 摘要文件：`report/allure-results/test_summary.json`（conftest.py 自动生成）
- 企微通知：CI 环境下由 `notify.py` 读取摘要后发送

### 企微通知配置

在 GitLab CI/CD Variables 中配置：

| 变量名 | 说明 |
|--------|------|
| `WECOM_WEBHOOK_URL` | 企业微信群机器人 webhook 地址 |
| `WECOM_MENTIONED_LIST` | 可选，被 @ 的用户手机号，逗号分隔 |

---

## GitLab CI/CD

### 流水线阶段

| 阶段 | 说明 |
|------|------|
| `lint` | flake8 代码检查（E9/F63/F7/F82 级别错误） |
| `smoke_test` | pytest 执行全部标记用例，结果写入 JSON，artifacts 保留 7 天 |
| `notify` | 调用 `notify.py` 发送企微机器人通知 |

### 触发规则

CI 在以下场景触发：
- push 到任意分支
- MR 合并请求
- main / master 分支推送
- feat / bugfix / hotfix 前缀分支推送

### 流程说明

```
lint ──(失败则中断)── smoke_test ──(always)── notify
                              │
                              └── report/ (artifacts，7天)
                                          │
                                          └── notify.py 读取 test_summary.json
```

---

## 常见问题

### Q: 如何配置登录账号密码？

**方式一（推荐）：.env 文件**
```bash
cp .env.example .env
# 编辑 .env 填入真实配置
```

**方式二：直接修改 settings.py**

编辑 `config/settings.py` 中的默认值。

### Q: `.env` 文件会泄露吗？

不会。该文件已被 `.gitignore` 忽略，不会推送到仓库。

### Q: 如何修改测试数据？
编辑 `data/order_data.py` 中对应数据类的常量，或在调用时传入自定义参数。

### Q: 如何跳过登录？
`conftest.py` 中的 `global_login` fixture 负责登录，可根据需要修改。

### Q: 如何添加新的接口？
1. 在 `api/` 下创建新的 API 类
2. 在 `data/` 下创建对应的测试数据类
3. 在 `testcases/` 下编写测试用例

---

## License

MIT
