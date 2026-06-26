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
import {
  Fold, Expand, SwitchButton, Files, EditPen, Connection, HomeFilled, FolderOpened
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const sidebarCollapsed = ref(false)

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
