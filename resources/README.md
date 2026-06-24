# PR Study - 接口自动化测试工具

> 本工具为物流管理系统提供全流程接口测试能力，支持从新建订单到付款单核销的 25 条链路测试。

---

## 目录结构

打包后的目录结构如下：

```
PRStudy/
├── PRStudy.exe              # 主程序（双击启动 GUI）
├── _internal/               # 运行时依赖（PyInstaller 打包内容）
│   ├── jre/                # Java 运行环境（Allure 报告生成器）
│   ├── allure/             # Allure 测试报告工具
│   ├── api/                # API 层源码
│   ├── data/                # 数据层配置
│   ├── workflows/           # 流程编排层
│   ├── testcases/           # 测试用例层
│   ├── core/                # 核心模块
│   ├── utils/               # 工具类
│   └── config/              # 配置模块
├── venv/                    # Python 虚拟环境（可移植运行）
├── testcases/               # 测试用例源码（独立副本，可用于二次开发）
├── report/                   # 测试报告输出目录
│   └── allure-results/       # Allure 报告数据
└── README.md                # 本使用指南
```

---

## 快速使用

### 方式一：图形界面（推荐）

1. 双击 `PRStudy.exe` 启动 GUI 工具
2. 在弹窗中配置：
   - **接口地址**：API 基础 URL
   - **账号/密码**：登录凭证
   - **用户ID**：操作员 ID
3. 选择要执行的链路（如 `link1`、`link11` 等）
4. 可选设置循环次数
5. 点击 **开始测试**，查看实时日志

### 方式二：命令行运行

```bash
# 进入目录
cd PRStudy

# 使用内置虚拟环境的 Python
venv\Scripts\python.exe -m pytest -v

# 运行指定链路
venv\Scripts\python.exe -m pytest -m link1
venv\Scripts\python.exe -m pytest -m "link11 or link12"

# 从链路25运行（包含所有前置步骤）
venv\Scripts\python.exe -m pytest -m link25
```

> **提示**：优先使用 `venv\Scripts\python.exe`，它包含了所有必要的依赖包。

---

## 测试链路说明

| 链路 | 停止阶段 | 说明 |
|------|----------|------|
| link1 | 新建订单 | 创建新订单 |
| link2 | 分发 | 订单分发 |
| link3 | 暂存 | 订单暂存 |
| link4 | 提交 | 订单提交 |
| link5 | 生成子订单 | 创建子订单 |
| link6 | 录费用 | 填写费用信息 |
| link7 | 资产推送审批 | 推送资产审批 |
| link8 | 订单锁定审批 | 锁定订单审批 |
| link9 | 未放款开票申请审批 | 开票申请 |
| link10 | 供应商垫付申请审批 | 垫付审批 |
| link11 | 生成费用通知单 | 费用通知 |
| link12 | 生成费用确认单 | 费用确认 |
| link13 | 发起应收对账批次 | 应收对账 |
| link14 | 确认应收对账 | 应收确认 |
| link15 | 发起应收开票批次审批 | 应收开票申请 |
| link16 | 审核生成开票申请 | 开票审核 |
| link17 | 发票上传与登记 | 发票上传 |
| link18 | 应收核销 | 应收核销 |
| link19 | 发起应付对账批次 | 应付对账 |
| link20 | 确认应付对账 | 应付确认 |
| link21 | 发起应付开票批次申请 | 应付开票申请 |
| link22 | 应付发票上传与登记 | 应付发票上传 |
| link23 | 发起付款需求 | 付款需求 |
| link24 | 审核生成付款单 | 付款审核 |
| link25 | 付款单核销 | 付款核销 |

> **提示**：链路按依赖顺序递增，`link25` 隐含 link1~link24 的全部步骤。

---

## 测试报告

测试完成后，报告文件位于 `report/allure-results/` 目录：

```bash
# 本地查看报告（需安装 Allure 命令行）
allure serve report/allure-results

# 或生成静态 HTML 报告
allure generate report/allure-results -o report/html
```

> **注意**：如需生成 Allure 报告，需要先安装 Allure 命令行工具。

---

## 配置说明

### 环境变量配置

在首次使用前，需创建 `.env` 配置文件：

```
BASE_URL=http://your-api-server.com
USERNAME=your_username
PASSWORD=your_password
ORDER_CREATE_ID=12345
TOKEN_FIELD=data.token
```

> **注意**：`.env` 文件不会推送到远程仓库，请妥善保管。

### GUI 配置保存

GUI 工具会自动保存最近一次配置到 `config.ini`，下次启动时自动回填。

---

## 常见问题

### Q1: 提示 "Python not found" 或运行报错

使用打包内的 `venv` 虚拟环境：

```bash
# 使用 venv 中的 Python 运行 pytest
venv\Scripts\python.exe -m pytest -v
```

### Q2: 登录失败 / Token 获取异常

1. 检查 `.env` 中的 `BASE_URL` 是否正确
2. 确认 `USERNAME` / `PASSWORD` 有效
3. 检查网络是否可访问 API 服务器

### Q3: 报告目录无内容

1. 确认测试用例有执行（GUI 日志显示成功）
2. 检查 `report/allure-results` 目录是否存在
3. 可手动执行 `pytest --collect-only` 确认用例收集正常

### Q4: Allure 报告无法打开

需安装 Allure 命令行工具：
- Windows: 下载 `allure-commandline` 包并配置 PATH
- 或访问 `https://qameta.io/allure-report/` 在线查看

---

## 技术支持

- 框架源码：`http://172.16.18.55:88/root/pr_study.git`
- 详细文档：参考项目 `README.md`
