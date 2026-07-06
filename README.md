# PR Study - 接口自动化测试框架 + Web 测试平台

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的完整链路。

**核心能力：**
- 32 条链路：`order1~12` 为树根，`order_pay_receive1~13` 与 `order_receive_pay1~13` 为两类扩展执行顺序
- workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）
- 所有业务配置参数集中存储于 YAML，Python 代码零硬编码
- data 层按环境自动加载 `*_tidb.yaml` 或 `*_pre.yaml`，通过 `.env` 中的 `TEST_ENV` 切换
- Web 平台：5 张流程选择卡片、环境管理、链路选择、循环执行、一键执行、实时日志、执行历史、用户管理
- CI 环境自动企微机器人通知
- Allure 报告

---

## 目录结构

```
pr_study/
├── api/                            # API 层：HTTP 接口封装，按 order/receive/pay 划分域
│   ├── order/
│   ├── receive/
│   └── pay/
├── config/
│   └── settings.py                 # 环境变量与全局常量
├── core/
│   └── http_client.py              # 统一 HTTP 客户端
├── data/                           # 数据层：YAML 配置 + 数据构建，按环境自动加载
│   ├── env.py
│   ├── order/
│   ├── receive/
│   └── pay/
├── utils/                          # 公共工具
│   ├── __init__.py
│   ├── generate.py                 # 测试数据生成/编码生成
│   └── logger.py                   # 日志初始化与格式化
├── testcases/                      # pytest 用例，按 order/pay_receive/receive_pay 分组
│   ├── conftest.py
│   ├── order/
│   ├── pay_receive/
│   └── receive_pay/
├── workflows/                      # 流程编排：业务链路到 steps 的调度与依赖传递
│   ├── order/
│   ├── receive/
│   ├── pay/
│   ├── pay_receive_workflow.py
│   └── receive_pay_workflow.py
├── platform/                       # Web 测试平台
│   ├── backend/                    # Flask 后端：执行调度、日志、用户管理
│   └── frontend/                   # Vue 3 前端：链路选择、执行、历史、用户管理
├── .gitlab-ci.yml                  # CI 配置
├── .gitignore
├── .env.example
├── conftest.py                     # pytest 根配置、环境与 fixtures
├── notify.py                       # 企微通知
├── pytest.ini
└── requirements.txt                # Python 依赖
```

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 测试框架 | pytest | >=7.4.0 |
| HTTP 客户端 | requests | >=2.31.0 |
| 日志记录 | loguru | >=0.7.2 |
| YAML 配置 | PyYAML | >=6.0 |
| 后端框架 | Flask | >=3.0.0 |
| 数据库 | SQLite | 3.x（无需额外服务） |
| 前端框架 | Vue 3 + Vite | ^3.4 / ^5.0 |
| UI 组件库 | Element Plus | ^2.4.0 |

---

## 快速开始

### 1. 克隆项目

```bash
git clone http://172.16.18.55:88/root/pr_study.git
cd pr_study
```

### 2. 安装依赖

**后端（Python）：**

```bash
cd platform/backend
pip install -r requirements.txt
```

**前端（Node.js）：**

```bash
cd platform/frontend
npm install
```

### 3. 配置环境

**命令行 pytest 环境变量：**

```bash
cp .env.example .env
# 编辑 .env，关键变量：
#   BASE_URL / LOGIN_URL / USERNAME / PASSWORD   -- 被测系统地址和登录凭据
#   TEST_ENV=tidb                               -- 指定 data 层加载 tidb/pre 专属 YAML
```

Web 测试平台的启动与部署说明见 `platform/README.md`。

---

## 直接运行 pytest（命令行模式）

保留原有的 pytest 命令行能力，不依赖 Web 平台：

```bash
# 配置被测系统
cp .env.example .env
# 编辑 .env 填入 BASE_URL、USERNAME、PASSWORD

# 运行
pytest -v                          # 全部
pytest -m order1                   # 仅订单链路1
pytest -m "order_pay_receive1 or order_pay_receive8"       # 多条链路
pytest -m order_pay_receive13      # 订单+应付+应收全流程
pytest -m order_receive_pay13      # 订单+应收+应付全流程
```

---

## 链路一览（32 条）

### 订单基础链路（order1~12）

| 链路 | 停止阶段 |
|------|----------|
| order1 | 新建 |
| order2 | 分发 |
| order3 | 暂存 |
| order4 | 提交 |
| order5 | 生成子订单 |
| order6 | 录费用 |
| order7 | 资产推送审批 |
| order8 | 订单锁定审批 |
| order9 | 未放款开票申请审批 |
| order10 | 供应商垫付申请审批 |
| order11 | 生成费用通知单 |
| order12 | 生成费用确认单 |

### 订单+应付+应收（默认，order_pay_receive1~13）

**执行顺序：订单 → 应付 → 应收**

| 链路 | 停止阶段 |
|------|----------|
| order_pay_receive1 | 发起应付对账批次 |
| order_pay_receive2 | 确认应付对账 |
| order_pay_receive3 | 发起应付开票批次申请 |
| order_pay_receive4 | 应付发票上传与登记 |
| order_pay_receive5 | 发起付款需求 |
| order_pay_receive6 | 审核生成付款单 |
| order_pay_receive7 | 付款单核销 |
| order_pay_receive8 | 发起应收对账批次 |
| order_pay_receive9 | 确认应收对账 |
| order_pay_receive10 | 发起应收开票批次审批 |
| order_pay_receive11 | 审核生成开票申请 |
| order_pay_receive12 | 发票上传与登记 |
| order_pay_receive13 | 应收核销 |

### 订单+应收+应付（扩展，order_receive_pay1~13）

**执行顺序：订单 → 应收 → 应付**

| 链路 | 停止阶段 |
|------|----------|
| order_receive_pay1 | 发起应收对账批次 |
| order_receive_pay2 | 确认应收对账 |
| order_receive_pay3 | 发起应收开票批次审批 |
| order_receive_pay4 | 审核生成开票申请 |
| order_receive_pay5 | 发票上传与登记 |
| order_receive_pay6 | 应收核销 |
| order_receive_pay7 | 发起应付对账批次 |
| order_receive_pay8 | 确认应付对账 |
| order_receive_pay9 | 发起应付开票批次申请 |
| order_receive_pay10 | 应付发票上传与登记 |
| order_receive_pay11 | 发起付款需求 |
| order_receive_pay12 | 审核生成付款单 |
| order_receive_pay13 | 付款单核销 |

> 所有链路基于链路依赖树模型：`order12` 是两类扩展流程的共同前置；`order_pay_receive7` 是 `order_pay_receive8` 的前置；`order_receive_pay6` 是 `order_receive_pay7` 的前置。

---

## Web 平台流程选择

平台前端提供 5 张流程选择卡片：

| 卡片 | Workflow 类型 | 可用 marker | 标注 |
|------|--------------|------------|------|
| 仅订单 | order_only | order1~12 | - |
| 订单+应付（默认） | pay_receive | order_pay_receive1~7 | 默认 |
| 订单+应付+应收（默认） | pay_receive | order_pay_receive8~13 | 默认 |
| 订单+应收（扩展） | receive_pay | order_receive_pay1~6 | 扩展 |
| 订单+应收+应付（扩展） | receive_pay | order_receive_pay7~13 | 扩展 |

切换卡片时，“运行链路”下拉框会自动过滤对应 marker 范围，并重置到该组第一个可用链路。

---

## 快捷方法

`OrderWorkflow` 提供 `run_until_xxx` 系列方法：

```python
from workflows.order_workflow import OrderWorkflow

# 订单基础链路
OrderWorkflow.run_until_distribute()                # order2
OrderWorkflow.run_until_stash()                    # order3
OrderWorkflow.run_until_generate_sub_order()        # order5
OrderWorkflow.run_until_record_fee(...)             # order6
OrderWorkflow.run_until_record_audit()              # order7
OrderWorkflow.run_until_order_lock()                # order8
OrderWorkflow.run_until_invoice_apply()             # order9
OrderWorkflow.run_until_supplier_advance()          # order10
OrderWorkflow.run_until_fee_notice()                # order11
OrderWorkflow.run_until_fee_confirm()               # order12

# 应收链路（order13~18）
OrderWorkflow.run_until_receive_account()           # order13
OrderWorkflow.run_until_confirm_account()           # order14
OrderWorkflow.run_until_invoice_batch()             # order15
OrderWorkflow.run_until_invoice_batch_audit()      # order16
OrderWorkflow.run_until_invoice_upload()            # order17
OrderWorkflow.run_until_receive_writeoff()          # order18

# 应付链路（order19~25）
OrderWorkflow.run_until_payable_account()           # order19
OrderWorkflow.run_until_confirm_payable()           # order20
OrderWorkflow.run_until_payable_invoice_apply()     # order21
OrderWorkflow.run_until_pay_demand()                # order23
OrderWorkflow.run_until_pay_demand_audit()          # order24
OrderWorkflow.run_until_pay_writeoff()              # order25
```

---

## 安全提示

- `.env` 文件包含敏感凭据，已加入 `.gitignore`
- 生产部署请修改 `ADMIN_PASSWORD` 和 `SECRET_KEY`
- 如仅内网使用，`TOKEN_EXPIRE_SECONDS` 可设为 `0`（永不过期）
- 建议在 Nginx 前配置 HTTPS（Let's Encrypt）
