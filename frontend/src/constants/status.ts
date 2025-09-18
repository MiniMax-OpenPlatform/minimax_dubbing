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

// API相关常量
export const API_BASE_URL = 'http://10.11.17.19:5172/api'

// UI相关常量
export const UPLOAD_FILE_SIZE_LIMIT = 1 * 1024 * 1024 // 1MB
export const LOG_MAX_COUNT = 100