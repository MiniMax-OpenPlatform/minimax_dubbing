<template>
  <div class="user-settings">
    <div class="settings-header">
      <h2>账户设置</h2>
      <p>管理您的账户信息和API配置</p>
    </div>

    <el-card class="setting-card">
      <template #header>
        <div class="card-header">
          <span>基本信息</span>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">
          {{ authStore.username }}
        </el-descriptions-item>
        <el-descriptions-item label="企业 Group ID">
          {{ authStore.group_id }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" v-if="authStore.user?.created_at">
          {{ formatDate(authStore.user.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="最后登录" v-if="authStore.user?.last_login">
          {{ formatDate(authStore.user.last_login) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="setting-card">
      <template #header>
        <div class="card-header">
          <span>API 配置</span>
        </div>
      </template>

      <el-form :model="apiForm" :rules="apiRules" ref="apiFormRef" label-width="120px">
        <el-form-item label="当前 API Key">
          <el-input
            v-model="displayApiKey"
            readonly
            type="password"
            show-password
            placeholder="当前API Key"
          />
        </el-form-item>

        <el-form-item label="新 API Key" prop="newApiKey">
          <el-input
            v-model="apiForm.newApiKey"
            type="password"
            show-password
            placeholder="输入新的API Key（如需更新）"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="updateApiKey"
            :loading="updating"
            :disabled="!apiForm.newApiKey"
          >
            更新 API Key
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="setting-card danger-zone">
      <template #header>
        <div class="card-header">
          <span>危险操作</span>
        </div>
      </template>

      <el-alert
        title="注意：退出登录后需要重新输入认证信息"
        type="warning"
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <el-button type="danger" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        退出登录
      </el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const emit = defineEmits<{
  logout: []
}>()

const apiFormRef = ref<FormInstance>()
const updating = ref(false)

const apiForm = reactive({
  newApiKey: ''
})

const apiRules = {
  newApiKey: [
    { min: 10, message: 'API Key长度至少10个字符', trigger: 'blur' }
  ]
}

const displayApiKey = computed(() => {
  return authStore.api_key ? authStore.api_key : '未设置'
})

const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateString
  }
}

const updateApiKey = async () => {
  if (!apiFormRef.value) return

  try {
    await apiFormRef.value.validate()
    updating.value = true

    await authStore.updateApiKey(apiForm.newApiKey)
    ElMessage.success('API Key更新成功')
    resetForm()
  } catch (error: any) {
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error.fields) {
      // 表单验证错误
      return
    } else {
      ElMessage.error('API Key更新失败：' + (error.message || '未知错误'))
    }
  } finally {
    updating.value = false
  }
}

const resetForm = () => {
  apiForm.newApiKey = ''
  apiFormRef.value?.clearValidate()
}

const handleLogout = () => {
  emit('logout')
}
</script>

<style scoped>
.user-settings {
  max-width: 800px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: 24px;
}

.settings-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.settings-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.setting-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.danger-zone {
  border-color: #f56c6c;
}

.danger-zone :deep(.el-card__header) {
  background-color: #fef0f0;
  border-bottom-color: #f56c6c;
}

.danger-zone .card-header span {
  color: #f56c6c;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-settings {
    max-width: 100%;
  }

  :deep(.el-descriptions) {
    font-size: 14px;
  }

  :deep(.el-form-item__label) {
    width: 100px !important;
  }
}
</style>