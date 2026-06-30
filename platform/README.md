# Web 测试平台

基于 Vue 3 + Flask 的自动化测试执行平台，支持登录认证、环境管理、一键执行、实时日志和结果展示。

## 项目结构

```
platform/
├── backend/               # Flask 后端
│   ├── server.py         # 启动入口
│   ├── requirements.txt  # Python 依赖
│   └── static/           # 前端构建产物（纯静态，无需 Node.js）
├── frontend/             # Vue 3 前端（Vite + Element Plus）
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── api/           # axios 接口封装
│       ├── views/         # 页面组件
│       ├── components/    # 公共组件
│       ├── stores/        # Pinia 状态管理
│       └── utils/         # request 拦截器
└── README.md
```

## 环境要求

- Python >= 3.10
- Node.js >= 18（仅构建时需要，构建后运行无需 Node.js）
- Ubuntu 22.04+（生产部署）

---

## 首次部署（虚拟机 git pull 后）

从 Git 拉取代码后，按以下步骤完成部署：

### 1. 修复项目目录权限

```bash
cd /opt/pr_study
sudo chown -R $(whoami):$(whoami) /opt/pr_study
```

> 项目目录可能属于其他用户（如 www-data），必须改为当前用户，否则后续步骤会报权限错误。

### 2. 创建并激活虚拟环境

```bash
cd /opt/pr_study
sudo rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装后端依赖

```bash
cd /opt/pr_study/platform/backend
pip install -r requirements.txt

# 安装 allure（pytest 报告用）
pip install allure-pytest

# 降级 pytest 到兼容版本
pip install pytest==8.3.5
```

### 4. 安装 Node.js（如未安装，仅构建时需要）

```bash
# 检查是否已有
node --version
npm --version

# 如没有，安装 Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 5. 构建前端

```bash
cd /opt/pr_study/platform/frontend
npm install
npm run build
```

### 6. 复制前端产物到 static 目录

```bash
cd /opt/pr_study/platform
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
```

### 7. 配置 Systemd 服务

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

> **注意**：`User` 必须与执行 git pull 的用户一致（如 `lele`），否则日志文件写入会报权限错误。

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable pr_study
sudo systemctl start pr_study
sudo systemctl status pr_study
```

### 8. 访问平台

浏览器打开 `http://<虚拟机IP>:5000`
端口转发：http://172.16.18.55:90/

---

## 后续代码更新

本地修改代码并 push 到 Git 后，在虚拟机执行以下步骤即可完成更新：

### 标准更新流程

```bash
cd /opt/pr_study
git pull origin dev

# 重启服务
sudo systemctl restart pr_study
sudo systemctl status pr_study
```

### 更新后验证

- 如果只改了 Python 代码 → 重启后即可
- 如果改了 requirements.txt → 需重新安装依赖：
  ```bash
  source venv/bin/activate
  pip install -r platform/backend/requirements.txt
  sudo systemctl restart pr_study
  ```
- 如果改了前端代码 → 需重新构建：
  ```bash
  cd platform/frontend
  npm install
  npm run build
  cp -r frontend/dist/* backend/static/
  sudo systemctl restart pr_study
  ```

---

## 常见问题排查

### 1. 浏览器运行测试报错 `PermissionError`

检查是否有多个 server.py 进程，且属于不同用户：

```bash
ps aux | grep server.py
```

如果有 `www-data` 用户的旧进程，杀掉并重启：

```bash
sudo pkill -f "server.py"
sudo systemctl restart pr_study
```

### 2. pytest 报错 `unrecognized arguments: --alluredir`

pytest 版本太高，allure-pytest 不兼容。降级：

```bash
source venv/bin/activate
pip install pytest==8.3.5
```

### 3. 配置文件找不到 `*.yaml`

缺少 `.env` 文件或 `TEST_ENV` 未设置。Web 平台运行时不需要 `.env`（平台会自动传环境变量），命令行直接运行 pytest 才需要。

### 4. 日志文件权限问题

修复整个 report 目录权限：

```bash
sudo chown -R $(whoami):$(whoami) /opt/pr_study/report/
chmod -R u+w /opt/pr_study/report/
```

### 5. 服务无法启动

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
| 链路选择 | 通过 pytest marker 筛选 link1 ~ link25 |
| 循环执行 | 支持指定循环次数 |
| 实时日志 | SSE 流式推送 pytest 输出到前端，自动滚动 |
| 结果汇总 | 通过 / 失败 / 跳过数量 + 失败用例详情 |
