# PR Study - 接口自动化测试框架 + Web 测试平台

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的 25 条链路。

**核心能力：**
- 25 条链路（link1~link25），按依赖顺序递增，link25 隐含 link1~link24
- workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）
- 所有业务配置参数集中存储于 YAML，Python 代码零硬编码
- Web 平台：环境管理、一键执行、实时日志、执行历史
- CI 环境自动企微机器人通知

---

## 目录结构

```
pr_study/
├── api/                        # API 层（按业务域组织）
│   ├── order/                  # 订单域
│   │   ├── order_api.py        # 订单 CRUD + 分发
│   │   └── audit_api.py        # 资产推送审批
│   ├── receive/               # 应收域
│   │   ├── receive_account_api.py
│   │   ├── receive_apply_api.py
│   │   ├── receive_invoice_register_api.py
│   │   └── receive_writeoff_api.py
│   └── pay/                    # 付款域
│       ├── pay_account_api.py
│       ├── pay_apply_api.py
│       ├── pay_demand_api.py
│       ├── pay_demand_audit_api.py
│       ├── pay_invoice_register_api.py
│       ├── pay_writeoff_api.py
│       └── payable_api.py
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
│   └── pay/                   # 应付对账、开票、付款需求、核销
│
├── testcases/                 # 测试用例层
│   ├── conftest.py            # pytest 全局配置（登录、JSON 摘要）
│   ├── order/                 # 链路 1~12
│   │   ├── test_order_basic.py
│   │   ├── test_fee.py
│   │   ├── test_audit.py
│   │   └── test_fee_notice_confirm.py
│   ├── receive/               # 链路 13~18
│   │   ├── test_receive_account.py
│   │   ├── test_receive_writeoff.py
│   │   ├── test_receive_invoice_batch.py
│   │   ├── test_receive_invoice_batch_audit.py
│   │   └── test_receive_invoice_upload.py
│   └── pay/                   # 链路 19~25
│       ├── test_pay_account.py
│       ├── test_pay_apply.py
│       ├── test_pay_invoice_register.py
│       └── test_pay_demand.py
│
├── workflows/                 # 流程编排层
│   ├── order_workflow.py      # 全流程编排入口
│   ├── order/                 # 订单域步骤
│   │   ├── order_steps.py
│   │   ├── audit_steps.py
│   │   └── fee_steps.py
│   ├── receive/               # 应收域步骤
│   │   ├── receive_account_steps.py
│   │   ├── receive_writeoff_steps.py
│   │   ├── receive_apply_steps.py
│   │   └── receive_invoice_register_steps.py
│   └── pay/                   # 付款域步骤
│       ├── pay_account_steps.py
│       ├── pay_apply_steps.py
│       ├── pay_invoice_register_steps.py
│       ├── pay_demand_steps.py
│       ├── pay_demand_audit_steps.py
│       └── pay_writeoff_steps.py
│
├── platform/                  # 🆕 Web 测试平台
│   ├── backend/               # Flask 后端 API
│   │   ├── run.py             # 启动入口
│   │   ├── requirements.txt   # Python 依赖
│   │   ├── app/
│   │   │   ├── api/           # 路由：auth / environments / exec
│   │   │   ├── core/          # config / db
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   └── utils/
│   │   └── static/            # Vue 构建产物（开发模式由 Vite 托管）
│   └── frontend/              # Vue 3 前端
│       ├── package.json
│       ├── vite.config.js
│       ├── index.html
│       └── src/
│           ├── api/           # axios 接口封装
│           ├── views/         # 页面组件
│           ├── components/    # 公共组件
│           ├── stores/        # Pinia 状态管理
│           └── utils/         # request 拦截器
│
├── notify.py                  # 企微机器人通知
├── pytest.ini                 # pytest 配置（标记定义）
├── conftest.py                # pytest 根配置（redirect）
├── .env.example               # 环境变量模板
└── requirements.txt           # Python 依赖
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

**后端环境变量：**

```bash
cp platform/backend/.env.example platform/backend/.env
# 编辑 .env，填入管理员账号和被测系统配置
```

**前端代理（开发模式）：**

`platform/frontend/vite.config.js` 中已配置 Vite 代理到 `http://localhost:5000`。

---

## 运行方式

### 方式一：开发模式（推荐用于本地调试）

**终端 1 - 启动 Flask 后端：**

```bash
cd platform/backend
python run.py
# 服务运行在 http://localhost:5000
```

**终端 2 - 启动 Vue 前端：**

```bash
cd platform/frontend
npm run dev
# 访问 http://localhost:3000
```

### 方式二：生产模式（Flask 托管构建后的静态文件）

```bash
# 1. 构建前端
cd platform/frontend
npm run build

# 2. 将构建产物复制到 backend/static
#    Linux/Mac:
#    cp -r dist/* platform/backend/app/static/
#    Windows (PowerShell):
#    Copy-Item -Recurse dist\* ..\backend\app\static\

# 3. 启动 Flask（同时服务 API + 静态页面）
cd platform/backend
python run.py
```

---

## Web 平台使用

### 1. 登录

- 默认账号：`admin`
- 默认密码：`admin123`
- 在 `.env` 中修改 `ADMIN_USERNAME` / `ADMIN_PASSWORD`

### 2. 环境管理

在「环境管理」页面添加被测系统环境：

| 字段 | 说明 |
|------|------|
| 名称 | 如 `uat`、`sit`、`prod` |
| API 地址 | 被测系统域名，如 `https://xxx.com` |
| 账号 / 密码 | 登录凭据 |
| Token 字段 | 响应中 token 路径，默认 `data.token` |
| 默认 | 是否设为默认环境 |

### 3. 发起测试

1. 选择环境
2. 勾选要执行的链路（可多选，如 link1~link25）
3. 设置循环次数（1~100）
4. （可选）输入费用配置 JSON
5. 点击「开始执行」

平台将：
- 自动写入 `.env` 凭据
- 在子进程中调用 `pytest`
- 通过 SSE 实时推送日志到前端
- 将执行结果存入 SQLite

### 4. 执行历史

查看历史执行记录，包括状态、链路、耗时、通过/失败数量。

---

## 部署到 Ubuntu VM（生产环境）

### 前置条件

- Ubuntu 22.04+，已安装 Python 3.10+、Node.js 18+、Nginx
- 开放 5000（Flask）和 80（Nginx）端口

### 步骤 1：上传项目

```bash
# 通过 scp / git clone 上传到 /opt/pr_study
cd /opt/pr_study
git clone http://172.16.18.55:88/root/pr_study.git  # 或 scp -r
```

### 步骤 2：安装后端依赖

```bash
cd platform/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 步骤 3：安装前端依赖并构建

```bash
cd platform/frontend
npm install
npm run build
```

### 步骤 4：复制前端产物到 backend/static

```bash
mkdir -p platform/backend/app/static
cp -r platform/frontend/dist/* platform/backend/app/static/
```

### 步骤 5：配置 Nginx

```bash
# /etc/nginx/sites-available/pr_study
server {
    listen 80;
    server_name <your-domain-or-ip>;

    client_max_body_size 10M;

    location / {
        root /opt/pr_study/platform/backend/app/static;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/pr_study /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 步骤 6：配置 Systemd

```bash
# /etc/systemd/system/pr_study.service
[Unit]
Description=PR Study Platform
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/pr_study/platform/backend
Environment="PATH=/opt/pr_study/platform/backend/.venv/bin"
ExecStart=/opt/pr_study/platform/backend/.venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now pr_study
journalctl -u pr_study -f  # 查看日志
```

### 步骤 7：访问

浏览器打开 `http://<your-ip>`，使用 `admin / admin123` 登录。

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
