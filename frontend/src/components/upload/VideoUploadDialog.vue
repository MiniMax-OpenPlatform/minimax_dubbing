<template>
  <el-dialog
    v-model="visible"
    title="上传视频文件"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <div class="upload-content">
      <!-- 文件选择区 -->
      <div class="file-select-area" v-if="!uploading && !uploadComplete">
        <el-upload
          ref="uploadRef"
          :show-file-list="false"
          :before-upload="handleFileSelect"
          accept=".mp4,.avi,.mov,.wmv,.flv,.mkv"
          drag
          class="upload-dragger"
        >
          <el-icon class="upload-icon"><VideoCamera /></el-icon>
          <div class="upload-text">
            <p>点击或拖拽视频文件到此区域</p>
            <p class="upload-hint">支持 MP4, AVI, MOV, WMV, FLV, MKV 格式，最大 500MB</p>
          </div>
        </el-upload>
      </div>

      <!-- 上传进度区 -->
      <div class="upload-progress-area" v-if="uploading">
        <div class="file-info">
          <el-icon><VideoCamera /></el-icon>
          <span class="file-name">{{ selectedFile?.name }}</span>
          <span class="file-size">{{ formatFileSize(selectedFile?.size || 0) }}</span>
        </div>

        <div class="progress-container">
          <el-progress
            :percentage="uploadPercentage"
            :status="uploadStatus"
            :stroke-width="8"
          />
          <div class="progress-info">
            <span>{{ uploadPercentage }}%</span>
            <span v-if="uploadSpeed > 0">{{ formatSpeed(uploadSpeed) }}</span>
          </div>
        </div>

        <div class="upload-status">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span>正在上传视频文件...</span>
        </div>
      </div>

      <!-- 上传完成区 -->
      <div class="upload-complete-area" v-if="uploadComplete">
        <div class="success-icon">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="success-message">
          <h3>上传成功！</h3>
          <p>视频文件已成功上传并关联到项目</p>
        </div>
      </div>

      <!-- 错误信息 -->
      <div class="error-message" v-if="errorMessage">
        <el-alert
          :title="errorMessage"
          type="error"
          show-icon
          :closable="false"
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" :disabled="uploading">
          {{ uploading ? '上传中...' : (uploadComplete ? '关闭' : '取消') }}
        </el-button>
        <el-button
          v-if="uploading"
          type="danger"
          @click="handleCancelUpload"
        >
          取消上传
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, Loading, CircleCheck } from '@element-plus/icons-vue'

interface Props {
  visible: boolean
  projectId: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'upload-success': []
}>()

// 响应式状态
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadComplete = ref(false)
const uploadPercentage = ref(0)
const uploadSpeed = ref(0)
const uploadStatus = ref<'success' | 'exception' | undefined>(undefined)
const errorMessage = ref('')
const currentXhr = ref<XMLHttpRequest | null>(null)

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

// 文件选择处理
const handleFileSelect = (file: File) => {
  // 验证文件类型
  const allowedTypes = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))

  if (!allowedTypes.includes(fileExtension)) {
    ElMessage.error('请选择支持的视频格式 (MP4, AVI, MOV, WMV, FLV, MKV)')
    return false
  }

  // 验证文件大小 (500MB)
  if (file.size > 500 * 1024 * 1024) {
    ElMessage.error('视频文件大小不能超过500MB')
    return false
  }

  selectedFile.value = file
  startUpload(file)
  return false // 阻止自动上传
}

// 开始上传
const startUpload = async (file: File) => {
  uploading.value = true
  uploadComplete.value = false
  uploadPercentage.value = 0
  uploadSpeed.value = 0
  errorMessage.value = ''
  uploadStatus.value = undefined

  const formData = new FormData()
  formData.append('video_file', file)

  const xhr = new XMLHttpRequest()
  currentXhr.value = xhr

  let lastTime = Date.now()
  let lastLoaded = 0

  // 上传进度监听
  xhr.upload.addEventListener('progress', (event) => {
    if (event.lengthComputable) {
      uploadPercentage.value = Math.round((event.loaded / event.total) * 100)

      // 计算上传速度
      const now = Date.now()
      const timeDiff = (now - lastTime) / 1000 // 秒
      const sizeDiff = event.loaded - lastLoaded

      if (timeDiff > 0.5) { // 每0.5秒更新一次速度
        uploadSpeed.value = sizeDiff / timeDiff
        lastTime = now
        lastLoaded = event.loaded
      }
    }
  })

  // 上传完成监听
  xhr.addEventListener('load', () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      try {
        const response = JSON.parse(xhr.responseText)
        uploadPercentage.value = 100
        uploadStatus.value = 'success'
        uploading.value = false
        uploadComplete.value = true

        ElMessage.success('视频文件上传成功')
        emit('upload-success')
      } catch (error) {
        handleUploadError('响应解析失败')
      }
    } else {
      try {
        const errorResponse = JSON.parse(xhr.responseText)
        handleUploadError(errorResponse.message || `上传失败: ${xhr.status}`)
      } catch {
        handleUploadError(`上传失败: ${xhr.status}`)
      }
    }
  })

  // 上传错误监听
  xhr.addEventListener('error', () => {
    handleUploadError('网络错误，上传失败')
  })

  // 上传取消监听
  xhr.addEventListener('abort', () => {
    uploading.value = false
    uploadStatus.value = 'exception'
    ElMessage.info('上传已取消')
  })

  try {
    // 动态导入API工具
    const api = (await import('../../utils/api')).default

    // 构建完整的上传URL
    const uploadUrl = `/projects/${props.projectId}/upload_video/`

    // 从api实例获取基础配置，回退到本地开发默认值
    const baseURL = api.defaults.baseURL || (() => {
      const protocol = window.location.protocol
      const hostname = window.location.hostname
      return hostname === 'localhost' || hostname === '127.0.0.1'
        ? `${protocol}//${hostname}:5172/api`
        : `/dubbing/api`
    })()
    const fullUrl = baseURL + uploadUrl

    // 设置请求
    xhr.open('POST', fullUrl)

    // 设置认证头
    const apiKey = api.defaults.headers['X-API-KEY']
    if (apiKey) {
      xhr.setRequestHeader('X-API-KEY', apiKey)
    }

    // 发送请求
    xhr.send(formData)
  } catch (error) {
    handleUploadError('初始化上传失败')
  }
}

// 处理上传错误
const handleUploadError = (message: string) => {
  uploading.value = false
  uploadStatus.value = 'exception'
  errorMessage.value = message
  ElMessage.error(message)
}

// 取消上传
const handleCancelUpload = () => {
  if (currentXhr.value) {
    currentXhr.value.abort()
  }
}

// 关闭对话框
const handleClose = () => {
  if (uploading.value) {
    ElMessage.warning('上传进行中，无法关闭')
    return
  }

  // 重置状态
  selectedFile.value = null
  uploading.value = false
  uploadComplete.value = false
  uploadPercentage.value = 0
  uploadSpeed.value = 0
  errorMessage.value = ''
  uploadStatus.value = undefined
  currentXhr.value = null

  visible.value = false
}

// 监听弹窗关闭，清理状态
watch(visible, (newVisible) => {
  if (!newVisible) {
    // 如果正在上传，取消上传
    if (uploading.value && currentXhr.value) {
      currentXhr.value.abort()
    }
  }
})
</script>

<style scoped>
.upload-content {
  padding: 20px 0;
}

.file-select-area {
  text-align: center;
}

.upload-dragger {
  width: 100%;
}

.upload-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 8px 0;
  color: #606266;
}

.upload-hint {
  font-size: 14px;
  color: #909399;
}

.upload-progress-area {
  text-align: center;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.file-name {
  font-weight: 500;
  color: #303133;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #909399;
  font-size: 14px;
}

.progress-container {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.upload-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #409eff;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-complete-area {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  font-size: 64px;
  color: #67c23a;
  margin-bottom: 16px;
}

.success-message h3 {
  color: #303133;
  margin: 0 0 8px 0;
  font-size: 18px;
}

.success-message p {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.error-message {
  margin-top: 16px;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 500px) {
  .file-info {
    flex-direction: column;
    gap: 4px;
  }

  .file-name {
    max-width: none;
  }
}
</style>