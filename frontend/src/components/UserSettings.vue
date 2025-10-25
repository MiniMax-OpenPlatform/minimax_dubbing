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

    <el-card class="setting-card">
      <template #header>
        <div class="card-header">
          <span>阿里云api_key</span>
        </div>
      </template>

      <el-form :model="aliyunForm" :rules="aliyunRules" ref="aliyunFormRef" label-width="200px">
        <el-form-item label="DashScope API Key" prop="dashscopeApiKey">
          <el-input
            v-model="aliyunForm.dashscopeApiKey"
            type="password"
            show-password
            placeholder="输入 DashScope API Key（格式：sk-xxx）"
            clearable
          />
          <template #extra>
            <el-link
              href="https://dashscope.console.aliyun.com/apiKey"
              target="_blank"
              type="primary"
              :underline="false"
              style="font-size: 12px;"
            >
              前往阿里云百炼控制台获取 API Key
            </el-link>
          </template>
        </el-form-item>

        <el-form-item label="AccessKey ID" prop="accessKeyId">
          <el-input
            v-model="aliyunForm.accessKeyId"
            placeholder="输入阿里云 AccessKey ID（需授权 AliyunNLSFullAccess）"
            clearable
          />
        </el-form-item>

        <el-form-item label="AccessKey Secret" prop="accessKeySecret">
          <el-input
            v-model="aliyunForm.accessKeySecret"
            type="password"
            show-password
            placeholder="输入阿里云 AccessKey Secret"
            clearable
          />
        </el-form-item>

        <el-form-item label="APP KEY（智能语音NLS应用Key）" prop="appKey">
          <el-input
            v-model="aliyunForm.appKey"
            placeholder="输入智能语音 NLS 应用 Key"
            clearable
          />
          <template #extra>
            <el-link
              href="https://nls-portal.console.aliyun.com/applist"
              target="_blank"
              type="primary"
              :underline="false"
              style="font-size: 12px;"
            >
              前往阿里云智能语音控制台获取 APP KEY
            </el-link>
          </template>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="updateAliyunConfig"
            :loading="updatingAliyun"
          >
            保存阿里云配置
          </el-button>
          <el-button @click="resetAliyunForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="setting-card">
      <el-button type="danger" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        退出登录
      </el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import api from '../utils/api'

const authStore = useAuthStore()

const emit = defineEmits<{
  logout: []
}>()

const apiFormRef = ref<FormInstance>()
const aliyunFormRef = ref<FormInstance>()
const updating = ref(false)
const updatingAliyun = ref(false)

const apiForm = reactive({
  newApiKey: ''
})

const aliyunForm = reactive({
  dashscopeApiKey: '',
  accessKeyId: '',
  accessKeySecret: '',
  appKey: ''
})

const apiRules = {
  newApiKey: [
    { min: 10, message: 'API Key长度至少10个字符', trigger: 'blur' }
  ]
}

const aliyunRules = {
  dashscopeApiKey: [
    { pattern: /^sk-[a-zA-Z0-9]+$/, message: 'API Key 格式应为 sk-xxx', trigger: 'blur' }
  ],
  accessKeyId: [],
  accessKeySecret: [],
  appKey: []
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

// 加载阿里云配置
const loadAliyunConfig = async () => {
  try {
    const response = await api.get('/auth/config/')
    if (response.data) {
      const config = response.data
      aliyunForm.dashscopeApiKey = config.dashscope_api_key || ''
      aliyunForm.accessKeyId = config.aliyun_access_key_id || ''
      aliyunForm.accessKeySecret = config.aliyun_access_key_secret || ''
      aliyunForm.appKey = config.aliyun_app_key || ''
    }
  } catch (error: any) {
    console.error('加载阿里云配置失败', error)
  }
}

// 更新阿里云配置
const updateAliyunConfig = async () => {
  if (!aliyunFormRef.value) return

  try {
    await aliyunFormRef.value.validate()
    updatingAliyun.value = true

    await api.patch('/auth/config/', {
      dashscope_api_key: aliyunForm.dashscopeApiKey,
      aliyun_access_key_id: aliyunForm.accessKeyId,
      aliyun_access_key_secret: aliyunForm.accessKeySecret,
      aliyun_app_key: aliyunForm.appKey
    })

    ElMessage.success('阿里云配置保存成功')
  } catch (error: any) {
    console.error('阿里云配置保存失败:', error)
    console.error('错误响应:', error?.response)

    let errorMsg = '配置保存失败'

    if (error?.response?.data) {
      const data = error.response.data
      errorMsg = data.message || data.error || data.detail || JSON.stringify(data)
    } else if (error?.message) {
      errorMsg = error.message
    }

    ElMessage.error(errorMsg)
  } finally {
    updatingAliyun.value = false
  }
}

// 重置阿里云表单
const resetAliyunForm = () => {
  aliyunFormRef.value?.resetFields()
  loadAliyunConfig()
}

// 页面加载时获取配置
onMounted(() => {
  loadAliyunConfig()
})
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