<template>
  <div class="page">
    <!-- 左侧可折叠导航栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- 折叠按钮 -->
      <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
      </button>

      <!-- 品牌区 -->
      <div class="sidebar-brand">
        <svg class="brand-icon" viewBox="0 0 24 24" fill="none">
          <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0-6v6m18-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="brand-text">API 测试平台</span>
      </div>

      <!-- 用户信息 -->
      <div class="sidebar-user">
        <el-tag type="info" size="small" effect="plain">PR Study</el-tag>
        <span class="username">{{ auth.username }}</span>
        <el-button type="danger" plain size="small" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span v-show="!sidebarCollapsed">退出</span>
        </el-button>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="$route.path"
        class="sidebar-menu"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页概览</template>
        </el-menu-item>
        <el-sub-menu index="logistics">
          <template #title>
            <el-icon><Connection /></el-icon>
            <span>物流系统</span>
          </template>
          <el-menu-item index="/logistics/link-test">
            <el-icon><Connection /></el-icon>
            <span>链路测试</span>
          </el-menu-item>
          <el-menu-item index="/logistics/document-upload">
            <el-icon><Files /></el-icon>
            <span>单证上传</span>
          </el-menu-item>
          <el-menu-item index="/logistics/approval-config">
            <el-icon><EditPen /></el-icon>
            <span>审批流配置</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </aside>

    <!-- 主内容区 -->
    <div class="main">
      <div class="manual-container">
        <h1 class="manual-title">PR Study - 项目用户手册</h1>
        <p class="manual-subtitle">接口自动化测试框架 + Web 测试平台</p>

        <el-divider />

        <section class="manual-section">
          <h2>项目简介</h2>
          <p>基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的 25 条链路。</p>
        </section>

        <section class="manual-section">
          <h2>核心能力</h2>
          <ul>
            <li>25 条链路（link1~link25），按依赖顺序递增，link25 隐含 link1~link24</li>
            <li>workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）</li>
            <li>所有业务配置参数集中存储于 YAML，Python 代码零硬编码</li>
            <li>Web 平台：环境管理、一键执行、实时日志、执行历史</li>
            <li>CI 环境自动企微机器人通知</li>
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

# 2. 将构建产物复制到 backend/static
#    Windows (PowerShell):
#    Copy-Item -Recurse dist\* ..\backend\app\static\

# 3. 启动 Flask（同时服务 API + 静态页面）
cd platform/backend
python run.py</pre>
        </section>

        <section class="manual-section">
          <h2>Web 平台使用</h2>
          <h3>1. 登录</h3>
          <ul>
            <li>默认账号：<code>admin</code></li>
            <li>默认密码：<code>admin123</code></li>
            <li>在 .env 中修改 ADMIN_USERNAME / ADMIN_PASSWORD</li>
          </ul>

          <h3>2. 环境管理</h3>
          <p>在「环境管理」页面添加被测系统环境：</p>
          <el-table :data="envFields" stripe size="small" style="width: 100%">
            <el-table-column prop="field" label="字段" width="120" />
            <el-table-column prop="desc" label="说明" />
          </el-table>

          <h3>3. 发起测试</h3>
          <ol>
            <li>选择环境</li>
            <li>勾选要执行的链路（可多选，如 link1~link25）</li>
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
pytest -m link1                    # 仅链路1
pytest -m "link11 or link12"       # 多条链路
pytest -m link25                   # 全流程</pre>
        </section>

        <section class="manual-section">
          <h2>链路一览（25 条）</h2>
          <el-table :data="linkTable" stripe size="small" style="width: 100%">
            <el-table-column prop="link" label="链路" width="100" />
            <el-table-column prop="stage" label="停止阶段" />
            <el-table-column prop="link2" label="链路" width="100" />
            <el-table-column prop="stage2" label="停止阶段" />
          </el-table>
          <p class="manual-note">链路按依赖顺序递增，link25 隐含 link1~link24 的全部步骤。</p>
        </section>

        <section class="manual-section">
          <h2>快捷方法</h2>
          <p>OrderWorkflow 提供 run_until_xxx 系列方法：</p>
          <pre class="code-block">from workflows.order_workflow import OrderWorkflow

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
OrderWorkflow.run_until_pay_writeoff()              # link25</pre>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Expand, Fold, SwitchButton, Files, EditPen, Connection, HomeFilled
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const sidebarCollapsed = ref(false)

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
  { link: 'link1', stage: '新建', link2: 'link14', stage2: '确认应收对账' },
  { link: 'link2', stage: '分发', link2: 'link15', stage2: '发起应收开票批次审批' },
  { link: 'link3', stage: '暂存', link2: 'link16', stage2: '审核生成开票申请' },
  { link: 'link4', stage: '提交', link2: 'link17', stage2: '发票上传与登记' },
  { link: 'link5', stage: '生成子订单', link2: 'link18', stage2: '应收核销' },
  { link: 'link6', stage: '录费用', link2: 'link19', stage2: '发起应付对账批次' },
  { link: 'link7', stage: '资产推送审批', link2: 'link20', stage2: '确认应付对账' },
  { link: 'link8', stage: '订单锁定审批', link2: 'link21', stage2: '发起应付开票批次申请' },
  { link: 'link9', stage: '未放款开票申请审批', link2: 'link22', stage2: '应付发票上传与登记' },
  { link: 'link10', stage: '供应商垫付申请审批', link2: 'link23', stage2: '发起付款需求' },
  { link: 'link11', stage: '生成费用通知单', link2: 'link24', stage2: '审核生成付款单' },
  { link: 'link12', stage: '生成费用确认单', link2: 'link25', stage2: '付款单核销' },
  { link: 'link13', stage: '发起应收对账批次', link2: '', stage2: '' },
]

function handleLogout() {
  auth.logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f0f2f5;
}

/* 左侧边栏 */
.sidebar {
  width: 280px;
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  transition: width 0.3s ease;
  overflow-x: hidden;
}
.sidebar.collapsed {
  width: 64px;
}

/* 折叠按钮 */
.sidebar-toggle {
  position: absolute;
  top: 12px;
  right: -12px;
  width: 24px;
  height: 24px;
  background: #1a1a2e;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 101;
  transition: all 0.2s;
}
.sidebar-toggle:hover {
  background: #667eea;
  border-color: #667eea;
}

/* 品牌区 */
.sidebar-brand {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.collapsed .sidebar-brand {
  justify-content: center;
  padding: 16px 8px;
}
.brand-icon {
  width: 28px;
  height: 28px;
  color: #667eea;
  flex-shrink: 0;
}
.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
  white-space: nowrap;
  overflow: hidden;
}
.collapsed .brand-text {
  display: none;
}

/* 用户区 */
.sidebar-user {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.collapsed .sidebar-user {
  flex-direction: column;
  padding: 12px 8px;
  gap: 8px;
}
.username {
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
:deep(.el-tag--info) {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
  color: #fff;
}
:deep(.el-button--danger.is-plain) {
  color: rgba(255,255,255,0.7);
  border-color: rgba(255,255,255,0.2);
  background: transparent;
  padding: 6px 8px;
}
:deep(.el-button--danger.is-plain:hover) {
  color: #fff;
  border-color: rgba(255,255,255,0.5);
  background: rgba(245,108,108,0.2);
}

/* 导航菜单 */
.sidebar-menu {
  background: transparent;
  border-right: none;
}
:deep(.el-menu) {
  background: transparent;
}
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: rgba(255,255,255,0.85);
  height: 44px;
  line-height: 44px;
}
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(102,126,234,0.2);
  color: #fff;
}
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #667eea, #764ba2);
  color: #fff;
}
:deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
  height: 40px;
  line-height: 40px;
}
:deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
}

/* 主内容区 */
.main {
  flex: 1;
  margin-left: 280px;
  padding: 24px;
  transition: margin-left 0.3s ease;
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
