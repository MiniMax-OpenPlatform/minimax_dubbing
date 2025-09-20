<template>
  <div class="login-container">
    <div class="login-form">
      <h2>用户登录</h2>
      <el-form
        :model="loginForm"
        :rules="rules"
        ref="loginFormRef"
        label-width="100px"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
          />
        </el-form-item>

        <el-form-item label="企业 Group ID" prop="group_id">
          <el-input
            v-model="loginForm.group_id"
            placeholder="请输入企业 Group ID"
          />
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="loginForm.api_key"
            type="password"
            placeholder="请输入 API Key"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-button
            type="text"
            @click="showRegister = true"
            style="width: 100%"
          >
            还没有账号？立即注册
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 注册对话框 -->
    <el-dialog
      v-model="showRegister"
      title="用户注册 - 无需密码"
      width="400px"
    >
      <el-alert
        title="注册说明：系统将验证您的Group ID和API Key是否能正常访问MiniMax服务"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      />
      <el-form
        :model="registerForm"
        :rules="registerRules"
        ref="registerFormRef"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
          />
        </el-form-item>

        <el-form-item label="企业 Group ID" prop="group_id">
          <el-input
            v-model="registerForm.group_id"
            placeholder="请输入企业 Group ID"
          />
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="registerForm.api_key"
            type="password"
            placeholder="请输入 API Key"
            show-password
          />
        </el-form-item>

      </el-form>

      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button
          type="primary"
          :loading="registerLoading"
          @click="handleRegister"
        >
          注册
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const emit = defineEmits<{
  loginSuccess: []
}>()

const loading = ref(false)
const registerLoading = ref(false)
const showRegister = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  group_id: '',
  api_key: ''
})

const registerForm = reactive({
  username: '',
  group_id: '',
  api_key: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  group_id: [
    { required: true, message: '请输入企业 Group ID', trigger: 'blur' }
  ],
  api_key: [
    { required: true, message: '请输入 API Key', trigger: 'blur' }
  ]
}

const registerRules = {
  ...rules
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true

    await authStore.login(loginForm)
    ElMessage.success('登录成功')
    emit('loginSuccess')
  } catch (error: any) {
    if (error?.response?.status === 401) {
      ElMessage.error('用户名、Group ID 或 API Key 错误')
    } else if (error.fields) {
      // 表单验证错误
      return
    } else {
      ElMessage.error('登录失败：' + (error.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()
    registerLoading.value = true

    await authStore.register(registerForm)
    ElMessage.success('注册成功，请使用新账号登录')
    showRegister.value = false

    // 清空注册表单
    Object.assign(registerForm, {
      username: '',
      group_id: '',
      api_key: ''
    })
  } catch (error: any) {
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error.fields) {
      // 表单验证错误
      return
    } else {
      ElMessage.error('注册失败：' + (error.message || '未知错误'))
    }
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-form {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 400px;
}

.login-form h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}
</style>