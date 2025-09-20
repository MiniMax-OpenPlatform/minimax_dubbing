import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../utils/api'
import axios from 'axios'

interface LoginCredentials {
  username: string
  group_id: string
  api_key: string
}

interface RegisterCredentials extends LoginCredentials {
}

interface UserInfo {
  id: number
  username: string
  group_id: string
  created_at: string
  last_login: string
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<UserInfo | null>(null)
  const username = ref(localStorage.getItem('username') || '')
  const group_id = ref(localStorage.getItem('group_id') || '')
  const api_key = ref(localStorage.getItem('api_key') || '')

  // 计算属性
  const isAuthenticated = computed(() => {
    return !!(username.value && group_id.value && api_key.value)
  })

  // 设置认证头
  const setAuthHeaders = () => {
    if (isAuthenticated.value) {
      axios.defaults.headers.common['X-Username'] = username.value
      axios.defaults.headers.common['X-Group-ID'] = group_id.value
      axios.defaults.headers.common['X-API-Key'] = api_key.value
    } else {
      delete axios.defaults.headers.common['X-Username']
      delete axios.defaults.headers.common['X-Group-ID']
      delete axios.defaults.headers.common['X-API-Key']
    }
  }

  // 登录
  const login = async (credentials: LoginCredentials) => {
    try {
      // 设置临时认证头进行测试
      const tempHeaders = {
        'X-Username': credentials.username,
        'X-Group-ID': credentials.group_id,
        'X-API-Key': credentials.api_key
      }

      // 测试认证是否有效
      const response = await api.get('/auth/test-auth/', {
        headers: tempHeaders
      })

      if (response.data.authenticated) {
        // 认证成功，保存凭据
        username.value = credentials.username
        group_id.value = credentials.group_id
        api_key.value = credentials.api_key

        localStorage.setItem('username', credentials.username)
        localStorage.setItem('group_id', credentials.group_id)
        localStorage.setItem('api_key', credentials.api_key)

        user.value = response.data.user

        // 认证头由api拦截器自动设置

        return response.data
      } else {
        throw new Error('认证失败')
      }
    } catch (error: any) {
      // 认证失败，清除可能的残留数据
      logout()
      throw error
    }
  }

  // 注册
  const register = async (credentials: RegisterCredentials) => {
    try {
      const response = await api.post('/auth/register/', credentials)
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 登出
  const logout = () => {
    user.value = null
    username.value = ''
    group_id.value = ''
    api_key.value = ''

    localStorage.removeItem('username')
    localStorage.removeItem('group_id')
    localStorage.removeItem('api_key')

    // 认证头由api拦截器自动清除
  }

  // 检查认证状态
  const checkAuth = async () => {
    if (!isAuthenticated.value) {
      return false
    }

    try {
      // 认证头由api拦截器自动设置
      const response = await api.get('/auth/test-auth/')

      if (response.data.authenticated) {
        user.value = response.data.user
        return true
      } else {
        logout()
        return false
      }
    } catch (error) {
      logout()
      return false
    }
  }

  // 更新API Key
  const updateApiKey = async (newApiKey: string) => {
    const oldApiKey = api_key.value

    try {
      // 临时更新API Key
      api_key.value = newApiKey
      localStorage.setItem('api_key', newApiKey)
      // 认证头由api拦截器自动更新

      // 测试新的API Key是否有效
      const response = await api.get('/auth/test-auth/')

      if (response.data.authenticated) {
        user.value = response.data.user
        return true
      } else {
        // 恢复旧的API Key
        api_key.value = oldApiKey
        localStorage.setItem('api_key', oldApiKey)
        // 认证头由api拦截器自动恢复
        throw new Error('新的API Key无效')
      }
    } catch (error) {
      // 恢复旧的API Key
      api_key.value = oldApiKey
      localStorage.setItem('api_key', oldApiKey)
      // 认证头由api拦截器自动恢复
      throw error
    }
  }

  // 认证头由api拦截器自动管理

  return {
    // 状态
    user,
    username,
    group_id,
    api_key,
    isAuthenticated,

    // 方法
    login,
    register,
    logout,
    checkAuth,
    updateApiKey
  }
})