import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

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
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'Login' }
  }
  if (to.meta.guest && auth.isLoggedIn) {
    return { name: 'Home' }
  }
})

export default router
