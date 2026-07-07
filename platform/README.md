# Web 测试平台

基于 Vue 3 + Flask 的自动化测试执行平台，支持登录认证、环境管理、用户管理、流程选择、链路过滤、循环执行、一键执行、实时日志、执行结果汇总、执行历史。

## 项目结构

```
platform/
├── backend/               # Flask 后端
│   ├── server.py         # 启动入口
│   ├── requirements.txt  # Python 依赖
│   ├── .env.example      # 平台环境变量模板
│   ├── api/              # 接口蓝图
│   │   ├── auth.py       # 登录
│   │   ├── markers.py    # pytest marker 列表
│   │   ├── run.py        # 执行测试
│   │   ├── logs.py       # 实时日志 SSE
│   │   └── users.py      # 用户管理
│   ├── services/         # 业务逻辑
│   │   ├── auth.py       # 登录校验 / token
│   │   ├── test_runner.py # 执行 pytest
│   │   ├── db.py         # 数据层（基于 SQLite）
│   │   └── users.py      # 用户 CRUD
│   └── static/           # 前端构建产物
├── frontend/             # Vue 3 前端（Vite + Element Plus）
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── api/           # axios 接口封装
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── utils/         # request 拦截器
│   │   └── router/        # 路由
└── README.md
```

---

## 环境要求

- Python >= 3.10
- Node.js >= 18（仅构建时需要，构建后运行无需 Node.js）
- Windows 开发：直接使用 `python run.py` 启动
- Ubuntu 22.04+（生产部署）

---

## 本地开发启动

### 1. 配置后端环境变量

```bash
cd platform/backend
copy .env.example .env
# 编辑 .env，确认管理员账号和端口
```

### 2. 安装后端依赖并启动

```bash
cd platform/backend
pip install -r requirements.txt
python run.py
# 服务运行在 http://localhost:5000
```

### 3. 安装前端依赖并启动

```bash
cd platform/frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

---

## 生产部署（虚拟机）

### 1. 克隆并进入项目

```bash
cd /opt/pr_study
```

### 2. 修复项目目录权限

```bash
# 把整个前端目录归属给 lele 用户
sudo chown -R lele:lele /opt/pr_study/platform/frontend
# 赋予执行权限
chmod -R 755 node_modules
```

### 3. 创建并激活虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装后端依赖

```bash
cd /opt/pr_study/platform/backend
pip install -r requirements.txt
```

### 5. 安装 Node.js（如未安装，仅构建时需要）

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 6. 构建前端

```bash
cd /opt/pr_study/platform/frontend
npm install
npm run build
```

### 7. 复制前端产物到 static 目录

```bash
cd /opt/pr_study/platform
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
```

### 8. 配置 Systemd 服务

创建服务文件：

```bash
sudo tee /etc/systemd/system/pr_study.service > /dev/null <<EOF
[Unit]
Description=PR Study Platform
After=network.target

[Service]
User=lele
WorkingDirectory=/opt/pr_study/platform/backend
Environment="PATH=/opt/pr_study/venv/bin"
ExecStart=/opt/pr_study/venv/bin/python server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable pr_study
sudo systemctl start pr_study
sudo systemctl status pr_study
```

### 9. 访问平台

浏览器打开 `http://<虚拟机IP>:5000`
端口转发：http://172.16.18.55:90/

---

## 后续代码更新

本地修改代码并 push 到 Git 后，在虚拟机执行以下步骤即可完成更新：

```bash
cd /opt/pr_study
git pull origin dev

# 重启服务
sudo systemctl restart pr_study
sudo systemctl status pr_study
```

如修改了前端代码，需重新构建并复制产物：

```bash
cd platform/frontend
npm install
# 把整个前端目录归属给 lele 用户
sudo chown -R lele:lele /opt/pr_study/platform/frontend
# 赋予执行权限
chmod -R 755 node_modules
npm run build
mkdir backend/static/dist
cp -r frontend/dist/* backend/static/dist
sudo systemctl restart pr_study
```

---

## 常见问题排查

### 1. 浏览器运行测试报错 `PermissionError`

检查是否有多个 server.py 进程，且属于不同用户：

```bash
ps aux | grep server.py
```

如果有其他用户的旧进程，杀掉并重启：

```bash
sudo pkill -f "server.py"
sudo systemctl restart pr_study
```

### 2. 配置文件找不到 `*.yaml`

Web 平台运行时不需要在项目根目录配置 `.env`（平台会自动传环境变量给 pytest）。只有命令行直接运行 pytest 时才需要根目录 `.env`。

### 3. 服务无法启动

查看 systemd 日志：

```bash
sudo journalctl -u pr_study -f
```

---

## 服务管理命令

| 操作 | 命令 |
|------|------|
| 启动服务 | `sudo systemctl start pr_study` |
| 停止服务 | `sudo systemctl stop pr_study` |
| 重启服务 | `sudo systemctl restart pr_study` |
| 查看状态 | `sudo systemctl status pr_study` |
| 查看日志 | `sudo journalctl -u pr_study -f` |
| 开机自启 | `sudo systemctl enable pr_study` |
| 取消自启 | `sudo systemctl disable pr_study` |

---

## 主要功能

| 功能 | 说明 |
|------|------|
| 登录认证 | 账号密码，会话级有效；错误时给出明确提示 |
| 环境配置 | 通过 Web 页面管理被测系统环境 |
| 用户管理 | 管理员可管理平台账号（仅管理员可见） |
| 链路选择 | 5 张流程选择卡片，自动过滤对应 marker 范围 |
| 循环执行 | 支持指定循环次数（1~100） |
| 实时日志 | SSE 流式推送 pytest 输出到前端，自动滚动 |
| 结果汇总 | 通过 / 失败 / 跳过数量 + 失败用例详情 |
| 执行历史 | 查看历史执行记录 |
