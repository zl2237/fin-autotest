# PR Study - 接口自动化测试框架 + Web 测试平台

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的 25 条链路。

**核心能力：**
- 25 条链路（link1~link25），按依赖顺序递增，link25 隐含 link1~link24
- workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）
- 所有业务配置参数集中存储于 YAML，Python 代码零硬编码
- data 层按环境自动加载 `*_tidb.yaml` 或 `*_pre.yaml`，通过 `.env` 中的 `TEST_ENV` 切换
- Web 平台：环境管理、一键执行、实时日志、执行历史
- CI 环境自动企微机器人通知

---

## 目录结构

```
pr_study/
├── api/                    # API 层（HTTP 接口封装）
│   ├── order/              # 订单域
│   ├── receive/            # 应收域
│   └── pay/                # 付款域
├── config/                 # 全局配置
│   └── settings.py         # .env 加载 + 常量
├── core/                   # 基础设施
│   └── http_client.py      # HTTP 客户端
├── data/                   # 数据层（YAML 配置 + 数据构建）
│   ├── env.py              # YAML 按环境加载
│   ├── order/              # 订单、费用、审批流
│   ├── receive/            # 应收对账、开票、核销
│   └── pay/                # 应付对账、开票、付款需求、核销
├── testcases/              # pytest 用例
│   ├── order/              # 链路 1~12
│   ├── receive/            # 链路 13~18
│   └── pay/                # 链路 19~25
├── workflows/              # 流程编排
│   ├── order/              # 订单域步骤
│   ├── receive/            # 应收域步骤
│   └── pay/                # 付款域步骤
├── platform/               # Web 测试平台
│   ├── backend/            # Flask 后端
│   └── frontend/           # Vue 3 前端
├── notify.py               # 企微通知
├── pytest.ini              # pytest 配置
├── conftest.py             # pytest 根配置
├── .env.example            # 环境变量模板
└── requirements.txt        # Python 依赖
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
pytest -m link1                    # 仅链路1
pytest -m "link11 or link12"       # 多条链路
pytest -m link25                   # 全流程
```

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

OrderWorkflow.run_until_distribute()                # link2
OrderWorkflow.run_until_stash()                    # link3
OrderWorkflow.run_until_generate_sub_order()        # link5
OrderWorkflow.run_until_record_fee(...)             # link6
OrderWorkflow.run_until_record_audit()              # link7
OrderWorkflow.run_until_order_lock()                # link8
OrderWorkflow.run_until_invoice_apply()             # link9
OrderWorkflow.run_until_supplier_advance()          # link10
OrderWorkflow.run_until_fee_notice()                # link11
OrderWorkflow.run_until_fee_confirm()               # link12
OrderWorkflow.run_until_receive_account()           # link13
OrderWorkflow.run_until_confirm_account()           # link14
OrderWorkflow.run_until_invoice_batch()             # link15
OrderWorkflow.run_until_invoice_batch_audit()      # link16
OrderWorkflow.run_until_invoice_upload()            # link17
OrderWorkflow.run_until_receive_writeoff()          # link18
OrderWorkflow.run_until_payable_account()           # link19
OrderWorkflow.run_until_confirm_payable()           # link20
OrderWorkflow.run_until_payable_invoice_apply()     # link21
OrderWorkflow.run_until_pay_demand()                # link23
OrderWorkflow.run_until_pay_demand_audit()          # link24
OrderWorkflow.run_until_pay_writeoff()              # link25
```

---

## 安全提示

- `.env` 文件包含敏感凭据，已加入 `.gitignore`
- 生产部署请修改 `ADMIN_PASSWORD` 和 `SECRET_KEY`
- 如仅内网使用，`TOKEN_EXPIRE_SECONDS` 可设为 `0`（永不过期）
- 建议在 Nginx 前配置 HTTPS（Let's Encrypt）
