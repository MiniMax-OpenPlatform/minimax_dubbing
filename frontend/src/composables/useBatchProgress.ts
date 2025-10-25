/**
 * 批量操作进度管理composable
 * 支持翻译、TTS、人声分离和ASR识别四种批量操作的进度跟踪
 */
import { ref, computed, reactive } from 'vue'

export interface BatchProgress {
  id: string
  type: 'translate' | 'tts' | 'vocal_separation' | 'asr' | 'asr'
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error' | 'cancelled'
  total: number
  completed: number
  failed: number
  currentItem?: string // 当前处理的项目描述
  startTime?: number
  estimatedTimeRemaining?: number // 秒
  speed?: number // 项目/分钟
  errorMessages: string[]
  canCancel: boolean
  canPause: boolean
}

export interface BatchProgressState {
  translate: BatchProgress
  tts: BatchProgress
  vocal_separation: BatchProgress
  asr: BatchProgress
}

export function useBatchProgress() {
  // 进度状态
  const progressState = reactive<BatchProgressState>({
    translate: {
      id: 'batch-translate',
      type: 'translate',
      status: 'idle',
      total: 0,
      completed: 0,
      failed: 0,
      errorMessages: [],
      canCancel: true,
      canPause: true
    },
    tts: {
      id: 'batch-tts',
      type: 'tts',
      status: 'idle',
      total: 0,
      completed: 0,
      failed: 0,
      errorMessages: [],
      canCancel: true,
      canPause: true
    },
    vocal_separation: {
      id: 'vocal-separation',
      type: 'vocal_separation',
      status: 'idle',
      total: 100, // 人声分离使用百分比进度
      completed: 0,
      failed: 0,
      errorMessages: [],
      canCancel: false, // 人声分离不可取消
      canPause: false    // 人声分离不可暂停
    },
    asr: {
      id: 'asr-recognize',
      type: 'asr',
      status: 'idle',
      total: 100, // ASR识别使用百分比进度
      completed: 0,
      failed: 0,
      errorMessages: [],
      canCancel: false, // ASR识别不可取消
      canPause: false    // ASR识别不可暂停
    }
  })

  // 是否有活跃的进度（包括已完成但需要显示的）
  const hasActiveProgress = computed(() => {
    return Object.values(progressState).some(progress =>
      ['running', 'paused', 'completed', 'error', 'cancelled'].includes(progress.status)
    )
  })

  // 获取活跃的进度列表（包括已完成但需要显示的）
  const activeProgresses = computed(() => {
    return Object.values(progressState).filter(progress =>
      ['running', 'paused', 'completed', 'error', 'cancelled'].includes(progress.status)
    )
  })

  // 开始批量操作
  const startBatchOperation = (
    type: 'translate' | 'tts' | 'vocal_separation' | 'asr' | 'asr',
    total: number,
    options?: {
      canCancel?: boolean
      canPause?: boolean
    }
  ) => {
    const progress = progressState[type]

    // 清除之前的状态（当开始新任务时，隐藏之前的完成状态）
    progress.status = 'running'
    progress.total = total
    progress.completed = 0
    progress.failed = 0
    progress.startTime = Date.now()
    progress.errorMessages = []
    progress.currentItem = undefined
    progress.estimatedTimeRemaining = undefined
    progress.speed = undefined
    progress.canCancel = options?.canCancel ?? true
    progress.canPause = options?.canPause ?? true

    console.log(`[BatchProgress] Started ${type} operation with ${total} items`)
  }

  // 更新进度
  const updateProgress = (
    type: 'translate' | 'tts' | 'vocal_separation' | 'asr',
    completed: number,
    options?: {
      failed?: number
      currentItem?: string
      addError?: string
    }
  ) => {
    const progress = progressState[type]

    if (progress.status !== 'running') return

    progress.completed = completed
    if (options?.failed !== undefined) {
      progress.failed = options.failed
    }
    if (options?.currentItem) {
      progress.currentItem = options.currentItem
    }
    if (options?.addError) {
      progress.errorMessages.push(options.addError)
    }

    // 计算预计剩余时间和速度
    if (progress.startTime && completed > 0) {
      const elapsed = (Date.now() - progress.startTime) / 1000 / 60 // 分钟
      progress.speed = completed / elapsed // 项目/分钟

      const remaining = progress.total - completed
      if (progress.speed > 0) {
        progress.estimatedTimeRemaining = (remaining / progress.speed) * 60 // 转为秒
      }
    }

    // 检查是否完成
    if (completed >= progress.total) {
      completeBatchOperation(type)
    }
  }

  // 完成批量操作
  const completeBatchOperation = (type: 'translate' | 'tts' | 'vocal_separation' | 'asr') => {
    const progress = progressState[type]
    progress.status = 'completed'
    progress.currentItem = undefined

    console.log(`[BatchProgress] Completed ${type} operation: ${progress.completed}/${progress.total}, failed: ${progress.failed}`)
  }

  // 取消批量操作
  const cancelBatchOperation = (type: 'translate' | 'tts' | 'vocal_separation' | 'asr') => {
    const progress = progressState[type]
    if (!progress.canCancel) return false

    progress.status = 'cancelled'
    progress.currentItem = undefined

    console.log(`[BatchProgress] Cancelled ${type} operation`)
    return true
  }

  // 暂停/恢复批量操作
  const togglePauseBatchOperation = (type: 'translate' | 'tts' | 'vocal_separation' | 'asr') => {
    const progress = progressState[type]
    if (!progress.canPause) return false

    if (progress.status === 'running') {
      progress.status = 'paused'
      console.log(`[BatchProgress] Paused ${type} operation`)
    } else if (progress.status === 'paused') {
      progress.status = 'running'
      console.log(`[BatchProgress] Resumed ${type} operation`)
    }

    return true
  }

  // 设置错误状态
  const setErrorState = (type: 'translate' | 'tts' | 'vocal_separation' | 'asr', error: string) => {
    const progress = progressState[type]
    progress.status = 'error'
    progress.errorMessages.push(error)
    progress.currentItem = undefined

    console.error(`[BatchProgress] Error in ${type} operation:`, error)
  }

  // 关闭进度显示（手动隐藏已完成的任务）
  const dismissProgress = (type: 'translate' | 'tts' | 'vocal_separation' | 'asr') => {
    const progress = progressState[type]
    if (['completed', 'error', 'cancelled'].includes(progress.status)) {
      progress.status = 'idle'
      progress.total = (type === 'vocal_separation' || type === 'asr') ? 100 : 0
      progress.completed = 0
      progress.failed = 0
      progress.currentItem = undefined
      progress.startTime = undefined
      progress.estimatedTimeRemaining = undefined
      progress.speed = undefined
      progress.errorMessages = []

      console.log(`[BatchProgress] Dismissed ${type} progress display`)
    }
  }

  // 重置进度
  const resetProgress = (type?: 'translate' | 'tts' | 'vocal_separation' | 'asr') => {
    const types = type ? [type] : ['translate', 'tts', 'vocal_separation', 'asr'] as const

    types.forEach(t => {
      const progress = progressState[t]
      progress.status = 'idle'
      progress.total = (t === 'vocal_separation' || t === 'asr') ? 100 : 0
      progress.completed = 0
      progress.failed = 0
      progress.currentItem = undefined
      progress.startTime = undefined
      progress.estimatedTimeRemaining = undefined
      progress.speed = undefined
      progress.errorMessages = []
    })
  }

  // 获取进度百分比
  const getProgressPercentage = (type: 'translate' | 'tts' | 'vocal_separation' | 'asr') => {
    const progress = progressState[type]
    if (progress.total === 0) return 0
    return Math.round((progress.completed / progress.total) * 100)
  }

  // 格式化时间
  const formatTime = (seconds?: number) => {
    if (!seconds || seconds <= 0) return ''

    if (seconds < 60) {
      return `${Math.round(seconds)}秒`
    } else if (seconds < 3600) {
      const minutes = Math.round(seconds / 60)
      return `${minutes}分钟`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.round((seconds % 3600) / 60)
      return `${hours}小时${minutes}分钟`
    }
  }

  // 获取状态显示文本
  const getStatusText = (type: 'translate' | 'tts' | 'vocal_separation' | 'asr') => {
    const progress = progressState[type]
    let typeName = '操作'
    if (type === 'translate') typeName = '翻译'
    else if (type === 'tts') typeName = 'TTS'
    else if (type === 'vocal_separation') typeName = '人声分离'
    else if (type === 'asr') typeName = 'ASR识别'

    switch (progress.status) {
      case 'idle':
        return '未开始'
      case 'running':
        return `正在${typeName}...`
      case 'paused':
        return '已暂停'
      case 'completed':
        return '已完成'
      case 'error':
        return '出现错误'
      case 'cancelled':
        return '已取消'
      default:
        return '未知状态'
    }
  }

  return {
    // 状态
    progressState,
    hasActiveProgress,
    activeProgresses,

    // 操作方法
    startBatchOperation,
    updateProgress,
    completeBatchOperation,
    cancelBatchOperation,
    togglePauseBatchOperation,
    setErrorState,
    dismissProgress,
    resetProgress,

    // 工具方法
    getProgressPercentage,
    formatTime,
    getStatusText
  }
}

export type UseBatchProgress = ReturnType<typeof useBatchProgress>