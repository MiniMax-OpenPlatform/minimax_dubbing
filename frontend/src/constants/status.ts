// 状态映射常量
export const PROJECT_STATUS_MAP = {
  'draft': { type: 'info', text: '草稿' },
  'processing': { type: 'warning', text: '处理中' },
  'completed': { type: 'success', text: '已完成' },
  'failed': { type: 'danger', text: '失败' }
} as const

export const SEGMENT_STATUS_MAP = {
  'pending': { type: 'info', text: '待处理' },
  'translating': { type: 'warning', text: '翻译中' },
  'translated': { type: 'success', text: '已翻译' },
  'tts_processing': { type: 'warning', text: 'TTS处理中' },
  'completed': { type: 'success', text: '已完成' },
  'failed': { type: 'danger', text: '失败' },
  'silent': { type: 'info', text: '静音' }
} as const

// API相关常量 - 动态获取基础URL
const getApiBaseUrl = () => {
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  const currentPort = window.location.port

  // 本地开发环境：直连后端 5172 端口
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}:5172/api`
  }

  // 生产环境：API 通过 /dubbing/api/ 访问
  if (currentPort && currentPort !== '80' && currentPort !== '443') {
    return `${protocol}//${hostname}:${currentPort}/dubbing/api`
  } else {
    return `/dubbing/api`
  }
}

export const API_BASE_URL = getApiBaseUrl()

// UI相关常量
export const UPLOAD_FILE_SIZE_LIMIT = 1 * 1024 * 1024 // 1MB
export const LOG_MAX_COUNT = 100