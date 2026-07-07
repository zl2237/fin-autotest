<template>
  <el-dialog v-model="visible" title="修改个人信息" width="460px" :close-on-click-modal="false" @update:model-value="onVisibilityChange">
    <el-form :model="form" label-width="100px">
      <el-form-item label="账号">
        <el-input :model-value="username" disabled />
      </el-form-item>
      <el-form-item label="姓名" required>
        <el-input v-model="form.name" placeholder="请输入姓名" />
      </el-form-item>
      <el-form-item label="手机号" required>
        <el-input v-model="form.phone" placeholder="请输入手机号" @blur="checkPhone" @change="checkPhone">
          <template #append>
            <el-button :loading="pending" @click="checkPhone">
              {{ pending ? '校验中' : result === 'taken' ? '已存在' : result === 'ok' ? '可用' : '校验' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="form.email" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="form.password" type="password" show-password placeholder="留空不修改" />
      </el-form-item>
      <el-form-item label="确认密码">
        <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :loading="loading" :disabled="!canSubmit" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  modelValue: boolean
  username: string
  userId?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'updated'): void
}>()

const auth = useAuthStore()

const visible = ref(props.modelValue)
const loading = ref(false)
const pending = ref(false)
const result = ref<'ok' | 'taken' | 'pending' | null>(null)
const form = reactive({ name: '', phone: '', email: '', password: '', confirmPassword: '' })

watch(() => props.modelValue, value => {
  visible.value = value
  if (value) {
    loadUser()
  }
})

watch(visible, value => emit('update:modelValue', value))

function onVisibilityChange(value: boolean) {
  visible.value = value
}

async function loadUser() {
  loading.value = true
  try {
    const { data } = await request.get('/auth/me')
    const user = data?.user
    if (!user) throw new Error(data?.message || '获取用户信息失败')
    Object.assign(form, {
      name: user.name || '',
      phone: user.phone || '',
      email: user.email || '',
      password: '',
      confirmPassword: '',
    })
    result.value = null
  } catch (e: any) {
    ElMessage.error(e?.message || '获取用户信息失败')
    close()
  } finally {
    loading.value = false
  }
}

async function checkPhone() {
  const phone = form.phone.trim()
  if (!phone) {
    result.value = null
    return
  }
  pending.value = true
  try {
    const { data } = await request.get('/auth/check-phone', { params: { phone, exclude_user_id: props.userId ? Number(props.userId) : undefined } })
    result.value = data?.taken ? 'taken' : 'ok'
  } catch {
    result.value = null
  } finally {
    pending.value = false
  }
}

const canSubmit = computed(() => {
  const nameOk = form.name.trim().length > 0
  const phoneOk = form.phone.trim().length > 0 && /^\+?\d{6,15}$/.test(form.phone.trim())
  const passwordOk = !form.password || form.password === form.confirmPassword
  return nameOk && phoneOk && passwordOk && result.value !== 'taken'
})

async function submit() {
  if (form.password && form.password !== form.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  if (result.value === 'taken') {
    ElMessage.error('手机号已存在，请更换')
    return
  }
  loading.value = true
  try {
    const payload: any = {
      name: form.name.trim(),
      phone: form.phone.trim(),
      email: form.email.trim(),
    }
    if (form.password.trim()) {
      payload.password = form.password.trim()
    }
    const { data } = await request.put('/auth/me', payload)
    if (!data?.ok) {
      throw new Error(data?.message || '更新失败')
    }
    const user = data?.user || {}
    auth.login(auth.username, auth.token, auth.role, user.name, user.phone, user.email, user.user_id)
    ElMessage.success('个人信息已更新')
    emit('updated')
    close()
  } catch (e: any) {
    ElMessage.error(e?.message || '更新失败')
  } finally {
    loading.value = false
  }
}

function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.code-block {
  background: #1a1a2e;
  color: #c9d1d9;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  margin: 8px 0;
}
</style>
