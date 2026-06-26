import { defineStore } from 'pinia'
import { reactive } from 'vue'

const STORAGE_KEY = 'platform_form_config'

const DEFAULTS = {
  base_url: 'https://fin-tidb.21eflag.com/',
  login_url: '/api/home/login/userLogin',
  test_username: '',
  test_password: '',
  token_field: 'data.token',
  token_type: '',
  auth_header: 'Authorization',
  marker: '',
  order_prefix: 'lele',
  loop_count: 1,
}

function readSaved(): Record<string, any> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    return JSON.parse(raw)
  } catch {
    return {}
  }
}

export const useFormStore = defineStore('form', () => {
  const data = reactive<Record<string, any>>({ ...DEFAULTS, ...readSaved() })

  function patch(values: Record<string, any>) {
    Object.assign(data, values)
    save()
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  function reset() {
    Object.assign(data, { ...DEFAULTS })
    localStorage.removeItem(STORAGE_KEY)
  }

  return { data, patch, save, reset }
})
