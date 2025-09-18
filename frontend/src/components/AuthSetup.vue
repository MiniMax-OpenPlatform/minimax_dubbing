<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const emit = defineEmits<{
  authenticated: []
}>()

const authForm = ref({
  group_id: '',
  api_key: ''
})

const isAuthenticated = ref(false)

const saveAuth = () => {
  if (!authForm.value.group_id || !authForm.value.api_key) {
    ElMessage.error('请填写完整的认证信息')
    return
  }

  localStorage.setItem('group_id', authForm.value.group_id)
  localStorage.setItem('api_key', authForm.value.api_key)

  testAuth()
}

const testAuth = async () => {
  try {
    await api.post('/auth/test-auth/', {
      group_id: authForm.value.group_id,
      api_key: authForm.value.api_key
    })
    ElMessage.success('认证成功')
    isAuthenticated.value = true
    emit('authenticated')
  } catch (error) {
    ElMessage.error('认证失败，请检查API密钥')
    isAuthenticated.value = false
  }
}

const clearAuth = () => {
  localStorage.removeItem('group_id')
  localStorage.removeItem('api_key')
  authForm.value.group_id = ''
  authForm.value.api_key = ''
  isAuthenticated.value = false
  ElMessage.info('认证信息已清除')
}

onMounted(() => {
  // 尝试从localStorage加载认证信息
  const storedGroupId = localStorage.getItem('group_id')
  const storedApiKey = localStorage.getItem('api_key')

  if (storedGroupId && storedApiKey) {
    authForm.value.group_id = storedGroupId
    authForm.value.api_key = storedApiKey
    testAuth()
  }
})
</script>

<template>
  <el-card style="max-width: 600px; margin: 50px auto;">
    <template #header>
      <div class="card-header">
        <span>MiniMax API 认证设置</span>
        <el-tag v-if="isAuthenticated" type="success">已认证</el-tag>
        <el-tag v-else type="danger">未认证</el-tag>
      </div>
    </template>

    <el-form :model="authForm" label-width="100px">
      <el-form-item label="Group ID">
        <el-input
          v-model="authForm.group_id"
          placeholder="请输入Group ID"
          :disabled="isAuthenticated"
        />
      </el-form-item>

      <el-form-item label="API Key">
        <el-input
          v-model="authForm.api_key"
          type="textarea"
          :rows="4"
          placeholder="请输入API Key"
          :disabled="isAuthenticated"
        />
      </el-form-item>

      <el-form-item>
        <el-button v-if="!isAuthenticated" type="primary" @click="saveAuth">
          保存并测试
        </el-button>
        <el-button v-else type="success" @click="emit('authenticated')">
          进入应用
        </el-button>
        <el-button v-if="isAuthenticated" @click="clearAuth">
          重新设置
        </el-button>
      </el-form-item>
    </el-form>

    <el-alert
      title="说明"
      type="info"
      :closable="false"
      style="margin-top: 20px;"
    >
      <template #default>
        <p>请输入您的MiniMax API认证信息：</p>
        <ul>
          <li>Group ID: 您的MiniMax账户组ID</li>
          <li>API Key: 您的MiniMax API访问密钥</li>
        </ul>
        <p>认证信息将保存在浏览器本地存储中，仅用于API调用。</p>
      </template>
    </el-alert>
  </el-card>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>