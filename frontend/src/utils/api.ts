import axios from 'axios'
import { ElMessage } from 'element-plus'

// 动态获取API基础URL
const getApiBaseUrl = () => {
  // 优先使用环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  // 自动检测当前域名和端口
  const protocol = window.location.protocol
  const hostname = window.location.hostname

  // 开发环境默认后端端口5172，生产环境使用相同域名
  const port = hostname === 'localhost' || hostname === '127.0.0.1' ? ':5172' : ':5172'

  return `${protocol}//${hostname}${port}/api`
}

// 创建axios实例
const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加三要素认证头
api.interceptors.request.use(
  (config) => {
    // 从localStorage获取用户认证信息
    const username = localStorage.getItem('username')
    const groupId = localStorage.getItem('group_id')
    const apiKey = localStorage.getItem('api_key')

    if (username && groupId && apiKey) {
      config.headers['X-Username'] = username
      config.headers['X-Group-ID'] = groupId
      config.headers['X-API-Key'] = apiKey
    }

    // 对于FormData，确保不设置Content-Type，让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error)

    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 400:
          ElMessage.error(data.error || '请求参数错误')
          break
        case 401:
          ElMessage.error('认证失败，请检查API密钥')
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data.error || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export { api }
export default api