<template>
  <div class="page">
    <div class="main">
      <el-card class="placeholder-card" shadow="hover">
        <div class="placeholder-icon">
          <el-icon :size="64" color="#667eea"><FolderOpened /></el-icon>
        </div>
        <h2 class="placeholder-title">功能开发中</h2>
        <p class="placeholder-desc">该模块正在搭建，敬请期待。</p>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { FolderOpened } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

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

.main {
  margin-left: 280px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: margin-left 0.3s ease;
}
.placeholder-card {
  max-width: 520px;
  width: 100%;
  border-radius: 16px;
  border: none;
  text-align: center;
  padding: 48px 24px;
}
.placeholder-icon {
  margin-bottom: 16px;
  opacity: 0.85;
}
.placeholder-title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.placeholder-desc {
  margin: 0;
  font-size: 14px;
  color: #909399;
}
</style>
