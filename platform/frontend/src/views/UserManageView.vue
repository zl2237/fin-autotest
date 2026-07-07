<template>
  <div class="page">
    <div class="main">
      <div class="user-manage-container">
        <div class="page-header">
          <h1>用户管理</h1>
          <el-button type="primary" @click="openCreateDialog">新增用户</el-button>
        </div>

        <el-card shadow="never">
          <el-table :data="users" stripe style="width: 100%">
            <el-table-column prop="user_id" label="用户ID" width="100" />
            <el-table-column prop="username" label="账号" min-width="160" />
            <el-table-column prop="name" label="姓名" min-width="120" />
            <el-table-column prop="phone" label="手机号" min-width="140" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column prop="role" label="角色" min-width="120">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'warning' : 'info'">
                  {{ row.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="openEditDialog(row)">
                  编辑
                </el-button>
                <el-popconfirm title="确认删除该账号？" @confirm="handleDelete(row.username)">
                  <template #reference>
                    <el-button size="small" type="danger" link :disabled="isCurrentUser(row.username)">
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增用户' : '编辑用户'" width="520px">
          <el-form :model="form" label-width="90px">
            <el-form-item v-if="dialogMode === 'edit'" label="用户ID">
              <el-input :model-value="form.user_id" disabled />
            </el-form-item>
            <el-form-item label="账号" required>
              <el-input v-model="form.username" :disabled="dialogMode === 'edit'" />
            </el-form-item>
            <el-form-item v-if="dialogMode === 'create'" label="密码" required>
              <el-input v-model="form.password" type="password" show-password />
            </el-form-item>
            <el-form-item v-if="dialogMode === 'edit'" label="新密码">
              <el-input v-model="form.password" type="password" show-password placeholder="留空不修改" />
            </el-form-item>
            <el-form-item label="姓名" required>
              <el-input v-model="form.name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="手机号" required>
              <el-input v-model="form.phone" placeholder="请输入手机号" @blur="checkPhone" @change="checkPhone">
                <template #append>
                  <el-button :loading="phoneCheckPending" @click="checkPhone">
                    {{ phoneCheckPending ? '校验中' : phoneCheckResult === 'taken' ? '已存在' : phoneCheckResult === 'ok' ? '可用' : '校验' }}
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="角色" required>
              <el-select v-model="form.role" style="width: 100%">
                <el-option label="管理员" value="admin" />
                <el-option label="普通用户" value="user" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="loading" :disabled="!canSubmit" @click="handleSubmit">
              确定
            </el-button>
          </template>
        </el-dialog>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User as UserIcon } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import request from '@/api/request'
import type { User } from '@/api/users'

const router = useRouter()
const auth = useAuthStore()
const users = ref<User[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const loading = ref(false)
const phoneCheckPending = ref(false)
const phoneCheckResult = ref<'ok' | 'taken' | 'pending' | null>(null)
const form = reactive<{ user_id?: number; username: string; password: string; name: string; phone: string; email: string; role: string }>({
  user_id: undefined,
  username: '',
  password: '',
  name: '',
  phone: '',
  email: '',
  role: 'user',
})

const isCurrentUser = (username: string) => username === auth.username

async function checkPhone() {
  const phone = form.phone.trim()
  if (!phone) {
    phoneCheckResult.value = null
    return
  }
  phoneCheckPending.value = true
  try {
    const { data } = await request.get('/auth/check-phone', { params: { phone, exclude_user_id: form.user_id } })
    phoneCheckResult.value = data?.taken ? 'taken' : 'ok'
  } catch {
    phoneCheckResult.value = null
  } finally {
    phoneCheckPending.value = false
  }
}

const canSubmit = computed(() => {
  const usernameOk = form.username.trim().length > 0
  const passwordOk = dialogMode.value === 'create' ? form.password.trim().length > 0 : true
  const nameOk = form.name.trim().length > 0
  const phoneOk = form.phone.trim().length > 0 && /^\+?\d{6,15}$/.test(form.phone.trim()) && phoneCheckResult.value !== 'taken'
  return usernameOk && passwordOk && nameOk && phoneOk && ['admin', 'user'].includes(form.role)
})

async function loadUsers() {
  try {
    const { data } = await request.get('/users')
    if (!data?.ok) {
      throw new Error(data?.message || '加载失败')
    }
    users.value = (data as any).users || []
  } catch (e: any) {
    ElMessage.error(e?.message || '加载用户失败')
  }
}

function openCreateDialog() {
  dialogMode.value = 'create'
  Object.assign(form, { user_id: undefined, username: '', password: '', name: '', phone: '', email: '', role: 'user' })
  phoneCheckResult.value = null
  dialogVisible.value = true
}

function openEditDialog(user: User) {
  dialogMode.value = 'edit'
  Object.assign(form, {
    user_id: user.user_id,
    username: user.username,
    password: '',
    name: user.name,
    phone: user.phone,
    email: user.email,
    role: user.role,
  })
  phoneCheckResult.value = null
  dialogVisible.value = true
}

async function handleSubmit() {
  if (phoneCheckResult.value === 'taken') {
    ElMessage.error('手机号已存在，请更换')
    return
  }
  loading.value = true
  try {
    if (dialogMode.value === 'create') {
      const { data } = await request.post('/users', {
        username: form.username.trim(),
        password: form.password.trim(),
        role: form.role,
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
      })
      if (!data?.ok) {
        throw new Error(data?.message || '创建失败')
      }
      ElMessage.success('创建成功')
    } else {
      const payload: any = {
        role: form.role,
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
      }
      if (form.password.trim()) {
        payload.password = form.password.trim()
      }
      const { data } = await request.put(`/users/${form.user_id}`, payload)
      if (!data?.ok) {
        throw new Error(data?.message || '更新失败')
      }
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(username: string) {
  const { data } = await request.delete(`/users/${encodeURIComponent(username)}`)
  if (!data?.ok) {
    ElMessage.error(data?.message || '删除失败')
    return
  }
  ElMessage.success('删除成功')
  await loadUsers()
}

function handleLogout() {
  auth.logout()
  router.push({ name: 'Login' })
}

onMounted(loadUsers)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f0f2f5;
}

.main {
  padding: 20px 24px;
  transition: margin-left 0.3s ease;
}
.user-manage-container {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
</style>
