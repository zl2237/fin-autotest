<template>
  <div class="page">
    <div class="main">
      <div class="manual-container">
        <h1 class="manual-title">PR Study - 项目用户手册</h1>
        <p class="manual-subtitle">接口自动化测试框架 + Web 测试平台</p>

        <el-divider />

        <section class="manual-section">
          <h2>项目简介</h2>
          <p>基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的 38 条链路。</p>
          <p>38 条链路按依赖顺序递增。配置与代码分离，所有业务参数均存储在 YAML，通过 <code>TEST_ENV</code> 切换环境。</p>
        </section>

        <section class="manual-section">
          <h2>核心能力</h2>
          <ul>
            <li>38 条链路，覆盖订单、应付、应收全流程</li>
            <li>workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）</li>
            <li>所有业务配置参数集中存储于 YAML，Python 代码零硬编码</li>
            <li>Web 平台：5 张流程选择卡片、环境管理、链路过滤、循环执行、一键执行、实时日志、执行历史、用户管理</li>
            <li>data 层按环境自动加载 <code>*_tidb.yaml</code> 或 <code>*_pre.yaml</code>，通过 <code>.env</code> 中的 <code>TEST_ENV</code> 切换</li>
            <li>CI 环境自动企微机器人通知</li>
            <li>Allure 报告</li>
          </ul>
        </section>

        <section class="manual-section">
          <h2>技术栈</h2>
          <el-table :data="techStack" stripe size="small" style="width: 100%">
            <el-table-column prop="layer" label="层级" width="120" />
            <el-table-column prop="tech" label="技术" width="140" />
            <el-table-column prop="version" label="版本" />
          </el-table>
        </section>

        <section class="manual-section">
          <h2>目录结构</h2>
          <pre class="code-block">pr_study/
├── api/                            # API 层：HTTP 接口封装，按 order/receive/pay 划分域
│   ├── order/
│   ├── receive/
│   └── pay/
├── config/                         # 配置层
│   └── settings.py                 # 环境变量与全局常量
├── core/                           # 基础设施
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
└── requirements.txt                # Python 依赖</pre>
        </section>

        <section class="manual-section">
          <h2>快速开始</h2>
          <h3>1. 克隆项目</h3>
          <pre class="code-block">git clone http://172.16.18.55:88/root/pr_study.git
cd pr_study</pre>

          <h3>2. 安装依赖</h3>
          <p><strong>后端（Python）：</strong></p>
          <pre class="code-block">cd platform/backend
pip install -r requirements.txt</pre>
          <p><strong>前端（Node.js）：</strong></p>
          <pre class="code-block">cd platform/frontend
npm install</pre>

          <h3>3. 配置环境</h3>
          <p><strong>后端环境变量：</strong></p>
          <pre class="code-block">cp platform/backend/.env.example platform/backend/.env
# 编辑 .env，填入管理员账号和被测系统配置</pre>
          <p><strong>前端代理（开发模式）：</strong></p>
          <p>platform/frontend/vite.config.js 中已配置 Vite 代理到 http://localhost:5000。</p>
        </section>

        <section class="manual-section">
          <h2>运行方式</h2>
          <h3>方式一：开发模式（推荐用于本地调试）</h3>
          <p><strong>终端 1 - 启动 Flask 后端：</strong></p>
          <pre class="code-block">cd platform/backend
python run.py
# 服务运行在 http://localhost:5000</pre>
          <p><strong>终端 2 - 启动 Vue 前端：</strong></p>
          <pre class="code-block">cd platform/frontend
npm run dev
# 访问 http://localhost:3000</pre>

          <h3>方式二：生产模式（Flask 托管构建后的静态文件）</h3>
          <pre class="code-block"># 1. 构建前端
cd platform/frontend
npm run build

# 2. 将构建产物复制到 platform/backend/static
# Linux / macOS
cp -r platform/frontend/dist/* platform/backend/static/
# Windows (PowerShell)
Copy-Item -Recurse platform/frontend/dist/* platform/backend/static/

# 3. 启动 Flask（同时服务 API + 静态页面）
cd platform/backend
python run.py</pre>
        </section>

        <section class="manual-section">
          <h2>Web 平台使用</h2>
          <h3>1. 登录</h3>
          <ul>
            <li>默认手机号：<code>13800000000</code></li>
            <li>默认密码：<code>admin123</code></li>
            <li>在 .env 中修改 ADMIN_PASSWORD</li>
          </ul>

          <h3>2. 环境管理</h3>
          <p>在「环境管理」页面添加被测系统环境：</p>
          <el-table :data="envFields" stripe size="small" style="width: 100%">
            <el-table-column prop="field" label="字段" width="120" />
            <el-table-column prop="desc" label="说明" />
          </el-table>

          <h3>3. 发起测试</h3>
          <ol>
            <li>选择流程卡片</li>
            <li>选择环境</li>
            <li>选择运行链路</li>
            <li>设置循环次数（1~100）</li>
            <li>（可选）输入费用配置 JSON</li>
            <li>点击「开始执行」</li>
          </ol>
          <p>平台将：</p>
          <ul>
            <li>自动写入 .env 凭据</li>
            <li>在子进程中调用 pytest</li>
            <li>通过 SSE 实时推送日志到前端</li>
            <li>将执行结果存入 SQLite</li>
          </ul>

          <h3>4. 执行历史</h3>
          <p>查看历史执行记录，包括状态、链路、耗时、通过/失败数量。</p>
        </section>

        <section class="manual-section">
          <h2>直接运行 pytest（命令行模式）</h2>
          <p>保留原有的 pytest 命令行能力，不依赖 Web 平台：</p>
          <pre class="code-block"># 配置被测系统
cp .env.example .env
# 编辑 .env 填入 BASE_URL、USERNAME、PASSWORD

# 运行
pytest -v                          # 全部
pytest -m order1                   # 仅订单链路1
pytest -m "order_pay_receive1 or order_pay_receive8"       # 多条链路
pytest -m order_pay_receive13      # 订单+应付+应收全流程
pytest -m order_receive_pay13      # 订单+应收+应付全流程</pre>
        </section>

        <section class="manual-section">
          <h2>链路一览（38 条）</h2>
          <el-table :data="linkTable" stripe size="small" style="width: 100%">
            <el-table-column prop="link" label="链路" width="120" />
            <el-table-column prop="stage" label="停止阶段" />
            <el-table-column prop="link2" label="链路" width="120" />
            <el-table-column prop="stage2" label="停止阶段" />
          </el-table>
          <p class="manual-note">实际链路命名：<code>order1~order12</code>、<code>order_pay_receive1~order_pay_receive13</code>、<code>order_receive_pay1~order_receive_pay13</code>。</p>
        </section>

        <section class="manual-section">
          <h2>快捷方法</h2>
          <p>OrderWorkflow 提供 run_until_xxx 系列方法：</p>
          <pre class="code-block">from workflows.order_workflow import OrderWorkflow

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
OrderWorkflow.run_until_receive_account()           # order13
OrderWorkflow.run_until_confirm_account()           # order14
OrderWorkflow.run_until_invoice_batch()             # order15
OrderWorkflow.run_until_invoice_batch_audit()      # order16
OrderWorkflow.run_until_invoice_upload()            # order17
OrderWorkflow.run_until_receive_writeoff()          # order18
OrderWorkflow.run_until_payable_account()           # order19
OrderWorkflow.run_until_confirm_payable()           # order20
OrderWorkflow.run_until_payable_invoice_apply()     # order21
OrderWorkflow.run_until_pay_demand()                # order23
OrderWorkflow.run_until_pay_demand_audit()          # order24
OrderWorkflow.run_until_pay_writeoff()              # order25</pre>
        </section>

        <section class="manual-section">
          <h2>安全提示</h2>
          <ul>
            <li>.env 文件包含敏感凭据，已加入 .gitignore</li>
            <li>生产部署请修改 ADMIN_PASSWORD 和 SECRET_KEY</li>
            <li>如仅内网使用，TOKEN_EXPIRE_SECONDS 可设为 0（永不过期）</li>
            <li>建议在 Nginx 前配置 HTTPS（Let's Encrypt）</li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Expand, Fold, SwitchButton, Files, EditPen, Connection, HomeFilled, User, Edit
} from '@element-plus/icons-vue'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const techStack = [
  { layer: '测试框架', tech: 'pytest', version: '>=7.4.0' },
  { layer: 'HTTP 客户端', tech: 'requests', version: '>=2.31.0' },
  { layer: '日志记录', tech: 'loguru', version: '>=0.7.2' },
  { layer: 'YAML 配置', tech: 'PyYAML', version: '>=6.0' },
  { layer: '后端框架', tech: 'Flask', version: '>=3.0.0' },
  { layer: '数据库', tech: 'SQLite', version: '3.x（无需额外服务）' },
  { layer: '前端框架', tech: 'Vue 3 + Vite', version: '^3.4 / ^5.0' },
  { layer: 'UI 组件库', tech: 'Element Plus', version: '^2.4.0' },
]

const envFields = [
  { field: '名称', desc: '如 uat、sit、prod' },
  { field: 'API 地址', desc: '被测系统域名，如 https://xxx.com' },
  { field: '账号 / 密码', desc: '登录凭据' },
  { field: 'Token 字段', desc: '响应中 token 路径，默认 data.token' },
  { field: '默认', desc: '是否设为默认环境' },
]

const linkTable = [
  { link: 'order1', stage: '新建', link2: 'order_pay_receive1', stage2: '发起应付对账批次' },
  { link: 'order2', stage: '分发', link2: 'order_pay_receive2', stage2: '确认应付对账' },
  { link: 'order3', stage: '暂存', link2: 'order_pay_receive3', stage2: '发起应付开票批次申请' },
  { link: 'order4', stage: '提交', link2: 'order_pay_receive4', stage2: '应付发票上传与登记' },
  { link: 'order5', stage: '生成子订单', link2: 'order_pay_receive5', stage2: '发起付款需求' },
  { link: 'order6', stage: '录费用', link2: 'order_pay_receive6', stage2: '审核生成付款单' },
  { link: 'order7', stage: '资产推送审批', link2: 'order_pay_receive7', stage2: '付款单核销' },
  { link: 'order8', stage: '订单锁定审批', link2: 'order_pay_receive8', stage2: '发起应收对账批次' },
  { link: 'order9', stage: '未放款开票申请审批', link2: 'order_pay_receive9', stage2: '确认应收对账' },
  { link: 'order10', stage: '供应商垫付申请审批', link2: 'order_pay_receive10', stage2: '发起应收开票批次审批' },
  { link: 'order11', stage: '生成费用通知单', link2: 'order_pay_receive11', stage2: '审核生成开票申请' },
  { link: 'order12', stage: '生成费用确认单', link2: 'order_pay_receive12', stage2: '发票上传与登记' },
  { link: 'order_pay_receive13', stage: '应收核销', link2: 'order_receive_pay1', stage2: '发起应收对账批次' },
  { link: 'order_receive_pay2', stage: '确认应收对账', link2: 'order_receive_pay3', stage2: '发起应收开票批次审批' },
  { link: 'order_receive_pay4', stage: '审核生成开票申请', link2: 'order_receive_pay5', stage2: '发票上传与登记' },
  { link: 'order_receive_pay6', stage: '应收核销', link2: 'order_receive_pay7', stage2: '发起应付对账批次' },
  { link: 'order_receive_pay8', stage: '确认应付对账', link2: 'order_receive_pay9', stage2: '发起应付开票批次申请' },
  { link: 'order_receive_pay10', stage: '应付发票上传与登记', link2: 'order_receive_pay11', stage2: '发起付款需求' },
  { link: 'order_receive_pay12', stage: '审核生成付款单', link2: 'order_receive_pay13', stage2: '付款单核销' },
  { link: '', stage: '', link2: '', stage2: '' },
]
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f0f2f5;
}

.main {
  padding: 24px;
}

.manual-container {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.manual-title {
  margin: 0 0 4px;
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
}
.manual-subtitle {
  margin: 0 0 16px;
  font-size: 14px;
  color: #667eea;
  font-weight: 500;
}
.manual-section {
  margin-bottom: 24px;
}
.manual-section h2 {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}
.manual-section h2::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 18px;
  background: linear-gradient(180deg, #667eea, #764ba2);
  border-radius: 2px;
}
.manual-section h3 {
  margin: 16px 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: #606266;
}
.manual-section p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
}
.manual-section ul,
.manual-section ol {
  margin: 8px 0;
  padding-left: 24px;
  color: #606266;
  line-height: 1.8;
}
.manual-section li {
  margin-bottom: 4px;
}
.manual-section code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 13px;
  color: #667eea;
}
.code-block {
  background: #1a1a2e;
  color: #c9d1d9;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  margin: 8px 0;
}
.manual-note {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
  font-style: italic;
}
:deep(.el-divider) {
  margin: 16px 0 24px;
}
:deep(.el-table) {
  margin: 12px 0;
  border-radius: 8px;
  overflow: hidden;
}
</style>
