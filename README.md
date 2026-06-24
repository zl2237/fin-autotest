# PR Study - 接口自动化测试框架

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的 25 条链路。

**核心能力：**
- 25 条链路（link1~link25），按依赖顺序递增，link25 隐含 link1~link24
- workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）
- 所有业务配置参数集中存储于 YAML，Python 代码零硬编码
- GUI 工具支持弹窗配置、实时日志、批量循环执行
- CI 环境自动企微机器人通知

---

## 目录结构

```
pr_study/
├── api/                        # API 层（按业务域组织）
│   ├── order/                  # 订单域
│   ├── receive/               # 应收域
│   └── pay/                    # 付款域
│
├── config/
│   └── settings.py            # 全局配置（.env 加载）
│
├── core/
│   └── http_client.py         # HTTP 客户端
│
├── data/                       # 数据层（YAML 配置 + 数据类）
│   ├── order/                 # 订单基础、费用、审批流、费用通知单、费用确认单
│   ├── receive/               # 应收对账、开票、核销
│   ├── pay/                   # 应付对账、开票、付款需求、核销
│   └── attachment/            # 测试附件（发票 PDF）
│
├── testcases/                 # 测试用例层
│   ├── order/                 # 链路 1~12
│   ├── receive/               # 链路 13~18
│   └── pay/                   # 链路 19~25
│
├── workflows/                 # 流程编排层
│   ├── order_workflow.py      # 全流程编排入口
│   ├── order/                 # 订单域步骤
│   ├── receive/               # 应收域步骤
│   └── pay/                   # 付款域步骤
│
├── conftest.py                # pytest 全局配置（登录、JSON 摘要）
├── notify.py                  # 企微机器人通知
├── pytest.ini                 # pytest 配置（标记定义）
├── GUI.py                     # GUI 测试工具（exe 打包入口）
├── .env.example               # 环境变量模板
└── requirements.txt           # Python 依赖
```

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| pytest | >=7.4.0 | 测试框架 |
| requests | >=2.31.0 | HTTP 客户端 |
| loguru | >=0.7.2 | 日志记录 |
| allure-pytest | >=2.13.2 | 测试结果收集 |
| python-dotenv | >=1.0.0 | 环境变量加载 |
| PyYAML | >=6.0 | YAML 配置解析 |

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
copy .env.example .env
# 编辑 .env，填入 BASE_URL、USERNAME、PASSWORD、ORDER_CREATE_ID
```

| 配置项 | 说明 |
|--------|------|
| `BASE_URL` | API 基础域名 |
| `USERNAME` / `PASSWORD` | 登录凭证（敏感） |
| `ORDER_CREATE_ID` | 操作员用户ID |
| `TOKEN_FIELD` | Token 字段路径（默认 `data.token`） |

> `.env` 已加入 `.gitignore`，不会推送。

### 3. 运行测试

```bash
pytest -v                          # 运行全部
pytest -m link1                    # 仅链路1
pytest -m "link11 or link12"       # 同时跑多条
pytest -m link25                   # 从链路25（包含所有前置步骤）
```

### 4. 测试结果

- **终端**：通过 / 失败 / 跳过数量汇总，失败用例详情
- **JSON 摘要**：`report/allure-results/test_summary.json`
- **企微通知**：CI 环境自动触发，本地不触发

---

## 链路一览（25 条）

| 链路 | 停止阶段 | 链路 | 停止阶段 |
|------|----------|------|----------|
| link1 | 新建 | link14 | 确认应收对账 |
| link2 | 分发 | link15 | 发起应收开票批次审批 |
| link3 | 暂存 | link16 | 审核生成开票申请 |
| link4 | 提交 | link17 | 发票上传与登记 |
| link5 | 生成子订单 | link18 | 应收核销 |
| link6 | 录费用 | link19 | 发起应付对账批次 |
| link7 | 资产推送审批 | link20 | 确认应付对账 |
| link8 | 订单锁定审批 | link21 | 发起应付开票批次申请 |
| link9 | 未放款开票申请审批 | link22 | 应付发票上传与登记 |
| link10 | 供应商垫付申请审批 | link23 | 发起付款需求 |
| link11 | 生成费用通知单 | link24 | 审核生成付款单 |
| link12 | 生成费用确认单 | link25 | 付款单核销 |
| link13 | 发起应收对账批次 | | |

> 链路按依赖顺序递增，link25 隐含 link1~link24 的全部步骤。

---

## 快捷方法

`OrderWorkflow` 提供 `run_until_xxx` 系列方法：

```python
from workflows.order_workflow import OrderWorkflow

OrderWorkflow.run_until_distribute()              # link2
OrderWorkflow.run_until_stash()                  # link3
OrderWorkflow.run_until_generate_sub_order()     # link5
OrderWorkflow.run_until_record_fee(...)          # link6
OrderWorkflow.run_until_fee_notice()             # link11
OrderWorkflow.run_until_fee_confirm()            # link12
OrderWorkflow.run_until_receive_account()        # link13
OrderWorkflow.run_until_confirm_account()       # link14
OrderWorkflow.run_until_invoice_batch()         # link15
OrderWorkflow.run_until_invoice_batch_audit()  # link16
OrderWorkflow.run_until_invoice_upload()        # link17
OrderWorkflow.run_until_receive_writeoff()       # link18
OrderWorkflow.run_until_payable_account()       # link19
OrderWorkflow.run_until_confirm_payable()       # link20
OrderWorkflow.run_until_payable_invoice_apply()  # link21
OrderWorkflow.run_until_payable_invoice_register()  # link22
OrderWorkflow.run_until_pay_demand()           # link23
OrderWorkflow.run_until_pay_demand_audit()      # link24
OrderWorkflow.run_until_pay_writeoff()          # link25
```

---

## 分层架构

| 层级 | 目录 | 职责 |
|------|------|------|
| API 层 | `api/` | 封装单个 HTTP 接口调用 |
| 数据层 | `data/` | 提供测试数据；所有业务参数从 YAML 读取 |
| 流程编排层 | `workflows/` | 串联多个 API，自动处理步骤间数据依赖 |
| 测试用例层 | `testcases/` | 调用 workflows，按业务阶段组合测试 |

---

## GUI 工具

使用打包后的 `PRStudy.exe`（由 `GUI.py` 生成）可图形化运行：

- 弹窗配置账号、链路、循环次数
- 实时日志展示执行进度
- 配置自动保存 / 回填

打包命令：

```bash
pyinstaller --onefile --noconsole GUI.spec
```
