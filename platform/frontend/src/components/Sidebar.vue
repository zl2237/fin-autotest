<template>
  <aside class="sidebar" :class="{ collapsed: collapsed }">
    <button class="sidebar-toggle" @click="$emit('toggle')">
      <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
    </button>

    <div class="sidebar-brand">
      <svg class="brand-icon" viewBox="0 0 24 24" fill="none">
        <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0-6v6m18-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span class="brand-text">API 测试平台</span>
    </div>

    <div class="sidebar-user">
      <el-tag type="info" size="small" effect="plain">PR Study</el-tag>
      <span class="username">{{ displayName }}</span>
      <el-button type="danger" plain size="small" @click="$emit('logout')">
        <el-icon><SwitchButton /></el-icon>
        <span v-show="!collapsed">退出</span>
      </el-button>
      <el-button type="danger" plain size="small" @click="$emit('profile')">
        <el-icon><Edit /></el-icon>
        <span v-show="!collapsed">修改个人信息</span>
      </el-button>
    </div>

    <el-menu
      :default-active="active"
      class="sidebar-menu"
      :collapse="collapsed"
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
          <template #title>链路测试</template>
        </el-menu-item>
        <el-menu-item index="/logistics/document-upload">
          <el-icon><Files /></el-icon>
          <template #title>单证上传</template>
        </el-menu-item>
        <el-menu-item index="/logistics/approval-config">
          <el-icon><EditPen /></el-icon>
          <template #title>审批流配置</template>
        </el-menu-item>
      </el-sub-menu>
      <el-menu-item v-if="isAdmin" index="/platform/users">
        <el-icon><User /></el-icon>
        <template #title>用户管理</template>
      </el-menu-item>
    </el-menu>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Expand, Fold, SwitchButton, Files, EditPen, Connection, HomeFilled, Edit, User } from '@element-plus/icons-vue'

const props = defineProps<{
  collapsed: boolean
  active: string
  isAdmin: boolean
  name?: string
  username: string
}>()

defineEmits<{
  (e: 'toggle'): void
  (e: 'profile'): void
  (e: 'logout'): void
}>()

const displayName = computed(() => props.name?.trim() || props.username)
</script>

<style scoped>
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
</style>
