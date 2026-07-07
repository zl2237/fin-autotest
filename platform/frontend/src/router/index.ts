import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/logistics/link-test',
      name: 'LogisticsLinkTest',
      component: () => import('@/views/LinkTestView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/logistics/document-upload',
      name: 'LogisticsDocumentUpload',
      component: () => import('@/views/PlaceholderView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/logistics/approval-config',
      name: 'LogisticsApprovalConfig',
      component: () => import('@/views/PlaceholderView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/platform/users',
      name: 'PlatformUserManage',
      component: () => import('@/views/UserManageView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('platform_token')
  const role = localStorage.getItem('platform_role')
  const isLoggedIn = !!token
  if (to.meta.requiresAuth && !isLoggedIn) {
    return { name: 'Login' }
  }
  if (to.meta.guest && isLoggedIn) {
    return { name: 'Home' }
  }
  if (to.meta.requiresAdmin && role !== 'admin') {
    return { name: 'Home' }
  }
})

export default router
