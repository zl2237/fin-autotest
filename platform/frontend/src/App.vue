<template>
  <Sidebar
    v-if="showSidebar"
    :collapsed="collapsed"
    :active="route.path"
    :is-admin="isAdmin"
    :name="displayName"
    :username="username"
    @toggle="collapsed = !collapsed"
    @profile="openProfile"
    @logout="handleLogout"
  />
  <div class="app-main" :class="{ 'has-sidebar': showSidebar, 'sidebar-collapsed': showSidebar && collapsed }">
    <router-view />
  </div>
  <ProfileDialog v-model="profileVisible" :username="username" :user-id="userId" @updated="onProfileUpdated" />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Sidebar from '@/components/Sidebar.vue'
import ProfileDialog from '@/components/ProfileDialog.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const collapsed = ref(false)
const profileVisible = ref(false)

const showSidebar = computed(() => route.meta.guest !== true)
const isAdmin = computed(() => auth.isAdmin)
const username = computed(() => auth.username)
const displayName = computed(() => auth.name?.trim() || auth.username)
const userId = computed(() => auth.user_id || '')

function openProfile() {
  profileVisible.value = true
}

function onProfileUpdated() {
  // The dialog already updates the auth store.
}

function handleLogout() {
  auth.logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.app-main {
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}
.has-sidebar {
  margin-left: 280px;
}
.sidebar-collapsed.has-sidebar {
  margin-left: 64px;
}
</style>
