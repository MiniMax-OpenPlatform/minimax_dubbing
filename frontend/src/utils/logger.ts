import { ref } from 'vue'

export interface LogEntry {
  id: number
  timestamp: string
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
  module?: string
}

const logs = ref<LogEntry[]>([])
let logCounter = 0

export const useLogger = () => {
  const addLog = (level: LogEntry['level'], message: string, module?: string) => {
    logCounter++
    const newLog: LogEntry = {
      id: logCounter,
      timestamp: new Date().toLocaleString(),
      level,
      message,
      module
    }

    logs.value.unshift(newLog)

    // 只保留最近100条日志
    if (logs.value.length > 100) {
      logs.value = logs.value.slice(0, 100)
    }

    // 在控制台也输出日志
    const logMethod = level === 'error' ? 'error' : level === 'warning' ? 'warn' : 'log'
    console[logMethod](`[${level.toUpperCase()}] ${module ? `[${module}] ` : ''}${message}`)
  }

  const clearLogs = () => {
    logs.value = []
    addLog('info', '清空日志记录', 'Logger')
  }

  const getLogs = () => logs.value

  return {
    logs,
    addLog,
    clearLogs,
    getLogs
  }
}

// 导出单例实例
export const logger = useLogger()