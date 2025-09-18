import { ref } from 'vue'

export interface LogEntry {
  id: number
  timestamp: string
  level: 'info' | 'success' | 'warning' | 'error' | 'debug'
  message: string
  module?: string
  traceId?: string
  userId?: string
  projectId?: number
  segmentId?: number
  duration?: number
  metadata?: Record<string, any>
}

export interface TraceSession {
  traceId: string
  startTime: number
  operation: string
  metadata?: Record<string, any>
}

const logs = ref<LogEntry[]>([])
const traceSessions = ref<Map<string, TraceSession>>(new Map())
let logCounter = 0

// 生成trace ID
const generateTraceId = (): string => {
  return `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// 获取当前用户ID（从localStorage）
const getCurrentUserId = (): string | undefined => {
  return localStorage.getItem('group_id') || undefined
}

export const useLogger = () => {
  const addLog = (
    level: LogEntry['level'],
    message: string,
    module?: string,
    options?: {
      traceId?: string
      projectId?: number
      segmentId?: number
      duration?: number
      metadata?: Record<string, any>
    }
  ) => {
    logCounter++
    const now = new Date()
    const newLog: LogEntry = {
      id: logCounter,
      timestamp: now.toLocaleString(),
      level,
      message,
      module,
      traceId: options?.traceId,
      userId: getCurrentUserId(),
      projectId: options?.projectId,
      segmentId: options?.segmentId,
      duration: options?.duration,
      metadata: options?.metadata
    }

    logs.value.unshift(newLog)

    // 只保留最近200条日志（增加容量）
    if (logs.value.length > 200) {
      logs.value = logs.value.slice(0, 200)
    }

    // 在控制台也输出日志，包含trace信息
    const logMethod = level === 'error' ? 'error' : level === 'warning' ? 'warn' : 'log'
    const traceInfo = options?.traceId ? `[${options.traceId}] ` : ''
    const moduleInfo = module ? `[${module}] ` : ''
    const projectInfo = options?.projectId ? `[P:${options.projectId}] ` : ''
    const segmentInfo = options?.segmentId ? `[S:${options.segmentId}] ` : ''

    console[logMethod](`[${level.toUpperCase()}] ${traceInfo}${moduleInfo}${projectInfo}${segmentInfo}${message}`)
  }

  // 开始trace会话
  const startTrace = (operation: string, metadata?: Record<string, any>): string => {
    const traceId = generateTraceId()
    const session: TraceSession = {
      traceId,
      startTime: Date.now(),
      operation,
      metadata
    }

    traceSessions.value.set(traceId, session)

    addLog('debug', `开始操作: ${operation}`, 'Trace', {
      traceId,
      metadata: { ...metadata, operation }
    })

    return traceId
  }

  // 结束trace会话
  const endTrace = (traceId: string, result?: 'success' | 'error', message?: string) => {
    const session = traceSessions.value.get(traceId)
    if (session) {
      const duration = Date.now() - session.startTime
      const level = result === 'error' ? 'error' : result === 'success' ? 'success' : 'info'
      const finalMessage = message || `操作完成: ${session.operation}`

      addLog(level, finalMessage, 'Trace', {
        traceId,
        duration,
        metadata: {
          ...session.metadata,
          operation: session.operation,
          result: result || 'completed'
        }
      })

      traceSessions.value.delete(traceId)
    }
  }

  // 添加trace日志（在现有会话中）
  const traceLog = (
    traceId: string,
    level: LogEntry['level'],
    message: string,
    module?: string,
    options?: {
      projectId?: number
      segmentId?: number
      metadata?: Record<string, any>
    }
  ) => {
    addLog(level, message, module, {
      traceId,
      ...options
    })
  }

  // 获取指定trace的所有日志
  const getTraceLog = (traceId: string): LogEntry[] => {
    return logs.value.filter(log => log.traceId === traceId)
  }

  // 获取指定项目的所有日志
  const getProjectLogs = (projectId: number): LogEntry[] => {
    return logs.value.filter(log => log.projectId === projectId)
  }

  // 按模块过滤日志
  const getLogsByModule = (module: string): LogEntry[] => {
    return logs.value.filter(log => log.module === module)
  }

  // 按级别过滤日志
  const getLogsByLevel = (level: LogEntry['level']): LogEntry[] => {
    return logs.value.filter(log => log.level === level)
  }

  const clearLogs = () => {
    logs.value = []
    traceSessions.value.clear()
    addLog('info', '清空日志记录', 'Logger')
  }

  const getLogs = () => logs.value

  // 导出日志为JSON
  const exportLogs = (format: 'json' | 'csv' = 'json') => {
    if (format === 'json') {
      return JSON.stringify(logs.value, null, 2)
    } else {
      // CSV格式
      const headers = ['ID', 'Timestamp', 'Level', 'Module', 'TraceID', 'ProjectID', 'SegmentID', 'Duration', 'Message']
      const csvData = logs.value.map(log => [
        log.id,
        log.timestamp,
        log.level,
        log.module || '',
        log.traceId || '',
        log.projectId || '',
        log.segmentId || '',
        log.duration || '',
        `"${log.message.replace(/"/g, '""')}"`
      ])

      return [headers.join(','), ...csvData.map(row => row.join(','))].join('\n')
    }
  }

  return {
    logs,
    traceSessions,
    addLog,
    startTrace,
    endTrace,
    traceLog,
    getTraceLog,
    getProjectLogs,
    getLogsByModule,
    getLogsByLevel,
    clearLogs,
    getLogs,
    exportLogs,
    generateTraceId
  }
}

// 导出单例实例
export const logger = useLogger()