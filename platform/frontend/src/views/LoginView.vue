<template>
  <div class="login-page">
    <div class="bg-orb bg-orb-1" />
    <div class="bg-orb bg-orb-2" />
    <div class="bg-orb bg-orb-3" />
    <el-card class="login-card">
      <div class="card-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0-6v6m18-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <h2 class="card-title">API 测试平台</h2>
      <p class="card-subtitle">PR Study Automation</p>
      <el-divider />
      <el-form :model="form" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="手机号">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            size="large"
            prefix-icon="Phone"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item style="margin-top: 24px">
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="!form.phone || !form.password"
            @click="handleLogin"
            style="width: 100%; font-size: 16px; height: 44px"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const form = reactive({ phone: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (!form.phone || !form.password) return
  loading.value = true
  try {
    const { data } = await request.post('/auth/login', form)
    if (data.ok) {
      auth.login(data.username, data.token, data.role, data.name, data.phone, data.email, data.user_id)
      ElMessage.success(`欢迎回来，${data.name || data.username}`)
      router.push({ name: 'Home' })
    }
  } catch (e: any) {
    const message = e?.response?.data?.message || e?.message || '登录失败，请检查网络'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  position: relative;
  overflow: hidden;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  pointer-events: none;
}
.bg-orb-1 {
  width: 500px;
  height: 500px;
  background: #667eea;
  top: -100px;
  left: -100px;
  animation: float1 8s ease-in-out infinite;
}
.bg-orb-2 {
  width: 400px;
  height: 400px;
  background: #764ba2;
  bottom: -80px;
  right: -80px;
  animation: float2 10s ease-in-out infinite;
}
.bg-orb-3 {
  width: 300px;
  height: 300px;
  background: #f093fb;
  top: 50%;
  left: 60%;
  animation: float3 12s ease-in-out infinite;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, 20px); }
}
@keyframes float2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-20px, -30px); }
}
@keyframes float3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-15px, 25px); }
}

.login-card {
  width: 400px;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.05);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  padding: 8px 0;
}

.card-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}
.card-icon svg {
  width: 48px;
  height: 48px;
  color: #667eea;
}

.card-title {
  text-align: center;
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: 1px;
}
.card-subtitle {
  text-align: center;
  margin: 4px 0 0;
  font-size: 12px;
  color: #888;
  letter-spacing: 2px;
  text-transform: uppercase;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #444;
  font-size: 13px;
  padding-bottom: 4px !important;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e0e0e0 inset;
  transition: all 0.2s;
}
:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #667eea inset !important;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 10px;
  font-weight: 600;
  letter-spacing: 2px;
  transition: all 0.3s;
}
:deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}
:deep(.el-button--primary:active) {
  transform: translateY(0);
}
:deep(.el-button--primary.is-disabled) {
  background: #c0b8e0;
}
</style>
