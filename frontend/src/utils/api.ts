import axios from 'axios'
import { ElMessage } from 'element-plus'

// 动态获取API基础URL
const getApiBaseUrl = () => {
  // 方案1: 优先使用构建时环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  // 方案2: 运行时环境变量（通过 window 对象注入）
  // 使用方式：在 index.html 中添加 <script>window.API_BASE_URL='https://domain.com:5172/api'</script>
  if ((window as any).API_BASE_URL) {
    return (window as any).API_BASE_URL
  }

  // 方案3: 自动检测
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  const currentPort = window.location.port

  // 本地开发环境：直连后端 5172 端口
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}:5172/api`
  }

  // 生产环境策略：
  // 如果访问地址有非标准端口（如 :5173），说明直接访问容器，使用容器内 nginx 代理
  // 如果是标准端口（无端口号，即 80/443），说明通过外部反向代理，直接访问后端 5172
  if (currentPort && currentPort !== '80' && currentPort !== '443') {
    // 有自定义端口（如 5173），通过当前端口访问，由容器内 nginx 代理到 5172
    return `${protocol}//${hostname}:${currentPort}/api`
  } else {
    // 无端口或标准端口，直接访问后端 5172 端口（适用于外部反向代理未配置 /api 的场景）
    return `${protocol}//${hostname}:5172/api`
  }
}

// 创建axios实例
const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 300000, // 5分钟超时，适配LLM长时间调用（尤其是大量段落的说话人分配）
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