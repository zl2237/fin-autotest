# PR Study - 接口自动化测试框架

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试。

## 项目简介

本项目是一套面向物流管理系统的接口自动化测试框架，采用分层设计（API 层、数据层、workflows 层、用例层），支持订单的新增、查询、分发、暂存、提交、生成子订单、录费用、资产推送审批等全流程测试。

**核心能力：**
- 完整的订单生命周期测试（新建 → 分发 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批）
- workflows 层自动处理步骤间数据依赖，资产推送审批内嵌于录费用阶段
- 支持多种运行方式（全部运行、按标记运行、单独运行）
- 测试结果自动写入 JSON，企微机器人通知
- 全局登录会话管理

---

## 目录结构

```
pr_study/
├── api/                          # API 层
│   ├── order.py                  # 订单相关接口封装
│   └── audit_api.py             # 审批流相关接口封装
│
├── config/                       # 配置层
│   └── settings.py               # 全局配置（加载 .env）
│
├── core/                         # 核心模块
│   └── http_client.py            # HTTP 客户端封装
│
├── data/                         # 数据层
│   ├── order.yaml               # 订单基础数据配置
│   ├── order_data.py            # 订单测试数据（字段分层设计）
│   ├── fee.yaml                 # 录费用配置
│   ├── audit.yaml               # 审批流配置
│   └── audit_data.py            # 审批流测试数据
│
├── testcases/                    # 测试用例层
│   └── test_link.py             # 链路测试（7条链路，按需选择执行）
│
├── utils/                        # 工具模块
│   ├── logger.py                # 日志工具
│   └── file_util.py             # 文件操作工具
│
├── workflows/                    # 流程编排层（自动处理步骤间数据依赖）
│   └── order_workflow.py        # 订单全流程：新建→分发→暂存→提交→生成子订单→录费用→资产推送审批
│
├── conftest.py                   # pytest 全局配置（登录、报告生成）
├── notify.py                     # 企微机器人通知脚本
├── pytest.ini                    # pytest 配置文件
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git 忽略配置
├── .gitlab-ci.yml                # GitLab CI/CD 配置（link7 冒烟）
└── requirements.txt              # Python 依赖
```

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| pytest | >=7.4.0 | 测试框架 |
| requests | >=2.31.0 | HTTP 客户端 |
| loguru | >=0.7.2 | 日志记录 |
| allure-pytest | >=2.13.2 | 测试结果收集 |
| python-dotenv | >=1.0.0 | 环境变量（可选） |

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
# 运行全部链路
pytest testcases/test_link.py -v

# 运行指定链路
pytest testcases/test_link.py -m link1   # 链路1：新建
pytest testcases/test_link.py -m link2   # 链路2：新建 → 分发
pytest testcases/test_link.py -m link3   # 链路3：新建 → 分发 → 查询 → 暂存
pytest testcases/test_link.py -m link4   # 链路4：新建 → 分发 → 查询 → 暂存 → 提交
pytest testcases/test_link.py -m link5   # 链路5：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单
pytest testcases/test_link.py -m link6   # 链路6：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用
pytest testcases/test_link.py -m link7   # 链路7：新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批
```

### 4. 测试结果

pytest 运行结束后：

- **本地**：终端输出汇总（通过/失败/跳过数量），失败用例详情
- **JSON**：测试摘要写入 `report/allure-results/test_summary.json`（由 `conftest.py` 生成）
- **企微通知**：CI 环境下自动调用 `notify.py` 发送机器人消息

> 本地运行时不发企微通知（`notify.py` 依赖 CI 环境变量），手动验证可跳过。

---

## pytest 标记使用

### 预定义标记

| 标记 | 说明 |
|------|------|
| `link1` | 链路1：新建 |
| `link2` | 链路2：新建 + 分发 |
| `link3` | 链路3：新建 + 分发 + 查询 + 暂存 |
| `link4` | 链路4：新建 + 分发 + 查询 + 暂存 + 提交 |
| `link5` | 链路5：新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 |
| `link6` | 链路6：新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 |
| `link7` | 链路7：新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 + 资产推送审批 |

### 目录结构说明

| 层级 | 目录 | 职责 |
|------|------|------|
| API 层 | `api/` | 封装单个接口调用 |
| 数据层 | `data/` | 提供测试数据和载荷构建 |
| 流程编排层 | `workflows/` | 串联多个 API，处理步骤间依赖，返回完整上下文 |
| 测试用例层 | `testcases/` | 调用 workflows，按业务阶段组合测试 |

---

## API 接口说明

### 订单 API (`api/order.py`)

| 方法 | 接口 | 说明 |
|------|------|------|
| `get_entrust_order_list()` | POST /api/order/orderEntrust/orderPage | 委托订单列表 |
| `get_business_order_list()` | POST /api/order/order/orderPage | 业务订单列表 |
| `get_order_by_bl_no()` | - | 按提单号查询订单 |
| `add_order()` | POST /api/order/orderEntrust/orderAdd | 新增订单 |
| `distribute_order()` | POST /api/order/orderEntrust/orderAdd | 分发订单 |
| `submit_order()` | POST /api/order/order/orderAdd | 提交订单 |
| `generate_sub_order()` | POST /api/order/order/generateOrderSub | 生成子订单 |

### 审批 API (`api/audit_api.py`)

| 方法 | 接口 | 说明 |
|------|------|------|
| `send_audit()` | POST /api/order/orderFee/assetPush | 发起指定类型审批 |
| `send_asset_push()` | POST /api/order/orderFee/assetPush | 发起资产推送审批 |
| `query_pending_audits()` | POST /api/home/audit/auditPage | 查询审批列表 |
| `audit_execute()` | POST /api/home/audit/auditExecute | 执行审批（通过/拒绝） |

### 使用示例

```python
from api.order import OrderApi

# 新增订单
resp = OrderApi.add_order(bl_no="TEST_BL_001")

# 按提单号查询
order_info = OrderApi.get_order_by_bl_no("TEST_BL_001")

# 分发订单
resp = OrderApi.distribute_order(order_info, bl_no="TEST_BL_001")

# 提交订单
resp = OrderApi.submit_order(order_info, bl_no="TEST_BL_001")

# 生成子订单
resp = OrderApi.generate_sub_order(order_id="xxx")
```

---

## 测试用例说明

### test_link.py 链路列表

| 链路 | 步骤 | 说明 |
|------|------|------|
| `link1` | 新建 | 验证新建订单 API 正常 |
| `link2` | 新建 → 分发 | 验证分发功能正常，链路停在 distribute 阶段 |
| `link3` | 新建 → 分发 → 查询 → 暂存 | 验证暂存功能正常，链路停在 stash 阶段 |
| `link4` | 新建 → 分发 → 查询 → 暂存 → 提交 | 验证提交功能正常，链路停在 submit 阶段 |
| `link5` | 新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 | 停在生成子订单阶段 |
| `link6` | 新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 | 停在录费用阶段 |
| `link7` | 新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 → 录费用 → 资产推送审批 | 完整链路，停在录审批阶段 |
