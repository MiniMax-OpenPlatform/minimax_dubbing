<template>
  <div class="upload-progress-container" v-if="visible">
    <div class="progress-header">
      <el-icon class="status-icon" :class="getStatusIconClass(status)">
        <component :is="getStatusIcon(status)" />
      </el-icon>
      <span class="progress-title">{{ getProgressTitle() }}</span>
      <div class="progress-controls">
        <el-button
          v-if="canCancel"
          text
          size="small"
          type="danger"
          @click="handleCancel"
        >
          <el-icon><Close /></el-icon>
          取消
        </el-button>
        <el-button
          v-if="canDismiss"
          text
          size="small"
          @click="handleDismiss"
        >
          <el-icon><Close /></el-icon>
          关闭
        </el-button>
      </div>
    </div>

    <div class="progress-main">
      <!-- 文件信息 -->
      <div class="file-info">
        <div class="file-name">
          <el-icon><VideoCamera /></el-icon>
          <span>{{ fileName }}</span>
        </div>
        <div class="file-size">
          {{ formatFileSize(fileSize) }}
        </div>
      </div>

      <!-- 进度条 -->
      <el-progress
        :percentage="percentage"
        :status="getProgressStatus(status)"
        :stroke-width="8"
        :show-text="false"
        class="upload-progress"
      />

      <!-- 进度详情 -->
      <div class="progress-details">
        <div class="progress-stats">
          <span class="progress-percentage">{{ percentage }}%</span>
          <span class="uploaded-size" v-if="status === 'uploading'">
            {{ formatFileSize(uploadedSize) }} / {{ formatFileSize(fileSize) }}
          </span>
        </div>

        <div class="upload-info" v-if="status === 'uploading'">
          <span v-if="speed > 0" class="upload-speed">
            {{ formatSpeed(speed) }}
          </span>
          <span v-if="remainingTime > 0" class="remaining-time">
            剩余时间: {{ formatTime(remainingTime) }}
          </span>
        </div>
      </div>

      <!-- 状态消息 -->
      <div class="status-message" v-if="statusMessage">
        <el-icon v-if="status === 'error'"><Warning /></el-icon>
        <el-icon v-if="status === 'success'"><CircleCheck /></el-icon>
        <span>{{ statusMessage }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessageBox } from 'element-plus'
import {
  Loading, Close, Warning, CircleCheck, VideoCamera,
  SuccessFilled, Timer
} from '@element-plus/icons-vue'

export interface UploadProgress {
  fileName: string
  fileSize: number
  uploadedSize: number
  percentage: number
  speed: number // bytes per second
  remainingTime: number // seconds
  status: 'uploading' | 'success' | 'error' | 'cancelled'
  statusMessage?: string
  visible: boolean
}

interface Props {
  fileName: string
  fileSize: number
  uploadedSize: number
  percentage: number
  speed?: number
  remainingTime?: number
  status: 'uploading' | 'success' | 'error' | 'cancelled'
  statusMessage?: string
  visible: boolean
}

const props = withDefaults(defineProps<Props>(), {
  speed: 0,
  remainingTime: 0,
  statusMessage: ''
})

const emit = defineEmits<{
  cancel: []
  dismiss: []
}>()

// 计算属性
const canCancel = computed(() => props.status === 'uploading')
const canDismiss = computed(() => ['success', 'error', 'cancelled'].includes(props.status))

// 获取进度标题
const getProgressTitle = () => {
  switch (props.status) {
    case 'uploading':
      return '正在上传视频文件'
    case 'success':
      return '视频文件上传成功'
    case 'error':
      return '视频文件上传失败'
    case 'cancelled':
      return '上传已取消'
    default:
      return '上传视频文件'
  }
}

// 获取进度条状态
const getProgressStatus = (status: string) => {
  switch (status) {
    case 'success':
      return 'success'
    case 'error':
    case 'cancelled':
      return 'exception'
    default:
      return undefined
  }
}

// 获取状态图标
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'uploading':
      return Loading
    case 'success':
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
    'uploading': status === 'uploading',
    'success': status === 'success',
    'error': status === 'error',
    'cancelled': status === 'cancelled'
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 格式化上传速度
const formatSpeed = (bytesPerSecond: number): string => {
  return formatFileSize(bytesPerSecond) + '/s'
}

// 格式化时间
const formatTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${minutes}分${secs}秒`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
}

// 处理取消上传
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消视频文件上传吗？已上传的数据将丢失。',
      '取消上传确认',
      {
        confirmButtonText: '确定取消',
        cancelButtonText: '继续上传',
        type: 'warning'
      }
    )
    emit('cancel')
  } catch {
    // 用户取消了取消操作
  }
}

// 处理关闭进度条
const handleDismiss = () => {
  emit('dismiss')
}
</script>

<style scoped>
.upload-progress-container {
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
  gap: 8px;
  margin-bottom: 12px;
}

.status-icon {
  font-size: 16px;
}

.status-icon.uploading {
  color: #409eff;
  animation: spin 1s linear infinite;
}

.status-icon.success {
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

.progress-title {
  font-weight: 600;
  color: #495057;
  flex: 1;
}

.progress-controls {
  display: flex;
  gap: 8px;
}

.progress-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #495057;
  flex: 1;
  min-width: 0; /* 允许文字截断 */
}

.file-name span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 14px;
  color: #6c757d;
  white-space: nowrap;
  margin-left: 12px;
}

.upload-progress {
  margin: 4px 0;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.progress-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-percentage {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}

.uploaded-size {
  font-size: 14px;
  color: #6c757d;
}

.upload-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: #6c757d;
}

.upload-speed {
  color: #409eff;
  font-weight: 500;
}

.remaining-time {
  color: #6c757d;
}

.status-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e9ecef;
}

.status-message .el-icon {
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-header {
    flex-wrap: wrap;
    gap: 8px;
  }

  .file-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .file-size {
    margin-left: 0;
  }

  .progress-details {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .upload-info {
    flex-direction: column;
    gap: 4px;
    align-items: flex-start;
  }
}
</style>