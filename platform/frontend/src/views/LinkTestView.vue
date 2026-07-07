<template>
  <div class="page">
    <!-- 主内容区 -->
    <div class="main">
      <!-- 警告提示 -->
      <div class="warning-banner">
        <el-alert
          type="warning"
          :closable="false"
          show-icon
        >
          <template #title>
            <span class="warning-title">提醒</span>
          </template>
          <template #default>
            <span class="warning-text">运行前请确保测试账号已配置到以下审批流节点：资产推送、订单锁定、未放款开票申请、供应商垫付申请、应收开票申请、付款需求申请</span>
          </template>
        </el-alert>
      </div>

      <!-- 配置卡片区 -->
      <div class="config-cards">
        <!-- 流程选择 -->
        <el-card class="cfg-card workflow-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Connection /></el-icon>
              <span>流程选择</span>
            </div>
          </template>
          <div class="workflow-options">
            <div
              v-for="item in formStore.workflowCards"
              :key="item.id"
              class="workflow-option"
              :class="{ active: formStore.activeCard?.id === item.id }"
              @click="formStore.setWorkflowCard(item.id)"
            >
              <span v-if="item.tag" class="workflow-tag">{{ item.tag }}</span>
              <div class="workflow-option-body">
                <div class="workflow-label">{{ item.label }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 环境配置 -->
        <el-card class="cfg-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>环境配置</span>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="BASE_URL">
              <el-select
                v-model="formStore.data.base_url"
                placeholder="请选择环境"
                style="width: 100%"
                @change="formStore.patch({ base_url: formStore.data.base_url })"
              >
                <el-option label="TIDB（测试）" value="https://fin-tidb.21eflag.com/" />
                <el-option label="PRE（预发）" value="https://fin-pre.21eflag.com/" />
              </el-select>
            </el-form-item>
            <el-form-item label="LOGIN_URL">
              <el-input
                v-model="formStore.data.login_url"
                placeholder="/api/home/login/userLogin"
                clearable
                @change="formStore.patch({ login_url: formStore.data.login_url })"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 测试账号 -->
        <el-card class="cfg-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>测试账号</span>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="USERNAME">
              <el-input
                v-model="formStore.data.test_username"
                placeholder="测试账号"
                clearable
                @change="formStore.patch({ test_username: formStore.data.test_username })"
              />
            </el-form-item>
            <el-form-item label="PASSWORD">
              <el-input
                v-model="formStore.data.test_password"
                type="password"
                show-password
                placeholder="测试密码"
                @change="formStore.patch({ test_password: formStore.data.test_password })"
              />
            </el-form-item>
            <el-form-item label="USER_ID">
              <el-input
                v-model="formStore.data.order_create_id"
                placeholder="创建者用户ID"
                clearable
                @change="formStore.patch({ order_create_id: formStore.data.order_create_id })"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 执行配置 -->
        <el-card class="cfg-card execution-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>执行配置</span>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <div class="execution-grid">
              <el-form-item label="运行链路">
                <el-select
                  v-model="formStore.data.marker"
                  placeholder="请选择"
                  filterable
                  style="width: 100%"
                  @change="formStore.patch({ marker: formStore.data.marker })"
                >
                  <el-option
                    v-for="item in filteredMarkers"
                    :key="item.name"
                    :label="`${item.name} - ${item.description}`"
                    :value="item.name"
                  />
                </el-select>
              </el-form-item>
            <el-form-item label="提单号前缀">
              <el-input
                v-model="formStore.data.order_prefix"
                placeholder="仅限字母、数字、下划线、短横线，不超过5位"
                clearable
                @change="formStore.patch({ order_prefix: formStore.data.order_prefix })"
              />
            </el-form-item>
              <el-form-item label="循环次数">
                <el-input-number
                  v-model="formStore.data.loop_count"
                  :min="1"
                  :max="100"
                  style="width: 100%"
                  @change="formStore.patch({ loop_count: formStore.data.loop_count })"
                />
              </el-form-item>
            </div>
          </el-form>
        </el-card>
      </div>

      <!-- 执行按钮 -->
      <div class="execute-section">
        <button
          class="execute-btn"
          :class="{ running: running }"
          :disabled="!formStore.data.marker || running"
          @click="handleRun"
        >
          <span class="execute-btn-content">
            <el-icon v-if="running" class="spin-icon"><Loading /></el-icon>
            <el-icon v-else><VideoPlay /></el-icon>
            <span class="execute-btn-text">{{ running ? '执行中...' : '开始执行' }}</span>
          </span>
        </button>
      </div>

      <!-- 结果 + 日志 -->
      <div class="bottom-panels">
        <!-- 执行结果卡片 -->
        <el-card class="result-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>执行结果</span>
              <el-button v-if="run.run_id" type="danger" size="small" plain @click="clearHistory">清除记录</el-button>
            </div>
          </template>

          <!-- 运行中 -->
          <template v-if="running">
            <div class="running-indicator">
              <div class="pulse-ring" />
              <div class="pulse-dot" />
              <span class="running-text">运行中...</span>
              <el-tag v-if="run.marker" type="primary" size="small">{{ run.marker }}</el-tag>
            </div>
          </template>

          <!-- 通过 -->
          <template v-else-if="run.status === 'completed' || run.status === 'success'">
            <div class="result-summary">
              <div class="result-status result-success">
                <el-icon class="status-icon"><CircleCheckFilled /></el-icon>
                <span>全部通过</span>
              </div>
              <div class="stats-grid">
                <div class="stat-card total">
                  <span class="stat-label">总计</span>
                  <span class="stat-value">{{ summary.total }}</span>
                  <span class="stat-meta">{{ run.marker }}</span>
                </div>
                <div class="stat-card passed">
                  <span class="stat-label">Passed</span>
                  <span class="stat-value">{{ summary.passed }}</span>
                  <span class="stat-meta">用例通过</span>
                </div>
                <div class="stat-card failed">
                  <span class="stat-label">Failed</span>
                  <span class="stat-value">{{ summary.failed }}</span>
                  <span class="stat-meta">用例失败</span>
                </div>
                <div class="stat-card skipped">
                  <span class="stat-label">Skipped</span>
                  <span class="stat-value">{{ summary.skipped }}</span>
                  <span class="stat-meta">跳过用例</span>
                </div>
              </div>
              <el-collapse v-if="summary.failed > 0" style="margin-top: 12px">
                <el-collapse-item title="失败用例详情" name="failures">
                  <el-table :data="failedCases" stripe size="small">
                    <el-table-column prop="name" label="用例" min-width="200" show-overflow-tooltip />
                    <el-table-column prop="message" label="原因" min-width="200" show-overflow-tooltip />
                  </el-table>
                </el-collapse-item>
              </el-collapse>
            </div>
          </template>

          <!-- 失败 -->
          <template v-else-if="run.status === 'failed'">
            <div class="result-status result-error">
              <el-icon class="status-icon"><CircleCloseFilled /></el-icon>
              <span>执行失败</span>
            </div>
            <el-alert :title="run.result?.error || 'pytest 退出码非 0'" type="error" :closable="false" />
          </template>

          <!-- 初始 -->
          <template v-else>
            <el-empty description="选择链路并点击「开始执行」" :image-size="80" />
          </template>
        </el-card>

        <!-- 日志卡片 -->
        <el-card class="log-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>运行日志</span>
              <el-tag v-if="logs.length" type="info" size="small">{{ logs.length }} 行</el-tag>
              <el-button v-if="logs.length" type="info" size="small" plain @click="logs = []">清空日志</el-button>
            </div>
          </template>
          <div class="log-box" ref="logBoxRef">
            <div v-if="logs.length === 0 && !running" class="log-empty">暂无日志</div>
            <div v-for="(line, idx) in logs" :key="idx" class="log-line" :class="logClass(line)">{{ line }}</div>
            <div v-if="running" class="log-cursor">_</div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Monitor, User, Setting, DataAnalysis, Document,
  VideoPlay, CircleCheckFilled, CircleCloseFilled, Connection, Loading
} from '@element-plus/icons-vue'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'
import { useFormStore } from '@/stores/form'

const router = useRouter()
const auth = useAuthStore()
const formStore = useFormStore()
const logBoxRef = ref<HTMLElement>()
const markers = ref<Array<{ name: string; description: string }>>([])

const run = ref<any>({ run_id: '', status: '', marker: '', result: {}, logs: [] })
const logs = ref<string[]>([])
const running = ref(false)

const summary = computed(() => run.value.result?.summary || {})
const failedCases = computed(() => summary.value.details?.failed || [])

const filteredMarkers = computed(() => {
  const allowed = formStore.activeCard?.markers ?? []
  return markers.value.filter(item => allowed.includes(item.name))
})

// localStorage 记忆键
const STORAGE_KEY = 'link_test_state_v1'

function loadSavedState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return
    const data = JSON.parse(saved)
    if (data.run) run.value = data.run
    if (data.logs) logs.value = data.logs
    if (typeof data.running === 'boolean') running.value = data.running
  } catch {
    // 忽略解析失败
  }
}

function saveState() {
  try {
    const payload = {
      run: run.value,
      logs: logs.value,
      running: running.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch {
    // 忽略存储失败
  }
}

// 从 base_url 提取环境标识（test_env），传给后端用于 data 层 YAML 切换
const testEnv = computed(() => {
  const url = formStore.data.base_url || ""
  if (url.includes("tidb")) return "tidb"
  if (url.includes("pre")) return "pre"
  return ""
})

function handleLogout() {
  auth.logout()
  router.push({ name: 'Login' })
}

async function loadMarkers() {
  try {
    const { data } = await request.get('/markers')
    markers.value = data.markers
    if (markers.value.length && !formStore.data.marker) {
      formStore.patch({ marker: markers.value[0].name })
    }
  } catch (e) {
    ElMessage.error('加载链路失败')
  }
}

async function handleRun() {
  if (!formStore.data.base_url || !formStore.data.test_username || !formStore.data.test_password) {
    ElMessage.warning('请填写 BASE_URL、测试账号和密码')
    return
  }
  if (!formStore.data.marker) {
    ElMessage.warning('请选择运行链路')
    return
  }
  const prefix = (formStore.data.order_prefix || '').trim()
  if (/[^a-zA-Z0-9_-]/.test(prefix)) {
    ElMessage.warning('提单号前缀仅限字母、数字、下划线和短横线')
    return
  }
  if (prefix.length > 5) {
    ElMessage.warning('提单号前缀不能超过5位')
    return
  }

  formStore.save()
  running.value = true
  logs.value = []
  run.value.run_id = ''
  run.value.status = 'running'
  run.value.result = {}

  try {
    const { data } = await request.post('/run', {
      base_url: formStore.data.base_url,
      login_url: formStore.data.login_url,
      test_username: formStore.data.test_username,
      test_password: formStore.data.test_password,
      token_field: formStore.data.token_field,
      token_type: formStore.data.token_type,
      auth_header: formStore.data.auth_header,
      marker: formStore.data.marker,
      order_prefix: formStore.data.order_prefix,
      loop_count: formStore.data.loop_count,
      order_create_id: formStore.data.order_create_id,
      test_env: testEnv.value,
    })
    if (!data.ok) {
      throw new Error(data.message || '启动失败')
    }
    run.value.run_id = data.run_id
    run.value.marker = data.marker
    listenLogs(data.run_id)
  } catch (e: any) {
    ElMessage.error(e?.message || '启动失败')
    run.value.status = 'failed'
    running.value = false
  }
}

function listenLogs(runId: string) {
  const logUrl = import.meta.env.DEV
    ? `http://localhost:5000/api/run/${runId}/logs`
    : `/api/run/${runId}/logs`
  const es = new EventSource(logUrl)
  es.onmessage = (e) => {
    logs.value.push(e.data)
    nextTick(() => {
      if (logBoxRef.value) {
        logBoxRef.value.scrollTop = logBoxRef.value.scrollHeight
      }
    })
  }
  es.addEventListener('done', async () => {
    es.close()
    running.value = false
    try {
      const resp = await request.get(`/run/${runId}`)
      run.value.status = resp.data.status === 'failed' ? 'failed' : 'completed'
      run.value.result = resp.data.result || {}
      run.value.logs = resp.data.logs || []
    } catch {
      run.value.status = 'completed'
    }
  })
  es.onerror = () => {
    es.close()
    running.value = false
    if (!run.value.status) run.value.status = 'failed'
  }
}

function logClass(line: string) {
  if (line.includes('FAILED') || line.includes('ERROR')) return 'log-fail'
  if (line.includes('PASSED') || line.includes('test session starts') || line.includes('passed')) return 'log-pass'
  if (line.includes('WARNING') || line.includes('WARN')) return 'log-warn'
  if (line.startsWith('=') || line.trim() === '') return 'log-sep'
  return ''
}

function clearHistory() {
  run.value = { run_id: '', status: '', marker: '', result: {}, logs: [] }
  logs.value = []
  running.value = false
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
  ElMessage.success('历史记录已清除')
}

watch(
  [run, logs, running],
  () => {
    saveState()
  },
  { deep: true }
)

onMounted(() => {
  loadSavedState()
  loadMarkers()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f0f2f5;
}

.main {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 警告提示 */
.warning-banner {
  background: rgba(255,255,255,0.95);
  border-radius: 12px;
  padding: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
:deep(.el-alert--warning) {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
}
:deep(.el-alert--warning .el-alert__icon) {
  color: #faad14;
  font-size: 16px;
}
:deep(.el-alert--warning .el-alert__title) {
  color: #d48806;
  font-size: 14px;
}
:deep(.el-alert--warning .el-alert__description) {
  color: #ad6800;
  font-size: 13px;
  line-height: 1.6;
}
.warning-title {
  font-weight: 600;
}
.warning-text {
  font-size: 13px;
  line-height: 1.5;
}

/* 配置卡片区 */
.config-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.workflow-card {
  grid-column: 1 / -1;
}
.execution-card {
  grid-column: 1 / -1;
}
.cfg-card {
  border-radius: 12px;
  border: none;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
:deep(.cfg-card .el-card__header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 12px 12px 0 0;
  border-bottom: none;
}
:deep(.cfg-card .el-card__body) {
  padding: 16px;
}
:deep(.el-form-item__label) {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}
:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  box-shadow: none;
}
:deep(.el-input__wrapper:hover),
:deep(.el-select__wrapper:hover) {
  border-color: #c0c4cc;
}
:deep(.el-input__inner) {
  color: #303133;
}
:deep(.el-input__wrapper.is-focus),
:deep(.el-select__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102,126,234,0.2);
}
:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background: #f5f7fa;
  color: #606266;
  border-color: #e4e7ed;
}
:deep(.el-input-number__decrease:hover),
:deep(.el-input-number__increase:hover) {
  color: #667eea;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.workflow-options {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}
.workflow-option {
  position: relative;
  border: 2px solid #d0d5f0;
  border-radius: 12px;
  padding: 14px 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 86px;
  background: #f0f2ff;
  transition: border-color 0.25s, box-shadow 0.25s, transform 0.2s, background 0.25s;
  overflow: hidden;
}
.workflow-option::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(102,126,234,0.12) 0%, rgba(118,75,162,0.12) 100%);
  opacity: 0;
  transition: opacity 0.3s;
}
.workflow-option:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 0 16px rgba(102,126,234,0.25), 0 4px 20px rgba(102,126,234,0.15);
  background: #eef1ff;
}
.workflow-option:hover::before {
  opacity: 1;
}
.workflow-option.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #eef1ff 0%, #ddd6fe 100%);
  box-shadow:
    0 0 0 2px rgba(102,126,234,0.3),
    0 0 20px rgba(102,126,234,0.2),
    0 4px 16px rgba(102,126,234,0.15);
  animation: card-glow 2s ease-in-out infinite alternate;
}
@keyframes card-glow {
  from { box-shadow: 0 0 0 2px rgba(102,126,234,0.3), 0 0 20px rgba(102,126,234,0.2), 0 4px 16px rgba(102,126,234,0.15); }
  to   { box-shadow: 0 0 0 3px rgba(102,126,234,0.5), 0 0 30px rgba(102,126,234,0.3), 0 6px 20px rgba(102,126,234,0.2); }
}
.workflow-tag {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 2px 6px;
  border-radius: 4px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  pointer-events: none;
  text-transform: uppercase;
  z-index: 1;
}
.workflow-option-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-align: center;
}
.workflow-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  line-height: 1.35;
}

.execution-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 12px;
}

/* 执行按钮区域 */
.execute-section {
  width: 100%;
  max-width: 1200px;
}
.execute-btn {
  width: 100%;
  padding: 20px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(102,126,234,0.4);
  position: relative;
  overflow: hidden;
}
.execute-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}
.execute-btn:hover:not(:disabled)::before {
  left: 100%;
}
.execute-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(102,126,234,0.5);
}
.execute-btn:active:not(:disabled) {
  transform: translateY(0);
}
.execute-btn:disabled {
  background: linear-gradient(135deg, #606c80 0%, #3f4c6b 100%);
  cursor: not-allowed;
  box-shadow: none;
}
.execute-btn.running {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}
.execute-btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.execute-btn-text {
  letter-spacing: 2px;
}
.spin-icon {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 底部面板区 */
.bottom-panels {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-height: 0;
}

.result-card,
.log-card {
  border-radius: 12px;
  border: none;
  display: flex;
  flex-direction: column;
}
:deep(.result-card .el-card__header),
:deep(.log-card .el-card__header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  color: #fff;
  border-radius: 12px 12px 0 0;
}
:deep(.result-card .el-card__body),
:deep(.log-card .el-card__body) {
  padding: 16px;
  flex: 1;
  overflow: hidden;
}

/* 运行状态指示器 */
.running-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  position: relative;
}
.pulse-ring {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid #409eff;
  position: absolute;
  left: 0;
  animation: pulse-ring 1.6s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}
.pulse-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #409eff;
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  animation: pulse-dot 1.6s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}
@keyframes pulse-ring {
  0% { transform: scale(0.6); opacity: 1; }
  100% { transform: scale(1.4); opacity: 0; }
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.running-text {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  margin-left: 44px;
}

/* 结果统计卡片 */
.result-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.result-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}
.result-success {
  background: #f0f9eb;
  color: #67c23a;
}
.result-error {
  background: #fef0f0;
  color: #f56c6c;
}
.status-icon {
  font-size: 20px;
}

/* 统计指标网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.stat-card {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: box-shadow 0.2s;
}
.stat-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stat-card.total { border-top: 3px solid #909399; }
.stat-card.passed { border-top: 3px solid #67c23a; }
.stat-card.failed { border-top: 3px solid #f56c6c; }
.stat-card.skipped { border-top: 3px solid #909399; }
.stat-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}
.stat-card.passed .stat-value { color: #67c23a; }
.stat-card.failed .stat-value { color: #f56c6c; }
.stat-card.total .stat-value { color: #303133; }
.stat-card.skipped .stat-value { color: #909399; }
.stat-meta {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 2px;
}

/* 日志区 */
.log-box {
  background: #0d1117;
  border-radius: 8px;
  height: 100%;
  max-height: 380px;
  overflow-y: auto;
  padding: 12px 16px;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.7;
  border: 1px solid #21262d;
}
.log-empty {
  color: #484f58;
  text-align: center;
  padding: 32px;
}
.log-line {
  white-space: pre-wrap;
  word-break: break-all;
  color: #c9d1d9;
}
.log-cursor {
  color: #58a6ff;
  animation: blink 1s step-end infinite;
}
.log-pass { color: #3fb950; }
.log-fail { color: #f85149; }
.log-warn { color: #d29922; }
.log-sep { color: #484f58; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

:deep(.el-empty__description p) {
  color: #aaa;
}

/* 响应式 */
@media (max-width: 1024px) {
  .bottom-panels {
    grid-template-columns: 1fr;
  }
  .config-cards {
    grid-template-columns: 1fr;
  }
  .workflow-options {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .execution-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 768px) {
  .workflow-options {
    grid-template-columns: 1fr;
  }
}
</style>
