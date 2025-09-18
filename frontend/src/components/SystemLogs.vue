<template>
  <div class="system-logs">
    <div class="logs-header">
      <h2>系统日志</h2>
      <div class="header-actions">
        <el-button @click="exportLogs('json')" type="primary" size="small">
          <el-icon><Download /></el-icon>
          导出JSON
        </el-button>
        <el-button @click="exportLogs('csv')" type="primary" size="small">
          <el-icon><Download /></el-icon>
          导出CSV
        </el-button>
        <el-button @click="clearLogs" type="danger" size="small">
          <el-icon><Delete /></el-icon>
          清空日志
        </el-button>
      </div>
    </div>

    <!-- 过滤器 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="levelFilter" placeholder="过滤级别" clearable size="small" style="width: 100%">
            <el-option label="全部" value="" />
            <el-option label="DEBUG" value="debug" />
            <el-option label="INFO" value="info" />
            <el-option label="SUCCESS" value="success" />
            <el-option label="WARNING" value="warning" />
            <el-option label="ERROR" value="error" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="moduleFilter" placeholder="过滤模块" clearable size="small" style="width: 100%">
            <el-option label="全部" value="" />
            <el-option
              v-for="module in moduleOptions"
              :key="module"
              :label="module"
              :value="module"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="traceFilter"
            placeholder="过滤TraceID"
            clearable
            size="small"
            prefix-icon="Search"
          />
        </el-col>
        <el-col :span="6">
          <el-input-number
            v-model="projectFilter"
            placeholder="项目ID"
            clearable
            size="small"
            style="width: 100%"
            :min="1"
          />
        </el-col>
      </el-row>
    </el-card>

    <el-card class="logs-card">
      <el-table
        :data="filteredLogs"
        height="calc(100vh - 420px)"
        stripe
        :border="true"
        style="width: 100%;"
        :table-layout="'auto'"
        :fit="true"
        @row-click="handleRowClick"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column prop="timestamp" label="时间" width="160" show-overflow-tooltip />
        <el-table-column prop="level" label="级别" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getLevelTagType(row.level)"
              size="small"
            >
              {{ row.level.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.module" size="small" type="info">
              {{ row.module }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="traceId" label="TraceID" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.traceId" class="trace-id" @click.stop="filterByTrace(row.traceId)">
              {{ row.traceId.split('_').pop() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="项目/段落" width="100" align="center">
          <template #default="{ row }">
            <div class="project-segment-info">
              <el-tag v-if="row.projectId" size="small" type="warning" style="margin-bottom: 2px;">
                P:{{ row.projectId }}
              </el-tag>
              <el-tag v-if="row.segmentId" size="small" type="success">
                S:{{ row.segmentId }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.duration" class="duration-text">
              {{ formatDuration(row.duration) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
      </el-table>

      <el-empty v-if="filteredLogs.length === 0" description="暂无日志记录" />
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="日志详情" width="70%">
      <div v-if="selectedLog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ selectedLog.id }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ selectedLog.timestamp }}</el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getLevelTagType(selectedLog.level)">
              {{ selectedLog.level.toUpperCase() }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模块">{{ selectedLog.module || '无' }}</el-descriptions-item>
          <el-descriptions-item label="TraceID">{{ selectedLog.traceId || '无' }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ selectedLog.userId || '无' }}</el-descriptions-item>
          <el-descriptions-item label="项目ID">{{ selectedLog.projectId || '无' }}</el-descriptions-item>
          <el-descriptions-item label="段落ID">{{ selectedLog.segmentId || '无' }}</el-descriptions-item>
          <el-descriptions-item label="耗时">
            {{ selectedLog.duration ? formatDuration(selectedLog.duration) : '无' }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">消息内容</el-divider>
        <div class="log-message">{{ selectedLog.message }}</div>

        <el-divider v-if="selectedLog.metadata" content-position="left">元数据</el-divider>
        <pre v-if="selectedLog.metadata" class="metadata-json">{{ JSON.stringify(selectedLog.metadata, null, 2) }}</pre>

        <el-divider v-if="selectedLog.traceId" content-position="left">相关追踪日志</el-divider>
        <el-table v-if="selectedLog.traceId" :data="relatedLogs" size="small">
          <el-table-column prop="timestamp" label="时间" width="160" />
          <el-table-column prop="level" label="级别" width="80">
            <template #default="{ row }">
              <el-tag :type="getLevelTagType(row.level)" size="small">
                {{ row.level.toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="100" />
          <el-table-column prop="message" label="消息" show-overflow-tooltip />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Delete, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { logger, type LogEntry } from '../utils/logger'

const levelFilter = ref('')
const moduleFilter = ref('')
const traceFilter = ref('')
const projectFilter = ref<number | null>(null)
const detailDialogVisible = ref(false)
const selectedLog = ref<LogEntry | null>(null)

const logs = computed(() => logger.logs.value)

const moduleOptions = computed(() => {
  const modules = new Set<string>()
  logs.value.forEach(log => {
    if (log.module) {
      modules.add(log.module)
    }
  })
  return Array.from(modules).sort()
})

const filteredLogs = computed(() => {
  let filtered = logs.value

  if (levelFilter.value) {
    filtered = filtered.filter(log => log.level === levelFilter.value)
  }

  if (moduleFilter.value) {
    filtered = filtered.filter(log => log.module === moduleFilter.value)
  }

  if (traceFilter.value) {
    filtered = filtered.filter(log => log.traceId?.includes(traceFilter.value))
  }

  if (projectFilter.value) {
    filtered = filtered.filter(log => log.projectId === projectFilter.value)
  }

  return filtered
})

const relatedLogs = computed(() => {
  if (!selectedLog.value?.traceId) return []
  return logger.getTraceLog(selectedLog.value.traceId)
})

const getLevelTagType = (level: string) => {
  switch (level) {
    case 'error': return 'danger'
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'debug': return 'info'
    default: return 'info'
  }
}

const formatDuration = (duration: number): string => {
  if (duration < 1000) {
    return `${duration}ms`
  } else {
    return `${(duration / 1000).toFixed(2)}s`
  }
}

const handleRowClick = (row: LogEntry) => {
  selectedLog.value = row
  detailDialogVisible.value = true
}

const filterByTrace = (traceId: string) => {
  traceFilter.value = traceId
}

const exportLogs = (format: 'json' | 'csv') => {
  try {
    const content = logger.exportLogs(format)
    const blob = new Blob([content], {
      type: format === 'json' ? 'application/json' : 'text/csv'
    })

    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `system_logs_${new Date().toISOString().split('T')[0]}.${format}`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success(`日志导出成功 (${format.toUpperCase()})`)
    logger.addLog('info', `日志导出成功: ${format.toUpperCase()}格式`, 'SystemLogs')
  } catch (error) {
    ElMessage.error('导出失败')
    logger.addLog('error', `日志导出失败: ${error}`, 'SystemLogs')
  }
}

const clearLogs = () => {
  logger.clearLogs()
}
</script>

<style scoped>
.system-logs {
  width: 100%;
  min-width: 0;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  box-sizing: border-box;
}

.logs-header h2 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logs-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 100%;
  box-sizing: border-box;
}

.trace-id {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
  font-family: monospace;
  font-size: 12px;
}

.trace-id:hover {
  color: #66b1ff;
}

.project-segment-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.duration-text {
  font-family: monospace;
  font-size: 12px;
  color: #909399;
}

.log-message {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  border-left: 4px solid #409eff;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

.metadata-json {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  border-left: 4px solid #67c23a;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  overflow-x: auto;
  margin: 0;
}

:deep(.el-table) {
  width: 100% !important;
  table-layout: auto;
}

:deep(.el-card__body) {
  padding: 0;
  width: 100%;
}

:deep(.filter-card .el-card__body) {
  padding: 20px;
}

:deep(.el-table__row) {
  transition: background-color 0.3s ease;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .logs-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  :deep(.el-col) {
    margin-bottom: 10px;
  }
}

@media (max-width: 768px) {
  .header-actions {
    flex-wrap: wrap;
    gap: 8px;
  }

  .header-actions .el-button {
    flex: 1;
    min-width: 0;
  }

  :deep(.el-table) {
    font-size: 12px;
  }

  .trace-id {
    font-size: 10px;
  }

  .duration-text {
    font-size: 10px;
  }
}
</style>