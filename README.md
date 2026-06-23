# PR Study - 接口自动化测试框架

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试。

## 项目简介

本项目面向物流管理系统，采用分层设计，支持从**新建订单**到**审核生成付款单**的 24 条链路端到端测试，覆盖订单全生命周期、审批流、费用单生成、发票上传与登记、应收核销、应付对账、应付开票申请、应付发票上传与登记、发起付款需求、审核生成付款单。

**核心能力：**
- 24 条链路，覆盖从新建到审核生成付款单完整流程（按需执行，灵活组合）
- workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）
- 资产推送审批 / 订单锁定审批 / 未放款开票申请审批 / 供应商垫付申请审批 内嵌于链路流程
- 所有业务配置参数集中存储于 YAML 文件（订单、费用、审批流、费用通知单、费用确认单、对账、开票、应收核销、应付对账、应付开票申请、应付发票上传与登记），Python 代码零硬编码
- 测试结果写入 JSON + Allure 报告，CI 环境自动企微机器人通知
- 全局登录会话管理

---

## 目录结构

```
pr_study/
├── api/                          # API 层
│   ├── order/                    # 订单域（order）
│   │   ├── order_api.py         # 订单接口封装（含费用通知单、费用确认单）
│   │   └── audit_api.py         # 审批流接口封装
│   ├── receive/                  # 应收域（receive）
│   │   ├── receive_account_api.py # 财务应收对账接口封装
│   │   ├── invoice_batch_api.py # 应收开票批次接口封装
│   │   ├── invoice_upload_api.py# 应收发票上传与登记接口封装
│   │   └── receive_writeoff_api.py  # 应收核销接口封装
│   └── pay/                     # 付款域（pay）
│       ├── payable_api.py        # 应付对账批次接口封装（含 LK19/20/21/22/23/24 全链路）
│       ├── pay_demand_api.py     # 发起付款需求接口封装（LK23）
│       ├── pay_demand_audit_api.py # 审核生成付款单接口封装（LK24）
│       └── __init__.py
│
├── config/                       # 配置层
│   └── settings.py               # 全局配置（BASE_URL、登录凭证等，支持 .env）
│
├── core/                         # 核心模块
│   └── http_client.py            # HTTP 客户端（统一拦截、日志）
│
├── data/                         # 数据层
│   ├── order/                    # 订单域
│   │   ├── order.yaml           # 订单基础数据、提交字段、箱型模板
│   │   ├── fee.yaml             # 录费用配置（客户应收、供应商应付、默认值）
│   │   ├── audit.yaml           # 审批流配置（资产推送、订单锁定、开票申请、垫付申请）
│   │   ├── fee_notice.yaml      # 费用通知单配置
│   │   ├── fee_confirm.yaml     # 费用确认单配置
│   │   ├── order_data.py        # 订单数据类（载荷构建，常量导出）
│   │   └── audit_data.py        # 审批数据类（载荷构建）
│   ├── receive/                  # 应收域
│   │   ├── receive_account.yaml      # 应收对账配置
│   │   ├── receive_invoice.yaml      # 应收开票批次配置
│   │   ├── receive_invoice_upload.yaml  # 应收发票上传与登记配置
│   │   ├── receive_writeoff.yaml     # 应收核销配置
│   │   └── receive_data.py       # 应收数据类（载荷构建，常量导出）
│   └── pay/                     # 付款域（应付对账 + 应付开票申请 + 应付发票上传与登记 + 发起付款需求 + 审核生成付款单）
│       ├── pay_account.yaml       # 应付对账配置（LK19 / LK20）
│       ├── payable_invoice.yaml   # 应付开票申请配置（LK21）
│       ├── payable_invoice_upload.yaml  # 应付发票上传与登记配置（LK22）
│       ├── pay_demand.yaml       # 发起付款需求配置（LK23）
│       ├── pay_demand_audit.yaml # 审核生成付款单配置（LK24）
│       └── pay_data.py           # 应付数据类
│
├── data/attachment/              # 测试附件（发票 PDF 等）
│   ├── invoice.pdf               # 历史附件（保留）
│   ├── receive_invoice.pdf       # 应收发票上传附件（LK17）
│   └── pay_invoice.pdf           # 应付发票上传附件（LK22）
│
├── testcases/                   # 测试用例层（按业务域分子目录）
│   ├── __init__.py
│   ├── conftest.py
│   ├── order/                    # 订单域测试
│   │   ├── __init__.py
│   │   ├── test_order_basic.py   # 链路 1~5：订单基础（新建→分发→暂存→提交→生成子订单）
│   │   ├── test_fee.py           # 链路 6：录费用
│   │   ├── test_audit.py         # 链路 7~10：审批流（资产推送/订单锁定/未放款开票/供应商垫付）
│   │   └── test_fee_notice_confirm.py  # 链路 11~12：费用通知单 / 费用确认单
│   ├── receive/                  # 应收域测试
│   │   ├── __init__.py
│   │   ├── test_receive_account.py     # 链路 13~14：应收对账
│   │   ├── test_receive_invoice.py      # 链路 15~17：应收发票（开票批次→审核→上传登记）
│   │   └── test_receive_writeoff.py     # 链路 18：应收核销
│   └── pay/                      # 付款域测试
│       ├── __init__.py
│       └── test_pay.py           # 链路 19/20/21/22/23/24：应付对账、确认应付对账、应付开票申请、应付发票上传与登记、发起付款需求、审核生成付款单
│
├── utils/                       # 工具模块
│   ├── logger.py                # 日志工具
│   └── file_util.py             # 文件操作工具
│
├── workflows/                   # 流程编排层
│   ├── order_workflow.py        # 订单全流程编排（新建→分发→暂存→提交→子订单→录费用→审批→费用单→对账→开票→发票上传→应收核销→应付对账→确认应付对账→应付开票申请→应付发票上传与登记）
│   ├── run_pytest_loop.py        # 批量执行脚本来准备数据，需要传入link编号和循环次数
│   ├── order/                   # 订单域步骤
│   │   ├── order_steps.py       # 订单基础步骤
│   │   ├── audit_steps.py       # 审批步骤
│   │   └── fee_steps.py         # 费用步骤
│   ├── receive/                  # 应收域步骤
│   │   ├── receive_account_steps.py  # 应收对账步骤
│   │   ├── invoice_steps.py      # 发票步骤
│   │   └── writeoff_steps.py     # 应收核销步骤
│   └── pay/                      # 付款域步骤
│       ├── payable_steps.py      # 应付对账 / 应付开票申请 / 应付发票上传与登记步骤
│       ├── pay_demand_steps.py   # 发起付款需求步骤
│       └── pay_demand_audit_steps.py # 审核生成付款单步骤
│
├── conftest.py                  # pytest 全局配置（登录、报告生成、allure-results 自动清空）
├── notify.py                    # 企微机器人通知脚本
├── pytest.ini                   # pytest 配置（标记、报告路径）
├── .env.example                 # 环境变量模板
├── .gitignore                  # Git 忽略配置
├── .gitlab-ci.yml             # GitLab CI 配置
└── requirements.txt            # Python 依赖
```

### 三层对应的三子目录

`api/`、`data/`、`workflows/` 均按**业务域**组织为 3 个子包：

| 域 | 含义 | 内容 |
|---|---|---|
| `order/` | 订单基础 + 费用 + 审批 | 订单 CRUD、录费用、费用通知/确认单、审批流 |
| `receive/` | 应收（对账/开票/核销） | 对账批次、开票批次、发票上传、核销 |
| `pay/` | 应付（对账/开票/发票上传） | 应付对账、确认对账、应付开票申请、应付发票上传与登记 |

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

#### 使用 .env 文件（推荐，敏感数据不上传）

```bash
# 复制示例文件
copy .env.example .env

# 编辑 .env，填入真实配置
```

| 配置项 | 说明 | 敏感程度 |
|--------|------|----------|
| `BASE_URL` | API 基础域名 | 低 |
| `USERNAME` | 登录账号 | 高 |
| `PASSWORD` | 登录密码 | 高 |
| `TOKEN_FIELD` | Token 字段路径（如 `data.token`） | 低 |
| `ORDER_CREATE_ID` | 操作员用户ID | 中 |

> `.env` 文件已被 `.gitignore` 忽略，不会推送到仓库。

### 3. 运行测试

```bash
# 运行全部链路
pytest -v

# 按标记运行指定链路
pytest -m link1           # 仅链路1
pytest -m "link11 or link12"  # 同时跑多条
pytest -m link19           # 从链路19开始（包含LK1~LK18所有前置步骤）
```

### 4. 测试结果

- **终端**：通过 / 失败 / 跳过数量汇总，失败用例详情
- **Allure 报告**：`report/allure-results/`（由 pytest `--alluredir` 自动生成，运行前自动清空旧数据）
- **JSON 摘要**：`report/allure-results/test_summary.json`（由 `conftest.py` 生成）
- **企微通知**：CI 环境下自动调用 `notify.py` 发送机器人消息；本地运行不触发

---

## 链路说明

### 链路一览（24 条）

| 链路 | 停止阶段 | 覆盖步骤 |
|------|----------|----------|
| link1 | 新建 | 新建 |
| link2 | 分发 | 新建 → 分发 |
| link3 | 暂存 | 新建 → 分发 → 查询 → 暂存 |
| link4 | 提交 | 新建 → 分发 → 查询 → 暂存 → 提交 |
| link5 | 生成子订单 | 新建 → 分发 → 查询 → 暂存 → 提交 → 生成子订单 |
| link6 | 录费用 | ... → 生成子订单 → 录费用 |
| link7 | 资产推送审批 | ... → 录费用 → 资产推送审批 |
| link8 | 订单锁定审批 | ... → 资产推送审批 → 订单锁定审批 |
| link9 | 未放款开票申请审批 | ... → 订单锁定审批 → 未放款开票申请审批 |
| link10 | 供应商垫付申请审批 | ... → 未放款开票申请审批 → 供应商垫付申请审批 |
| link11 | 生成费用通知单 | ... → 供应商垫付申请审批 → **生成费用通知单** |
| link12 | 生成费用确认单 | ... → **生成费用通知单** → **生成费用确认单** |
| link13 | 发起应收对账批次 | ... → **生成费用确认单** → **发起应收对账批次** |
| link14 | 确认应收对账 | ... → **发起应收对账批次** → **确认应收对账** |
| link15 | 发起应收开票批次审批 | ... → **确认应收对账** → **发起应收开票批次审批** |
| link16 | 审核生成开票申请 | ... → **发起应收开票批次审批** → **审核生成开票申请** |
| link17 | 发票上传与登记 | ... → **审核生成开票申请** → **发票上传与登记** |
| link18 | 应收核销 | ... → **发票上传与登记** → **应收核销**（feeTakePage + writeoffBatch） |
| link19 | 发起应付对账批次 | ... → **应收核销** → **发起应付对账批次**（financePayList + orderPayAccountEdit） |
| link20 | 确认应付对账 | ... → **发起应付对账批次** → **确认应付对账**（payAccountPage + accountConfirm） |
| link21 | 发起应付开票批次申请 | ... → **确认应付对账** → **发起应付开票批次申请**（financePayList(开票) + getOrderInfoByFeeId + batchOrderEdit） |
| link22 | 应付发票上传与登记 | ... → **发起应付开票批次申请** → **应付发票上传与登记**（uploadFile + invoiceAdd + applyPage + allocationInvoiceFee） |
| link23 | 发起付款需求 | ... → **应付发票上传与登记** → **发起付款需求**（financePayList + paymentList + demandEditByOrder） |
| link24 | 审核生成付款单 | ... → **发起付款需求** → **审核生成付款单**（auditPage + auditExecute） |

> 链路按依赖顺序递增：link24 隐含 link1~link23 的全部步骤。

### 快捷方法

`order_workflow.py` 提供了 `run_until_xxx` 系列快捷方法，可直接执行到指定阶段：

```python
from workflows.order_workflow import OrderWorkflow

OrderWorkflow.run_until_distribute()           # 新建 + 分发
OrderWorkflow.run_until_stash()               # 到暂存
OrderWorkflow.run_until_generate_sub_order()  # 到子订单
OrderWorkflow.run_until_record_fee(...)       # 到录费用
OrderWorkflow.run_until_fee_notice()          # 到费用通知单
OrderWorkflow.run_until_fee_confirm()         # 到费用确认单
OrderWorkflow.run_until_receive_account()      # 到应收对账批次
OrderWorkflow.run_until_confirm_account()     # 到确认应收对账
OrderWorkflow.run_until_invoice_batch()       # 到应收开票批次
OrderWorkflow.run_until_invoice_batch_audit() # 到开票批次审核
OrderWorkflow.run_until_invoice_upload()      # 到发票上传与登记
OrderWorkflow.run_until_receive_writeoff()     # 到应收核销（link18）
OrderWorkflow.run_until_payable_account()     # 到发起应付对账（link19）
OrderWorkflow.run_until_confirm_payable()     # 到确认应付对账（link20）
OrderWorkflow.run_until_payable_invoice_apply()  # 到发起应付开票批次申请（link21）
OrderWorkflow.run_until_payable_invoice_register()  # 到应付发票上传与登记（link22）
OrderWorkflow.run_until_pay_demand()          # 到发起付款需求（link23）
OrderWorkflow.run_until_pay_demand_audit()     # 到审核生成付款单（link24）
```

---

## 分层架构说明

| 层级 | 目录 | 职责 |
|------|------|------|
| API 层 | `api/` | 封装单个 HTTP 接口调用，统一日志和错误处理 |
| 数据层 | `data/` | 提供测试数据和载荷构建；所有业务参数从 YAML 读取 |
| 流程编排层 | `workflows/` | 串联多个 API，自动处理步骤间数据依赖（order_id、审批ID），返回完整执行上下文 |
| 测试用例层 | `testcases/` | 调用 workflows，按业务阶段组合测试，聚焦断言 |

---

## API 接口说明

### 订单 API（`api/order/order_api.py`）

| 方法 | 接口 | 说明 |
|------|------|------|
| `add_order()` | POST /api/order/orderEntrust/orderAdd | 新增订单 |
| `distribute_order()` | POST /api/order/orderEntrust/orderAdd | 分发订单 |
| `submit_order()` | POST /api/order/order/orderAdd | 提交订单 |
| `get_entrust_order_list()` | POST /api/order/orderEntrust/orderPage | 委托订单列表查询 |
| `get_business_order_list()` | POST /api/order/order/orderPage | 业务订单列表查询 |
| `get_order_by_bl_no()` | - | 按提单号查询（组合调用） |
| `generate_sub_order()` | POST /api/order/order/generateOrderSub | 生成子订单 |
| `book_real_amount()` | POST /api/order/orderFee/bookRealAmountEdit | 录费用 |
| `generate_fee_notice()` | POST /api/order/order/orderNotice | 生成费用通知单 |
| `generate_fee_confirm()` | POST /api/order/order/orderConfirmLoan | 生成费用确认单 |

### 审批 API（`api/order/audit_api.py`）

| 方法 | 接口 | 说明 |
|------|------|------|
| `send_audit()` | 按类型分发 | 发起指定类型审批 |
| `send_asset_push()` | POST /api/order/orderFee/assetPush | 发起资产推送审批 |
| `send_actual_cost_lock()` | POST /api/order/orderFee/realAmountSubmit | 发起/审批订单锁定 |
| `send_add_loan_before_invoice()` | POST /api/order/order/changeInvoiceApply | 发起未放款开票申请审批 |
| `send_add_special_payment_flag()` | POST /api/order/order/changeSpecialPayRules | 发起供应商垫付申请审批 |
| `query_pending_audits()` | POST /api/home/audit/auditPage | 查询审批列表 |
| `audit_execute()` | POST /api/home/audit/auditExecute | 执行审批（通过/拒绝） |

### 财务应收对账 API（`api/receive/receive_account_api.py`）

| 方法 | 接口 | 说明 |
|------|------|------|
| `query_finance_put_list()` | POST /api/finance/accountFee/financePutList | 查询应收款项列表（用于预填充 select_list） |
| `edit_receive_account()` | POST /api/finance/receiveAccount/orderReceiveAccountEdit | 应收对账批次编辑（action=check 预校验 / action=submit 正式提交） |
| `get_receive_account_detail()` | POST /api/finance/receiveAccount/receiveAccountDetail | 查询应收对账批次详情 |
| `confirm_receive_account()` | POST /api/finance/receiveAccount/accountConfirm | 确认应收对账 |
| `get_confirm_list()` | POST /api/finance/receiveAccount/receiveConfirmList | 查询应收确认列表 |

### 应收开票批次 API（`api/receive/invoice_batch_api.py`）

| 方法 | 接口 | 说明 |
|------|------|------|
| `query_finance_put_list_for_invoice()` | POST /api/finance/accountFee/financePutList | 查询应收款项列表（开票模式） |
| `get_exchange_rate()` | POST /api/home/exchangeRate/monthExchangeRate | 获取系统汇率 |
| `get_sell_info()` | POST /api/finance/receiveInvoiceBatch/getSellInfo | 获取开票方信息（买家/卖家） |
| `batch_order_edit()` | POST /api/Finance/ReceiveInvoiceBatch/batchOrderEdit | 批次编辑（action=check/audit/submit） |
| `verify_batch()` | POST /api/Finance/ReceiveInvoiceBatch/batchpage | 验证批次创建 |

### 应收发票上传与登记 API（`api/receive/invoice_upload_api.py`）

| 方法 | 接口 | 说明 |
|------|------|------|
| `upload_file()` | POST /api/home/common/uploadFile | 上传发票文件（PDF） |
| `invoice_add()` | POST /api/finance/receiveInvoice/invoiceAdd | 上传应收发票 |
| `get_apply_page()` | POST /api/Finance/ReceiveInvoiceBatch/applyPage | 按提单号查询发票申请ID |
| `allocation_invoice_fee()` | POST /api/Finance/ReceiveInvoiceBatch/allocationInvoiceFee | 应收开票申请登记发票 |

### 应收核销 API（`api/receive/receive_writeoff_api.py`）

| 方法 | 接口 | 说明 |
|------|------|------|
| `query_order_fee_real_id_list()` | POST /api/order/orderFee/feeTakePage | 按提单号分页查询费用实付 ID 列表（writeoffBatch 上游依赖） |
| `submit_writeoff_batch()` | POST /api/finance/receiveWriteoff/writeoffBatch | 应收核销批次提交（依赖 feeTakePage 返回的 order_fee_real_id + un_writeoff_amount） |

### 应付对账 API（`api/pay/payable_api.py`）

| 方法 | 接口 | 说明 |
|------|------|------|
| `query_finance_pay_list()` | POST /api/finance/accountFee/financePayList | 按提单号查询应付项列表（提取 amount_list，含 order_fee_real_id） |
| `submit_pay_account()` | POST /api/finance/payAccount/orderPayAccountEdit | 发起应付对账批次（依赖 financePayList 返回的 select_list） |
| `query_pay_account_page()` | POST /api/finance/payAccount/payAccountPage | 按 bl_no 查询应付对账批次（验证状态，提取 pay_account_id） |
| `confirm_pay_account()` | POST /api/finance/payAccount/accountConfirm | 确认应付对账（依赖 payAccountPage 返回的 pay_account_id） |
| `query_finance_pay_list_for_invoice()` | POST /api/finance/accountFee/financePayList | 按 bl_no + main_id + pay_settle_object_id 查询应付开票项（开票模式：search_style=invoice + batch_type=1；main_id/pay_settle_object_id 必填，否则返回全量 fee 致后续 406） |
| `get_order_info_by_fee_id()` | POST /api/Finance/payInvoiceBatch/getOrderInfoByFeeId | 按 order_fee_real_id 列表查询开票订单详情（book_supplier / order_sub / real_amount 等） |
| `submit_pay_invoice_batch()` | POST /api/Finance/payInvoiceBatch/batchOrderEdit | 发起应付开票批次申请（apply_type=2 应付，submit 提交即生效，无需审批） |
| `upload_pay_invoice_file()` | POST /api/home/common/uploadFile | 上传应付发票文件（PDF），返回 file_id / file_name / file_url / attachment_id |
| `invoice_add()` | POST /api/finance/payInvoice/invoiceAdd | 登记应付发票（响应 data 为 {invoice_number: pay_invoice_id} 字典） |
| `apply_page()` | POST /api/Finance/PayInvoiceBatch/applyPage | 按 bl_nos 查询应付开票申请ID（响应 data.data[0].pay_invoice_apply_id） |
| `allocation_invoice_fee()` | POST /api/Finance/payInvoiceBatch/allocationInvoiceFee | 分配发票到费用（pay_invoice_id 来自 invoiceAdd，pay_invoice_apply_id 来自 applyPage） |
| `query_payment_list()` | POST /api/finance/payDemand/paymentList | 付款需求预览 |
| `submit_demand()` | POST /api/finance/payDemand/demandEditByOrder | 提交付款需求 |

---

## 配置文件说明

所有业务配置集中存放于 `data/` 目录下的 YAML 文件，Python 代码**零硬编码**：

| 文件 | 用途 |
|------|------|
| `data/order/order.yaml` | 订单基础字段、提交字段、供应商模板、箱型模板、分页/排序测试数据 |
| `data/order/fee.yaml` | 客户应收费用项、供应商应付费用项、录费用默认值、费用行默认值 |
| `data/order/audit.yaml` | 资产推送审批、订单锁定审批、未放款开票申请审批、供应商垫付申请审批 的标题/消息/审批人配置 |
| `data/order/fee_notice.yaml` | 生成费用通知单的 action、finance_ids、bank_ids |
| `data/order/fee_confirm.yaml` | 生成费用确认单的 action、finance_ids、bank_ids |
| `data/receive/receive_account.yaml` | 应收对账批次查询/预校验/提交接口的默认参数 |
| `data/receive/receive_invoice.yaml` | 应收开票批次编辑的枚举值、默认值、action 常量 |
| `data/receive/receive_invoice_upload.yaml` | 应收发票上传与登记接口的发票信息、买家/卖家信息、默认税率 |
| `data/receive/receive_writeoff.yaml` | 应收核销接口的默认值（main_id / main_name / writeoff_name / statement 银行/汇率等），主主体配置 |
| `data/pay/pay_account.yaml` | 应付对账接口默认值（search_style、batch_type、pay_settle_object_id 等），应付对账批次 action 常量 |
| `data/pay/payable_invoice.yaml` | 应付开票申请接口默认值（apply_type、batch_type、fee_type 等），应付开票申请 action 常量 |
| `data/pay/payable_invoice_upload.yaml` | 应付发票上传与登记接口配置（发票类型/税率/金额默认值、买/卖家信息、applyPage 分页与筛选条件） |
| `data/pay/pay_demand.yaml` | 发起付款需求配置（operate_type、batch_type、split_dimension、audit_msg 等） |
| `data/pay/pay_demand_audit.yaml` | 审核生成付款单配置（auditPage 分页与筛选条件、auditExecute 审批状态等） |

> 调整测试数据时只需修改对应 YAML 文件，无需改动 Python 代码。

---

## 使用示例

```python
# === 方式一：通过 workflows 跑完整链路 ===
from workflows.order_workflow import OrderWorkflow

# 执行到指定阶段（link12 等效）
result = OrderWorkflow.full_flow(
    stop_at='fee_confirm',
    bl_no='TEST_BL_001',
    fee_configs=[{'to_customer_fees': [...], 'to_supplier_fees': [...]}],
)

# === 方式二：快捷方法 ===
result = OrderWorkflow.run_until_fee_confirm()
result = OrderWorkflow.run_until_receive_account()
result = OrderWorkflow.run_until_confirm_account()
result = OrderWorkflow.run_until_invoice_upload()
result = OrderWorkflow.run_until_receive_writeoff()  # 完整链路（link18 等效）

# === 方式三：直接调用 API ===
from api.order import OrderApi

resp = OrderApi.add_order(bl_no="TEST_BL_001")
order_info = OrderApi.get_order_by_bl_no("TEST_BL_001")
resp = OrderApi.submit_order(order_info, bl_no="TEST_BL_001")
resp = OrderApi.generate_fee_confirm(order_id=order_info['order_id'])
```
