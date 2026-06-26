# API 测试平台

基于 Vue 3 + Flask 的自动化测试执行平台，支持登录认证、链路选择、实时日志和结果展示。

## 项目结构

```
platform/
├── backend/           # Flask 后端
│   ├── server.py      # Flask 入口，同时 serve Vue 静态文件
│   ├── api/           # REST API（auth, markers, run, logs）
│   ├── services/      # 业务逻辑（auth, test_runner, store）
│   ├── static/        # Vue 构建产物（部署时由 frontend build 填充）
│   ├── .env.example   # 环境变量示例
│   └── requirements.txt
├── frontend/          # Vue 3 前端（Vite + Element Plus）
│   └── src/
│       ├── api/request.ts    # Axios 封装，含登录拦截
│       ├── stores/auth.ts    # Pinia 认证状态
│       ├── router/index.ts   # 路由（/login, /dashboard）
│       ├── views/LoginView.vue
│       └── views/DashboardView.vue
└── deploy/            # 部署配置
    ├── gunicorn_config.py
    └── test-platform.service
```

## 环境要求

- Python >= 3.10
- Node.js >= 18
- pytest + pytest-xdist + pytest-repeat + allure-pytest（项目依赖）
- Ubuntu 虚拟机（部署目标）

## 本地开发

### 1. 安装后端依赖

```bash
cd platform/backend
pip install -r requirements.txt
```

### 2. 启动后端

```bash
cd platform/backend
python server.py
```

启动后访问：
- 前端页面：http://localhost:3000/
- 健康检查：http://localhost:3000/api/health
- 链路列表：http://localhost:3000/api/markers

### 3. 前端开发（可选，有热重载）

```bash
cd platform/frontend
npm install
npm run dev
```

访问 http://localhost:5173（前端 dev server 代理 API 到 :5000）

## 部署到 Ubuntu 虚拟机

### 1. 上传整个 pr_study 目录到虚拟机

```bash
scp -r pr_study user@your-vm:/home/user/
```

### 2. 创建 Python 虚拟环境并安装依赖

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
cd ~/pr_study/platform/backend
pip install -r requirements.txt
```

### 3. 构建前端

```bash
cd ~/pr_study/platform/frontend
npm install
sudo chmod -R 775 /home/lele/pr_study
npm run build          # 产物输出到 ../backend/static/
```

### 4. 启动服务

方式一：直接运行

```bash
cd ~/pr_study/platform/backend
PLATFORM_PORT=5000 PLATFORM_USER=admin PLATFORM_PASSWORD=admin123 \
  FLASK_SECRET_KEY=change-me-in-prod \
  gunicorn -c ../deploy/gunicorn_config.py server:app
```

方式二：systemd 服务（推荐）

编辑 `deploy/test-platform.service`，替换以下占位符：
- `{{USER}}` / `{{GROUP}}` — 运行用户
- `{{PROJECT_ROOT}}` — 项目路径，如 `/home/user/pr_study`
- `{{PATH}}` — venv bin 路径，如 `/home/user/venv/bin`
- `{{SECRET_KEY}}` — Flask secret key

```bash
sudo cp ~/pr_study/platform/deploy/test-platform.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable test-platform
sudo systemctl start test-platform
sudo systemctl status test-platform
```

访问 `http://your-vm-ip:3000`

## 平台默认账号

| 账号  | 密码     |
|-------|----------|
| admin | admin123 |

修改方式：设置环境变量 `PLATFORM_USER` 和 `PLATFORM_PASSWORD`。

## 主要功能

| 功能 | 说明 |
|------|------|
| 登录认证 | 简单账号密码，会话级有效；账号/密码错误时给出明确提示 |
| 环境配置 | BASE_URL、LOGIN_URL、测试账号/密码、USER_ID（创建者） |
| 链路选择 | 通过 pytest marker 筛选 link1 ~ linkN |
| 循环执行 | 支持指定循环次数（loop_count） |
| 实时日志 | SSE 流式推送 pytest 输出到前端，自动滚动 |
| 结果汇总 | 通过 / 失败 / 跳过数量 + 失败用例详情 |
