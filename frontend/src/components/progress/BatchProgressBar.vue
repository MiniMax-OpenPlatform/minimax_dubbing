<template>
  <div class="batch-progress-container" v-if="hasActiveProgress">
    <div class="progress-header">
      <el-icon><Loading /></el-icon>
      <span class="progress-title">批量操作进度</span>
      <div class="progress-controls">
        <el-button
          v-if="canExpandDetails"
          text
          size="small"
          @click="expanded = !expanded"
        >
          {{ expanded ? '收起' : '详情' }}
        </el-button>
      </div>
    </div>

    <div class="progress-items">
      <div
        v-for="progress in activeProgresses"
        :key="progress.id"
        class="progress-item"
      >
        <!-- 主进度条 -->
        <div class="progress-main">
          <div class="progress-info">
            <div class="progress-label">
              <el-icon :class="getStatusIconClass(progress.status)">
                <component :is="getStatusIcon(progress.status)" />
              </el-icon>
              <span class="operation-name">
                {{ getOperationName(progress.type) }}
              </span>
              <span class="status-text">{{ getStatusText(progress.type) }}</span>
            </div>

            <div class="progress-stats">
              <span class="progress-count">
                {{ progress.completed }}/{{ progress.total }}
              </span>
              <span class="progress-percentage">
                {{ getProgressPercentage(progress.type) }}%
              </span>
            </div>
          </div>

          <el-progress
            :percentage="getProgressPercentage(progress.type)"
            :status="getProgressStatus(progress.status)"
            :stroke-width="6"
            :show-text="false"
          />

          <!-- 辅助信息 -->
          <div class="progress-details" v-if="progress.status === 'running'">
            <span v-if="progress.currentItem" class="current-item">
              正在处理: {{ progress.currentItem }}
            </span>
            <span v-if="progress.estimatedTimeRemaining" class="time-remaining">
              预计剩余: {{ formatTime(progress.estimatedTimeRemaining) }}
            </span>
            <span v-if="progress.speed" class="speed">
              速度: {{ Math.round(progress.speed) }}项/分钟
            </span>
          </div>

          <!-- 操作按钮 -->
          <div class="progress-actions">
            <el-button
              v-if="progress.canPause && progress.status === 'running'"
              text
              size="small"
              @click="$emit('pauseOperation', progress.type)"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>

            <el-button
              v-if="progress.canPause && progress.status === 'paused'"
              text
              size="small"
              @click="$emit('resumeOperation', progress.type)"
            >
              <el-icon><VideoPlay /></el-icon>
              继续
            </el-button>

            <el-button
              v-if="progress.canCancel && ['running', 'paused'].includes(progress.status)"
              text
              size="small"
              type="danger"
              @click="handleCancel(progress.type)"
            >
              <el-icon><Close /></el-icon>
              取消
            </el-button>
          </div>
        </div>

        <!-- 展开的详细信息 -->
        <div v-if="expanded" class="progress-expanded">
          <div class="progress-summary">
            <div class="summary-item">
              <span class="label">总数:</span>
              <span class="value">{{ progress.total }}</span>
            </div>
            <div class="summary-item success">
              <span class="label">成功:</span>
              <span class="value">{{ progress.completed }}</span>
            </div>
            <div class="summary-item error" v-if="progress.failed > 0">
              <span class="label">失败:</span>
              <span class="value">{{ progress.failed }}</span>
            </div>
            <div class="summary-item" v-if="progress.startTime">
              <span class="label">已用时:</span>
              <span class="value">{{ getElapsedTime(progress.startTime) }}</span>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="progress.errorMessages.length > 0" class="error-messages">
            <div class="error-header">
              <el-icon><WarningFilled /></el-icon>
              <span>错误信息 ({{ progress.errorMessages.length }})</span>
            </div>
            <div class="error-list">
              <div
                v-for="(error, index) in progress.errorMessages.slice(-3)"
                :key="index"
                class="error-item"
              >
                {{ error }}
              </div>
              <div v-if="progress.errorMessages.length > 3" class="error-more">
                还有 {{ progress.errorMessages.length - 3 }} 个错误...
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessageBox } from 'element-plus'
import {
  Loading, VideoPause, VideoPlay, Close, WarningFilled,
  CircleCheck, Warning, Timer, SuccessFilled
} from '@element-plus/icons-vue'
import type { UseBatchProgress } from '../../composables/useBatchProgress'

interface Props {
  progressState: UseBatchProgress['progressState']
  hasActiveProgress: boolean
  activeProgresses: ReturnType<UseBatchProgress['activeProgresses']>
  getProgressPercentage: UseBatchProgress['getProgressPercentage']
  formatTime: UseBatchProgress['formatTime']
  getStatusText: UseBatchProgress['getStatusText']
}

const props = defineProps<Props>()

const emit = defineEmits<{
  pauseOperation: [type: 'translate' | 'tts']
  resumeOperation: [type: 'translate' | 'tts']
  cancelOperation: [type: 'translate' | 'tts']
}>()

const expanded = ref(false)

// 是否可以展开详情
const canExpandDetails = computed(() => {
  return props.activeProgresses.some(p =>
    p.errorMessages.length > 0 || p.failed > 0 || p.startTime
  )
})

// 获取操作名称
const getOperationName = (type: 'translate' | 'tts') => {
  return type === 'translate' ? '批量翻译' : '批量TTS'
}

// 获取进度条状态
const getProgressStatus = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'error':
    case 'cancelled':
      return 'exception'
    case 'paused':
      return 'warning'
    default:
      return undefined
  }
}

// 获取状态图标
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'running':
      return Loading
    case 'paused':
      return Timer
    case 'completed':
      return CircleCheck
    case 'error':
      return Warning
    case 'cancelled':
      return Close
    default:
      return Loading
  }
}

// 获取状态图标样式类
const getStatusIconClass = (status: string) => {
  return {
    'status-icon': true,
    'running': status === 'running',
    'paused': status === 'paused',
    'completed': status === 'completed',
    'error': status === 'error',
    'cancelled': status === 'cancelled'
  }
}

// 处理取消操作
const handleCancel = async (type: 'translate' | 'tts') => {
  try {
    await ElMessageBox.confirm(
      `确定要取消正在进行的${getOperationName(type)}操作吗？`,
      '取消确认',
      {
        confirmButtonText: '确定取消',
        cancelButtonText: '继续操作',
        type: 'warning'
      }
    )
    emit('cancelOperation', type)
  } catch {
    // 用户取消了取消操作
  }
}

// 获取已用时间
const getElapsedTime = (startTime: number) => {
  const elapsed = (Date.now() - startTime) / 1000
  if (elapsed < 60) {
    return `${Math.round(elapsed)}秒`
  } else {
    const minutes = Math.floor(elapsed / 60)
    const seconds = Math.round(elapsed % 60)
    return `${minutes}分${seconds}秒`
  }
}
</script>

<style scoped>
.batch-progress-container {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
  margin: 8px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.progress-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #495057;
}

.progress-controls {
  display: flex;
  gap: 8px;
}

.progress-item {
  margin-bottom: 16px;
}

.progress-item:last-child {
  margin-bottom: 0;
}

.progress-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  font-size: 16px;
}

.status-icon.running {
  color: #409eff;
  animation: spin 1s linear infinite;
}

.status-icon.paused {
  color: #e6a23c;
}

.status-icon.completed {
  color: #67c23a;
}

.status-icon.error {
  color: #f56c6c;
}

.status-icon.cancelled {
  color: #909399;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.operation-name {
  font-weight: 500;
  color: #212529;
}

.status-text {
  font-size: 14px;
  color: #6c757d;
}

.progress-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.progress-count {
  color: #495057;
}

.progress-percentage {
  color: #409eff;
  font-weight: 600;
}

.progress-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #6c757d;
  flex-wrap: wrap;
}

.current-item {
  color: #495057;
  font-weight: 500;
}

.progress-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.progress-expanded {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.progress-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

.summary-item .label {
  color: #6c757d;
}

.summary-item .value {
  font-weight: 500;
  color: #495057;
}

.summary-item.success .value {
  color: #28a745;
}

.summary-item.error .value {
  color: #dc3545;
}

.error-messages {
  border-top: 1px solid #e9ecef;
  padding-top: 12px;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #dc3545;
}

.error-list {
  max-height: 120px;
  overflow-y: auto;
}

.error-item {
  padding: 4px 8px;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #721c24;
}

.error-more {
  padding: 4px 8px;
  font-size: 12px;
  color: #6c757d;
  text-align: center;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .progress-details {
    flex-direction: column;
    gap: 4px;
  }

  .progress-summary {
    flex-direction: column;
    gap: 8px;
  }

  .progress-actions {
    justify-content: flex-start;
  }
}
</style>