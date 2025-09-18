<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Refresh } from '@element-plus/icons-vue'
import api from '../utils/api'
import { logger } from '../utils/logger'

interface Segment {
  id: number
  index: number
  start_time: string
  end_time: string
  time_display: string
  duration: number
  speaker: string
  original_text: string
  translated_text: string
  voice_id: string
  emotion: string
  speed: number
  translated_audio_url: string
  t_tts_duration: number
  target_duration: number
  ratio: number
  is_aligned: boolean
  status: string
  updated_at: string
}

interface Project {
  id: number
  name: string
  source_lang: string
  target_lang: string
  status: string
  segment_count: number
  completed_segment_count: number
  progress_percentage: number
}

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  back: []
}>()

const project = ref<Project | null>(null)
const segments = ref<Segment[]>([])
const loading = ref(false)
const segmentsLoading = ref(false)

const selectedSegments = ref<number[]>([])

const loadProject = async () => {
  loading.value = true
  logger.addLog('info', `开始加载项目信息: ID ${props.projectId}`, 'ProjectDetail')
  try {
    const response = await api.get(`/projects/${props.projectId}/`)
    project.value = response.data
    logger.addLog('success', `成功加载项目: ${project.value.name}`, 'ProjectDetail')
  } catch (error) {
    ElMessage.error('加载项目信息失败')
    logger.addLog('error', `加载项目信息失败: ID ${props.projectId}`, 'ProjectDetail')
    console.error('Load project error:', error)
  } finally {
    loading.value = false
  }
}

const loadSegments = async () => {
  segmentsLoading.value = true
  logger.addLog('info', `开始加载段落列表: 项目 ID ${props.projectId}`, 'ProjectDetail')
  try {
    const response = await api.get(`/projects/${props.projectId}/segments/`)
    segments.value = response.data.results || []
    logger.addLog('success', `成功加载 ${segments.value.length} 个段落`, 'ProjectDetail')
  } catch (error) {
    ElMessage.error('加载段落列表失败')
    logger.addLog('error', `加载段落列表失败: 项目 ID ${props.projectId}`, 'ProjectDetail')
    console.error('Load segments error:', error)
  } finally {
    segmentsLoading.value = false
  }
}

const batchTranslate = async () => {
  try {
    await ElMessageBox.confirm('确认开始批量翻译项目中的所有待翻译段落？', '批量翻译', {
      type: 'warning'
    })

    logger.addLog('info', `开始批量翻译项目: ${project.value?.name}`, 'ProjectDetail')
    const response = await api.post(`/projects/${props.projectId}/batch_translate/`)
    ElMessage.success(response.data.message)
    logger.addLog('success', `批量翻译任务已提交: ${project.value?.name}`, 'ProjectDetail')
    loadProject()
    loadSegments()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量翻译失败')
      logger.addLog('error', `批量翻译失败: ${project.value?.name}`, 'ProjectDetail')
      console.error('Batch translate error:', error)
    }
  }
}

const batchTTS = async () => {
  try {
    await ElMessageBox.confirm('确认为所有已翻译段落生成TTS音频？', '批量TTS', {
      type: 'warning'
    })

    const response = await api.post(`/projects/${props.projectId}/segments/batch_tts/`)
    ElMessage.success(response.data.message)
    loadSegments()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量TTS失败')
      console.error('Batch TTS error:', error)
    }
  }
}

const translateSegment = async (segmentId: number) => {
  try {
    logger.addLog('info', `开始翻译段落: ID ${segmentId}`, 'ProjectDetail')
    const response = await api.post(`/projects/${props.projectId}/segments/${segmentId}/translate/`)
    ElMessage.success('翻译成功')
    logger.addLog('success', `段落翻译成功: ID ${segmentId}`, 'ProjectDetail')
    loadSegments()
  } catch (error) {
    ElMessage.error('翻译失败')
    logger.addLog('error', `段落翻译失败: ID ${segmentId}`, 'ProjectDetail')
    console.error('Translate segment error:', error)
  }
}

const generateTTS = async (segmentId: number) => {
  try {
    const response = await api.post(`/projects/${props.projectId}/segments/${segmentId}/generate_tts/`)
    ElMessage.success('TTS生成成功')
    loadSegments()
  } catch (error) {
    ElMessage.error('TTS生成失败')
    console.error('Generate TTS error:', error)
  }
}

const exportSRT = async () => {
  try {
    const response = await api.get(`/projects/${props.projectId}/export_srt/`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value?.name || 'project'}_translated.srt`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('SRT文件导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
    console.error('Export SRT error:', error)
  }
}

const getStatusTag = (status: string) => {
  const statusMap: Record<string, { type: string, text: string }> = {
    'pending': { type: 'info', text: '待处理' },
    'translating': { type: 'warning', text: '翻译中' },
    'translated': { type: 'success', text: '已翻译' },
    'tts_processing': { type: 'warning', text: 'TTS处理中' },
    'completed': { type: 'success', text: '已完成' },
    'failed': { type: 'danger', text: '失败' },
    'silent': { type: 'info', text: '静音' }
  }
  return statusMap[status] || { type: 'info', text: status }
}

const pendingCount = computed(() => segments.value.filter(s => s.status === 'pending').length)
const translatedCount = computed(() => segments.value.filter(s => s.status === 'translated').length)

const playAudio = (audioUrl: string) => {
  window.open(audioUrl)
}

onMounted(() => {
  loadProject()
  loadSegments()
})
</script>

<template>
  <div v-if="project">
    <!-- 项目信息 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>{{ project.name }}</span>
          <div>
            <el-button @click="$emit('back')">返回列表</el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总段落数" :value="project.segment_count" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="已完成" :value="project.completed_segment_count" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="完成进度" :value="project.progress_percentage" suffix="%" />
        </el-col>
        <el-col :span="6">
          <el-tag :type="getStatusTag(project.status).type" size="large">
            {{ getStatusTag(project.status).text }}
          </el-tag>
        </el-col>
      </el-row>
    </el-card>

    <!-- 操作栏 -->
    <div style="margin-bottom: 20px;">
      <el-button
        type="primary"
        @click="batchTranslate"
        :disabled="pendingCount === 0"
      >
        批量翻译 ({{ pendingCount }}个待翻译)
      </el-button>

      <el-button
        type="success"
        @click="batchTTS"
        :disabled="translatedCount === 0"
      >
        批量TTS ({{ translatedCount }}个已翻译)
      </el-button>

      <el-button @click="exportSRT">
        <el-icon><Download /></el-icon>
        导出SRT
      </el-button>

      <el-button @click="loadSegments">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 段落列表 -->
    <el-table
      :data="segments"
      v-loading="segmentsLoading"
      stripe
      style="width: 100%"
      :row-class-name="({ row }) => row.status === 'failed' ? 'warning-row' : ''"
    >
      <el-table-column prop="index" label="序号" width="80" />

      <el-table-column prop="time_display" label="时间" width="120" />

      <el-table-column prop="speaker" label="说话人" width="100" />

      <el-table-column prop="original_text" label="原文" min-width="200">
        <template #default="{ row }">
          <div style="max-width: 300px; word-break: break-all;">
            {{ row.original_text }}
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="translated_text" label="译文" min-width="200">
        <template #default="{ row }">
          <div v-if="row.translated_text" style="max-width: 300px; word-break: break-all;">
            {{ row.translated_text }}
          </div>
          <span v-else style="color: #999;">未翻译</span>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTag(row.status).type" size="small">
            {{ getStatusTag(row.status).text }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="音频" width="100">
        <template #default="{ row }">
          <el-button
            v-if="row.translated_audio_url"
            size="small"
            type="success"
            @click="playAudio(row.translated_audio_url)"
          >
            播放
          </el-button>
          <span v-else style="color: #999;">无音频</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button
            size="small"
            @click="translateSegment(row.id)"
            :disabled="row.status === 'translating'"
          >
            翻译
          </el-button>

          <el-button
            size="small"
            type="success"
            @click="generateTTS(row.id)"
            :disabled="!row.translated_text || row.status === 'tts_processing'"
          >
            TTS
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.warning-row) {
  background-color: #fef0f0;
}
</style>