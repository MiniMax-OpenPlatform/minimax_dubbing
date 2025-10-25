<template>
  <div class="speaker-profiles">
    <!-- 操作栏 -->
    <div class="actions-bar">
      <el-button
        type="primary"
        :icon="VideoCamera"
        @click="startDiarization"
        :loading="isRunning"
        :disabled="isRunning || !project.video_file_path"
      >
        {{ isRunning ? '识别中...' : '开始说话人识别' }}
      </el-button>

      <el-button
        v-if="isRunning"
        type="danger"
        @click="cancelTask"
      >
        取消任务
      </el-button>

      <el-button
        @click="refreshTasks"
        :icon="Refresh"
      >
        刷新
      </el-button>
    </div>

    <!-- 当前任务进度 -->
    <div v-if="currentTask" class="current-task">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>当前任务</span>
            <el-tag :type="getStatusTagType(currentTask.status)">
              {{ getStatusText(currentTask.status) }}
            </el-tag>
          </div>
        </template>

        <div class="task-info">
          <div class="info-row">
            <span class="label">任务ID:</span>
            <span class="value">{{ currentTask.id }}</span>
          </div>
          <div class="info-row">
            <span class="label">创建时间:</span>
            <span class="value">{{ formatTime(currentTask.created_at) }}</span>
          </div>
          <div v-if="currentTask.completed_at" class="info-row">
            <span class="label">完成时间:</span>
            <span class="value">{{ formatTime(currentTask.completed_at) }}</span>
          </div>
        </div>

        <!-- 进度条 -->
        <div v-if="['pending', 'running'].includes(currentTask.status)" class="progress-section">
          <el-progress
            :percentage="currentTask.progress"
            :status="currentTask.status === 'failed' ? 'exception' : undefined"
          />
          <div class="progress-message">{{ currentTask.progress_message }}</div>
        </div>

        <!-- 错误信息 -->
        <el-alert
          v-if="currentTask.status === 'failed' && currentTask.error_message"
          type="error"
          :title="currentTask.error_message"
          :closable="false"
          show-icon
        />

        <!-- 统计信息 -->
        <div v-if="currentTask.status === 'completed'" class="statistics">
          <el-divider />
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-label">检测到说话人</div>
              <div class="stat-value">{{ currentTask.num_speakers_detected }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">总人脸数</div>
              <div class="stat-value">{{ currentTask.total_faces }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">有效人脸数</div>
              <div class="stat-value">{{ currentTask.valid_faces }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">总片段数</div>
              <div class="stat-value">{{ currentTask.total_segments }}</div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 说话人档案列表 -->
    <div v-if="currentTask && currentTask.speakers && currentTask.speakers.length > 0" class="speakers-list">
      <el-divider content-position="left">
        <h3>说话人档案（{{ currentTask.speakers.length }}人）</h3>
      </el-divider>

      <div class="speakers-grid">
        <el-card v-for="speaker in currentTask.speakers" :key="speaker.id" class="speaker-card">
          <!-- 说话人基本信息 -->
          <div class="speaker-header">
            <div class="speaker-basic-info">
              <h4>{{ speaker.name }}</h4>
              <div class="speaker-meta">
                <el-tag size="small">说话人{{ speaker.speaker_id }}</el-tag>
                <el-tag v-if="speaker.role" size="small" type="info">{{ speaker.role }}</el-tag>
                <el-tag v-if="speaker.gender" size="small" type="success">{{ speaker.gender }}</el-tag>
              </div>
            </div>
          </div>

          <!-- 代表图片 -->
          <div v-if="speaker.representative_images && speaker.representative_images.length > 0" class="representative-images">
            <el-image
              v-for="(img, idx) in speaker.representative_images"
              :key="idx"
              :src="getMediaUrl(img)"
              fit="cover"
              class="rep-image"
              :preview-src-list="speaker.representative_images.map(i => getMediaUrl(i))"
              :initial-index="idx"
            />
          </div>

          <!-- 统计信息 -->
          <div class="speaker-stats">
            <div class="stat">
              <span class="stat-label">人脸数:</span>
              <span class="stat-value">{{ speaker.face_count }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">片段数:</span>
              <span class="stat-value">{{ speaker.segment_count }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">平均置信度:</span>
              <span class="stat-value">{{ (speaker.avg_confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>

          <!-- 外观描述 -->
          <div v-if="speaker.appearance && Object.keys(speaker.appearance).length > 0" class="appearance">
            <el-divider content-position="left">外观特征</el-divider>
            <div class="appearance-content">
              <div v-if="speaker.appearance.clothing" class="appearance-item">
                <strong>服装:</strong> {{ speaker.appearance.clothing }}
              </div>
              <div v-if="speaker.appearance.facial_features" class="appearance-item">
                <strong>面部特征:</strong> {{ speaker.appearance.facial_features }}
              </div>
              <div v-if="speaker.appearance.age_estimate" class="appearance-item">
                <strong>年龄估计:</strong> {{ speaker.appearance.age_estimate }}
              </div>
              <div v-if="speaker.appearance.distinctive_features" class="appearance-item">
                <strong>显著特征:</strong> {{ speaker.appearance.distinctive_features }}
              </div>
            </div>
          </div>

          <!-- 性格分析 -->
          <div v-if="speaker.character_analysis && Object.keys(speaker.character_analysis).length > 0" class="character">
            <el-divider content-position="left">性格分析</el-divider>
            <div class="character-content">
              <div v-if="speaker.character_analysis.personality" class="character-item">
                <strong>性格特点:</strong> {{ speaker.character_analysis.personality }}
              </div>
              <div v-if="speaker.character_analysis.importance" class="character-item">
                <strong>重要程度:</strong> {{ speaker.character_analysis.importance }}
              </div>
              <div v-if="speaker.character_analysis.relationship" class="character-item">
                <strong>人物关系:</strong> {{ speaker.character_analysis.relationship }}
              </div>
              <div v-if="speaker.character_analysis.dialogue_characteristics" class="character-item">
                <strong>说话特点:</strong> {{ speaker.character_analysis.dialogue_characteristics }}
              </div>
            </div>
          </div>

          <!-- 出现片段 -->
          <div class="segments">
            <el-divider content-position="left">出现片段</el-divider>
            <div class="segments-display">
              <el-tag
                v-for="(segIdx, idx) in speaker.segments.slice(0, 20)"
                :key="idx"
                size="small"
                class="segment-tag"
              >
                #{{ segIdx }}
              </el-tag>
              <span v-if="speaker.segments.length > 20" class="more-segments">
                ...共{{ speaker.segments.length }}个片段
              </span>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 无数据提示 -->
    <el-empty v-else-if="!currentTask" description="暂无说话人识别任务">
      <template #extra>
        <p class="empty-hint">
          点击"开始说话人识别"按钮，系统将使用人脸检测+VLM命名+LLM分配技术自动识别视频中的说话人。
        </p>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera, Refresh } from '@element-plus/icons-vue'
import api from '../../utils/api'

interface Speaker {
  id: string
  speaker_id: number
  name: string
  role: string
  gender: string
  face_count: number
  segment_count: number
  segments: number[]
  appearance: Record<string, string>
  character_analysis: Record<string, string>
  representative_images: string[]
  avg_confidence: number
}

interface DiarizationTask {
  id: string
  project: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  progress_message: string
  num_speakers_detected: number | null
  total_faces: number | null
  valid_faces: number | null
  total_segments: number | null
  error_message: string
  is_applied: boolean
  created_at: string
  updated_at: string
  started_at: string | null
  completed_at: string | null
  applied_at: string | null
  speakers: Speaker[]
}

const props = defineProps<{
  project: any
}>()

const currentTask = ref<DiarizationTask | null>(null)
const isRunning = ref(false)
const pollInterval = ref<number | null>(null)

// 启动说话人识别
const startDiarization = async () => {
  try {
    const response = await api.post('/speakers/tasks/', {
      project_id: props.project.id
    })

    currentTask.value = response.data
    isRunning.value = true
    startPolling()

    ElMessage.success('说话人识别任务已启动')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '启动任务失败')
  }
}

// 轮询任务状态
const startPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }

  pollInterval.value = window.setInterval(async () => {
    if (!currentTask.value) return

    try {
      const response = await api.get(`/speakers/tasks/${currentTask.value.id}/progress/`)
      const progressData = response.data

      // 更新进度
      if (currentTask.value) {
        currentTask.value.status = progressData.status
        currentTask.value.progress = progressData.progress
        currentTask.value.progress_message = progressData.message
      }

      // 如果任务完成或失败，停止轮询并刷新完整数据
      if (['completed', 'failed', 'cancelled'].includes(progressData.status)) {
        stopPolling()
        isRunning.value = false
        await refreshCurrentTask()
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
  }, 2000) // 每2秒轮询一次
}

// 停止轮询
const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

// 刷新当前任务详情
const refreshCurrentTask = async () => {
  if (!currentTask.value) return

  try {
    const response = await api.get(`/speakers/tasks/${currentTask.value.id}/`)
    currentTask.value = response.data
  } catch (error) {
    console.error('刷新任务详情失败:', error)
  }
}

// 刷新任务列表
const refreshTasks = async () => {
  try {
    // 获取该项目的最新任务
    const response = await api.get('/speakers/tasks/', {
      params: {
        project_id: props.project.id
      }
    })

    if (response.data.results && response.data.results.length > 0) {
      // 获取第一个任务的详情
      const latestTask = response.data.results[0]
      const detailResponse = await api.get(`/speakers/tasks/${latestTask.id}/`)
      currentTask.value = detailResponse.data

      // 如果任务正在运行，开始轮询
      if (['pending', 'running'].includes(currentTask.value.status)) {
        isRunning.value = true
        startPolling()
      }
    }

    ElMessage.success('刷新成功')
  } catch (error: any) {
    ElMessage.error('刷新失败')
  }
}

// 取消任务
const cancelTask = async () => {
  if (!currentTask.value) return

  try {
    await ElMessageBox.confirm('确定要取消当前任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.delete(`/speakers/tasks/${currentTask.value.id}/cancel/`)
    stopPolling()
    isRunning.value = false
    await refreshCurrentTask()

    ElMessage.success('任务已取消')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '取消任务失败')
    }
  }
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const typeMap: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return textMap[status] || status
}

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 获取media文件的完整URL（指向后端服务器）
const getMediaUrl = (path: string) => {
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  const port = hostname === 'localhost' || hostname === '127.0.0.1' ? ':5172' : ':5172'
  return `${protocol}//${hostname}${port}/media/${path}`
}

// 组件挂载时加载任务
onMounted(() => {
  refreshTasks()
})

// 组件卸载时停止轮询
watch(() => props.project, () => {
  stopPolling()
  refreshTasks()
})
</script>

<style scoped>
.speaker-profiles {
  padding: 16px;
}

.actions-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.current-task {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-info {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row .label {
  font-weight: bold;
  width: 100px;
  color: #909399;
}

.info-row .value {
  flex: 1;
  color: #606266;
}

.progress-section {
  margin: 16px 0;
}

.progress-message {
  margin-top: 8px;
  color: #909399;
  font-size: 14px;
}

.statistics {
  margin-top: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.apply-section {
  margin-top: 20px;
  text-align: center;
}

.speakers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.speaker-card {
  height: fit-content;
}

.speaker-header {
  margin-bottom: 16px;
}

.speaker-basic-info h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.speaker-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.representative-images {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.rep-image {
  width: 120px;
  height: 120px;
  border-radius: 4px;
  cursor: pointer;
}

.speaker-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat .stat-label {
  font-size: 12px;
  color: #909399;
}

.stat .stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.appearance-content,
.character-content {
  font-size: 14px;
}

.appearance-item,
.character-item {
  margin-bottom: 8px;
  line-height: 1.6;
}

.segments-display {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  align-items: center;
}

.segment-tag {
  margin: 2px;
}

.more-segments {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.empty-hint {
  color: #909399;
  font-size: 14px;
  max-width: 500px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .speakers-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .speaker-stats {
    grid-template-columns: 1fr;
  }
}
</style>
