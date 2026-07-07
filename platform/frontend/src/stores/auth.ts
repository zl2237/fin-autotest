import { defineStore } from 'pinia'
import { ref } from 'vue'

const TOKEN_KEY = 'platform_token'
const USERNAME_KEY = 'platform_username'
const ROLE_KEY = 'platform_role'
const NAME_KEY = 'platform_name'
const PHONE_KEY = 'platform_phone'
const EMAIL_KEY = 'platform_email'
const USER_ID_KEY = 'platform_user_id'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const username = ref(localStorage.getItem(USERNAME_KEY) || '')
  const role = ref(localStorage.getItem(ROLE_KEY) || '')
  const name = ref(localStorage.getItem(NAME_KEY) || '')
  const phone = ref(localStorage.getItem(PHONE_KEY) || '')
  const email = ref(localStorage.getItem(EMAIL_KEY) || '')
  const user_id = ref(localStorage.getItem(USER_ID_KEY) || '')

  const isLoggedIn = ref(!!token.value)
  const isAdmin = ref(role.value === 'admin')

  function login(usernameValue: string, t: string, userRole: string, userName: string, userPhone: string, userEmail: string, userId: number | string | null) {
    token.value = t
    username.value = usernameValue
    role.value = userRole
    name.value = userName || ''
    phone.value = userPhone || ''
    email.value = userEmail || ''
    user_id.value = userId != null ? String(userId) : ''
    localStorage.setItem(TOKEN_KEY, t)
    localStorage.setItem(USERNAME_KEY, usernameValue)
    localStorage.setItem(ROLE_KEY, userRole)
    localStorage.setItem(NAME_KEY, userName || '')
    localStorage.setItem(PHONE_KEY, userPhone || '')
    localStorage.setItem(EMAIL_KEY, userEmail || '')
    localStorage.setItem(USER_ID_KEY, userId != null ? String(userId) : '')
    isLoggedIn.value = true
    isAdmin.value = userRole === 'admin'
  }

  function logout() {
    token.value = ''
    username.value = ''
    role.value = ''
    name.value = ''
    phone.value = ''
    email.value = ''
    user_id.value = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USERNAME_KEY)
    localStorage.removeItem(ROLE_KEY)
    localStorage.removeItem(NAME_KEY)
    localStorage.removeItem(PHONE_KEY)
    localStorage.removeItem(EMAIL_KEY)
    localStorage.removeItem(USER_ID_KEY)
    isLoggedIn.value = false
    isAdmin.value = false
  }

  return { token, username, role, name, phone, email, user_id, isLoggedIn, isAdmin, login, logout }
})
