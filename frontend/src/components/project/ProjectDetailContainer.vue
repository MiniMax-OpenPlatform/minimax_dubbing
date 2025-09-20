<template>
  <div class="project-detail-container">
    <!-- 项目头部信息 -->
    <div class="project-header" v-if="project">
      <div class="header-left">
        <el-button @click="$emit('back')" :icon="ArrowLeft" type="text" size="large">
          返回项目列表
        </el-button>
        <div class="project-info">
          <h1 class="project-title">{{ project.name }}</h1>
        </div>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button @click="showSettings = true" :icon="Setting" type="primary">
            项目配置
          </el-button>
          <el-button @click="refreshData" :icon="Refresh" :loading="loading">
            刷新数据
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 媒体预览 -->
    <MediaPreview
      :project="project"
      :segments="segments"
      :concatenated-audio-url="concatenatedAudioUrl"
      :audio-key="audioKey"
      :final-mixed-audio-url="null"
      @segment-click="handleSegmentClick"
      @time-update="handleTimeUpdate"
    />

    <!-- 项目操作工具栏 -->
    <EditorToolbar
      v-if="project"
      :selected-count="selectedSegments.length"
      :total-count="segments.length"
      :batch-loading="batchTtsLoading"
      @batch-translate="handleBatchTranslate"
      @batch-tts="handleBatchTts"
      @concatenate-audio="handleConcatenateAudio"
      @export="handleExport"
      @upload-srt="handleUploadSrt"
      @auto-assign-speaker="handleAutoAssignSpeaker"
      @batch-speaker="handleBatchSpeaker"
    />


    <!-- 段落数据表格 -->
    <InlineEditTable
      :segments="segments"
      :table-height="600"
      :project-id="projectId"
      :project="project"
      @segment-click="handleSegmentClick"
      @selection-change="handleSelectionChange"
      @field-change="updateSegment"
      @translate-single="handleTranslateSingle"
      @generate-tts="handleGenerateTts"
      @shorten-translation="handleShortenTranslation"
      @lengthen-translation="handleLengthenTranslation"
      @delete-row="handleDeleteSegment"
      @duplicate-row="handleDuplicateSegment"
    />

    <!-- 项目设置对话框 -->
    <ProjectSettings
      :visible="showSettings"
      :project="project"
      :saving="settingsSaving"
      @close="showSettings = false"
      @save="saveProjectSettings"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Setting, Refresh } from '@element-plus/icons-vue'

// 导入子组件
import MediaPreview from './MediaPreview.vue'
import InlineEditTable from '../editor/InlineEditTable.vue'
import ProjectSettings from './ProjectSettings.vue'
import EditorToolbar from '../editor/EditorToolbar.vue'
import BatchOperations from './BatchOperations.vue'

// 导入composables
import { useProjectData } from '../../composables/useProjectData'
import { useAudioOperations } from '../../composables/useAudioOperations'
import type { Segment } from '../../composables/useProjectData'

// Props 和 Emits
const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  back: []
}>()

// 使用composables
const {
  project,
  segments,
  loading,
  refreshData,
  updateSegment
} = useProjectData(props.projectId)

const {
  batchTtsLoading,
  concatenatedAudioUrl,
  audioKey,
  batchTts,
  concatenateAudio
} = useAudioOperations(props.projectId)

// 本地状态
const settingsSaving = ref(false)
const showSettings = ref(false)
const selectedSegments = ref<Segment[]>([])

// 页面初始化
onMounted(() => {
  refreshData()
})

// 保存项目设置
const saveProjectSettings = async (settings: any) => {
  settingsSaving.value = true
  try {
    // 这里应该调用useProjectData的updateProject方法
    // 但为了保持兼容性，先保留原有逻辑
    const api = (await import('../../utils/api')).default
    await api.patch(`/projects/${props.projectId}/`, settings)

    if (project.value) {
      project.value = { ...project.value, ...settings }
    }
    showSettings.value = false
    ElMessage.success('项目设置保存成功')
    console.log('项目设置保存成功', { settings })
  } catch (error) {
    console.error('保存项目设置失败', error)
    ElMessage.error('保存项目设置失败')
  } finally {
    settingsSaving.value = false
  }
}

// 处理段落点击
const handleSegmentClick = (segment: Segment) => {
  console.log('段落点击', { segmentId: segment.id, index: segment.index })
  // 这里可以添加段落点击的逻辑，比如跳转到对应时间点
}

// 处理时间更新
const handleTimeUpdate = (time: number) => {
  // 处理音频时间更新
  console.log('时间更新', { time })
}

// 选择相关处理
const handleSelectionChange = (selection: Segment[]) => {
  selectedSegments.value = selection
}

const clearSelection = () => {
  selectedSegments.value = []
}

// 批量操作处理
const handleBatchTranslate = async () => {
  try {
    const api = (await import('../../utils/api')).default

    // 项目级别的批量翻译，翻译所有待处理的段落
    await api.post(`/projects/${props.projectId}/batch_translate/`)

    ElMessage.success('开始批量翻译项目中的所有待处理段落')
    refreshData()
  } catch (error) {
    console.error('批量翻译失败', error)
    ElMessage.error('批量翻译失败')
  }
}

const handleBatchTts = async () => {
  try {
    const api = (await import('../../utils/api')).default

    // 段落级别的批量TTS
    await api.post(`/projects/${props.projectId}/segments/batch_tts/`)

    ElMessage.success('开始批量TTS项目中的所有已翻译段落')
    refreshData()
  } catch (error) {
    console.error('批量TTS失败', error)
    ElMessage.error('批量TTS失败')
  }
}

// 使用useAudioOperations中的concatenateAudio函数
const handleConcatenateAudio = concatenateAudio

// 批量设置处理
const handleBatchSetVoice = async (voiceId: string) => {
  try {
    const api = (await import('../../utils/api')).default
    const segmentIds = selectedSegments.value.map(s => s.id)

    await api.post(`/projects/${props.projectId}/segments/batch_update/`, {
      segment_ids: segmentIds,
      voice_id: voiceId
    })

    ElMessage.success('批量设置音色成功')
    refreshData()
  } catch (error) {
    ElMessage.error('批量设置音色失败')
  }
}

const handleBatchSetEmotion = async (emotion: string) => {
  try {
    const api = (await import('../../utils/api')).default
    const segmentIds = selectedSegments.value.map(s => s.id)

    await api.post(`/projects/${props.projectId}/segments/batch_update/`, {
      segment_ids: segmentIds,
      emotion
    })

    ElMessage.success('批量设置情感成功')
    refreshData()
  } catch (error) {
    ElMessage.error('批量设置情感失败')
  }
}

const handleBatchSetSpeed = async (speed: number) => {
  try {
    const api = (await import('../../utils/api')).default
    const segmentIds = selectedSegments.value.map(s => s.id)

    await api.post(`/projects/${props.projectId}/segments/batch_update/`, {
      segment_ids: segmentIds,
      speed
    })

    ElMessage.success('批量设置语速成功')
    refreshData()
  } catch (error) {
    ElMessage.error('批量设置语速失败')
  }
}

const handleBatchSetSpeaker = async (speaker: string) => {
  try {
    const api = (await import('../../utils/api')).default
    const segmentIds = selectedSegments.value.map(s => s.id)

    await api.post(`/projects/${props.projectId}/segments/batch_update/`, {
      segment_ids: segmentIds,
      speaker
    })

    ElMessage.success('批量设置说话人成功')
    refreshData()
  } catch (error) {
    ElMessage.error('批量设置说话人失败')
  }
}

// 导出处理
const handleExport = (type: string) => {
  switch (type) {
    case 'srt':
      handleExportSrt()
      break
    case 'csv':
      handleExportCsv()
      break
    case 'audio':
      handleExportAudio()
      break
  }
}

const handleExportSrt = async () => {
  try {
    const api = (await import('../../utils/api')).default
    const response = await api.get(`/projects/${props.projectId}/export_srt/`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${project.value?.name || 'project'}.srt`
    a.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('SRT文件导出成功')
  } catch (error) {
    ElMessage.error('SRT文件导出失败')
  }
}

const handleExportCsv = async () => {
  try {
    const api = (await import('../../utils/api')).default
    const response = await api.get(`/projects/${props.projectId}/export-csv/`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${project.value?.name || 'project'}.csv`
    a.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('CSV文件导出成功')
  } catch (error) {
    ElMessage.error('CSV文件导出失败')
  }
}

const handleExportAudio = async () => {
  try {
    await concatenateAudio()
    ElMessage.success('音频拼接成功')
  } catch (error) {
    ElMessage.error('音频拼接失败')
  }
}

// 单个操作处理
const handleTranslateSingle = async (segment: Segment) => {
  try {
    const api = (await import('../../utils/api')).default
    await api.post(`/projects/${props.projectId}/segments/${segment.id}/translate/`)
    ElMessage.success('翻译任务已启动')
    refreshData()
  } catch (error) {
    ElMessage.error('翻译失败')
  }
}

const handleGenerateTts = async (segment: Segment) => {
  try {
    const api = (await import('../../utils/api')).default

    // 使用简化TTS接口，不进行时间戳对齐
    const response = await api.post(`/projects/${props.projectId}/segments/${segment.id}/simple_tts/`)

    if (response.data.success) {
      ElMessage.success(`TTS生成成功，时长比例: ${response.data.ratio}`)
    } else {
      ElMessage.warning(response.data.error || 'TTS生成失败')
    }

    refreshData()
  } catch (error: any) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('TTS生成失败')
    }
  }
}

const handleShortenTranslation = async (segment: Segment) => {
  try {
    const api = (await import('../../utils/api')).default

    const response = await api.post(`/projects/${props.projectId}/segments/${segment.id}/shorten/`)

    if (response.data.success) {
      ElMessage.success(response.data.message || '译文缩短成功')
    } else {
      ElMessage.warning(response.data.error || '译文缩短失败')
    }

    refreshData()
  } catch (error: any) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('译文缩短失败')
    }
  }
}

const handleLengthenTranslation = async (segment: Segment) => {
  try {
    const api = (await import('../../utils/api')).default

    const response = await api.post(`/projects/${props.projectId}/segments/${segment.id}/lengthen/`)

    if (response.data.success) {
      ElMessage.success(response.data.message || '译文加长成功')
    } else {
      ElMessage.warning(response.data.error || '译文加长失败')
    }

    refreshData()
  } catch (error: any) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('译文加长失败')
    }
  }
}

// 删除段落
const handleDeleteSegment = async (segment: Segment) => {
  try {
    const api = (await import('../../utils/api')).default

    await api.delete(`/projects/${props.projectId}/segments/${segment.id}/`)

    ElMessage.success('段落删除成功')
    refreshData()
  } catch (error: any) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('段落删除失败')
    }
  }
}

// 复制段落（在下方增加新段落）
const handleDuplicateSegment = async (segment: Segment) => {
  try {
    const api = (await import('../../utils/api')).default

    // 解析时间戳为秒数
    const parseTimeToSeconds = (timeStr: string): number => {
      if (typeof timeStr === 'number') return timeStr
      if (!timeStr) return 0

      // 如果是 HH:MM:SS,mmm 格式
      const match = timeStr.match(/^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/)
      if (match) {
        const [, hours, minutes, seconds, milliseconds] = match
        return parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds) + parseInt(milliseconds) / 1000
      }

      // 如果已经是数字字符串
      return parseFloat(timeStr) || 0
    }

    // 创建新段落数据，基于当前段落但清空一些字段
    const newSegmentData = {
      index: segment.index + 1, // 在当前段落后插入
      start_time: parseTimeToSeconds(segment.end_time), // 新段落从当前段落结束时间开始
      end_time: parseTimeToSeconds(segment.end_time), // 初始结束时间和开始时间相同
      original_text: '新段落', // 默认文本，不能为空
      translated_text: '', // 空白译文
      speaker: segment.speaker, // 继承说话人
      voice_id: segment.voice_id, // 继承音色
      emotion: segment.emotion || 'auto', // 继承情感
      speed: segment.speed || 1.0, // 继承语速
      target_duration: 0, // 初始时长为0
      status: 'pending'
    }

    await api.post(`/projects/${props.projectId}/segments/`, newSegmentData)

    ElMessage.success('新段落添加成功')
    refreshData()
  } catch (error: any) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('新段落添加失败')
    }
  }
}


// SRT上传处理
const handleUploadSrt = async (file: File) => {
  try {
    const formData = new FormData()
    formData.append('srt_file', file)
    formData.append('project_name', `${project.value?.name || 'project'}_imported_${Date.now()}`)

    const api = (await import('../../utils/api')).default
    await api.post(`/projects/upload_srt/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    ElMessage.success('SRT文件上传成功，将创建新项目')

    // 不需要刷新当前项目，因为这会创建一个新项目
    ElMessage.info('SRT文件已作为新项目导入，请在项目列表中查看')

  } catch (error) {
    console.error('SRT上传失败', error)
    ElMessage.error('SRT文件上传失败')
  }
}

// 说话人管理
const handleAutoAssignSpeaker = async () => {
  try {
    // 这个功能可能需要根据实际后端API来实现
    // 暂时使用批量更新来模拟自动分配
    ElMessage.info('自动分配说话人功能需要后端支持，请手动设置')
  } catch (error) {
    console.error('自动分配说话人失败', error)
    ElMessage.error('自动分配说话人失败')
  }
}

const handleBatchSpeaker = async () => {
  // 这里可以打开一个对话框让用户选择说话人
  try {
    const { value: speaker } = await ElMessageBox.prompt('请输入说话人', '批量修改说话人', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S/,
      inputErrorMessage: '说话人不能为空',
      inputPlaceholder: '例如: speaker1, speaker2, narrator 等'
    })

    if (!speaker) return

    if (selectedSegments.value.length === 0) {
      ElMessage.warning('请先选择要修改的段落')
      return
    }

    const segmentIds = selectedSegments.value.map(s => s.id)
    const api = (await import('../../utils/api')).default

    await api.post(`/projects/${props.projectId}/segments/batch_update/`, {
      segment_ids: segmentIds,
      speaker
    })

    ElMessage.success(`已为 ${selectedSegments.value.length} 个段落设置说话人: ${speaker}`)
    refreshData()

  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量修改说话人失败', error)
      ElMessage.error('批量修改说话人失败')
    }
  }
}
</script>

<style scoped>
.project-detail-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background-color: #f5f7fa;
}

/* 项目头部样式 */
.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-info {
  flex: 1;
}

.project-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}


.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .project-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .header-left {
    justify-content: space-between;
  }


  .header-right {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .project-detail-container {
    padding: 12px;
  }

  .project-header {
    padding: 16px;
  }

  .project-title {
    font-size: 20px;
  }

  .header-left {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}
</style>