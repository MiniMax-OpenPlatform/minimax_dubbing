<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Download, Refresh, Setting } from '@element-plus/icons-vue'
import api from '../utils/api'
import { logger } from '../utils/logger'
import VideoPlayer from './VideoPlayer.vue'
import AudioTrack from './AudioTrack.vue'

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

const editingSegments = ref<Set<number>>(new Set())
const editingValues = ref<Record<number, {original_text?: string, translated_text?: string, speaker?: string}>>({})
const lastConcatenatedAudioUrl = ref<string>('')
const showProjectSettings = ref(false)

const projectSettings = ref({
  name: '',
  description: '',
  source_lang: 'zh',
  target_lang: 'en',
  voice_mappings: [] as Array<{
    speaker: string
    voice_id: string
  }>,
  custom_vocabulary: [] as Array<{
    词汇: string
    译文: string
  }>
})

const vocabularyBatchText = ref('')

// 新增数据集相关状态
const selectedSegments = ref<Set<number>>(new Set())
const pagination = ref({
  currentPage: 1,
  pageSize: 20,
  total: 0
})
const currentAudio = ref<HTMLAudioElement | null>(null)
const batchRoleForm = ref({
  visible: false,
  newRole: '',
  selectedCount: 0
})

// 视频和音频相关状态
const translatedVideoUrl = ref('')
const translatedAudioUrl = ref('')
const originalAudioUrl = ref('')
const backgroundAudioUrl = ref('')
const compositeAudioUrl = ref('')

// 播放同步相关
const currentPlayTime = ref(0)
const isVideoVisible = ref({
  original: true,
  translated: false
})
const isAudioVisible = ref({
  translated: true,
  original: false,
  background: false,
  composite: false
})

const loadProject = async () => {
  loading.value = true
  logger.addLog('info', `开始加载项目信息: ID ${props.projectId}`, 'ProjectDetail')
  try {
    const response = await api.get(`/projects/${props.projectId}/`)
    project.value = response.data
    loadProjectSettings()
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

const concatenateAudio = async () => {
  const traceId = logger.startTrace('音频拼接', {
    projectId: props.projectId,
    projectName: project.value?.name,
    segmentCount: audioSegmentsCount.value
  })

  try {
    await ElMessageBox.confirm(
      `确认拼接项目中的 ${audioSegmentsCount.value} 个音频段落为完整音频文件？`,
      '音频拼接',
      { type: 'warning' }
    )

    logger.traceLog(traceId, 'info', `用户确认音频拼接: ${project.value?.name}`, 'ProjectDetail', {
      projectId: props.projectId
    })

    const loadingInstance = ElLoading.service({
      lock: true,
      text: '正在拼接音频，请稍候...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    const response = await api.post(`/projects/${props.projectId}/concatenate_audio/`)

    loadingInstance.close()

    if (response.data.success) {
      ElMessage.success(`音频拼接成功！拼接了${response.data.segments_count}个段落`)
      logger.traceLog(traceId, 'success', `音频拼接成功: ${response.data.audio_url}`, 'ProjectDetail', {
        projectId: props.projectId,
        metadata: {
          segmentsCount: response.data.segments_count,
          audioUrl: response.data.audio_url,
          traceIdBackend: response.data.trace_id
        }
      })

      // 提供在线播放
      await ElMessageBox.confirm(
        '音频拼接完成，是否立即播放？',
        '播放音频',
        { type: 'success' }
      )

      // 保存音频URL用于后续下载
      lastConcatenatedAudioUrl.value = response.data.audio_url

      // 在线播放拼接后的音频
      playAudio(response.data.audio_url)

      logger.endTrace(traceId, 'success', `音频拼接和播放完成，共处理${response.data.segments_count}个段落`)

    } else {
      ElMessage.error('音频拼接失败')
      logger.traceLog(traceId, 'error', `音频拼接失败: ${response.data.error}`, 'ProjectDetail', {
        projectId: props.projectId
      })
      logger.endTrace(traceId, 'error', '音频拼接失败')
    }

  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('音频拼接失败')
      logger.traceLog(traceId, 'error', `音频拼接异常: ${error}`, 'ProjectDetail', {
        projectId: props.projectId
      })
      logger.endTrace(traceId, 'error', `音频拼接异常: ${error}`)
      console.error('Concatenate audio error:', error)
    } else {
      logger.traceLog(traceId, 'info', '用户取消音频拼接操作', 'ProjectDetail', {
        projectId: props.projectId
      })
      logger.endTrace(traceId, 'success', '用户取消操作')
    }
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
const audioSegmentsCount = computed(() => segments.value.filter(s => s.translated_audio_url && s.translated_audio_url.trim() !== '').length)

const playAudio = (audioUrl: string) => {
  window.open(audioUrl)
}

const downloadAudio = () => {
  if (!lastConcatenatedAudioUrl.value) {
    ElMessage.error('没有可下载的音频文件')
    return
  }

  const link = document.createElement('a')
  link.href = lastConcatenatedAudioUrl.value
  link.download = `${project.value?.name || 'project'}_complete_audio.mp3`
  link.click()

  ElMessage.success('音频下载已开始')
  logger.addLog('info', '用户下载完整音频文件', 'ProjectDetail', {
    projectId: props.projectId,
    audioUrl: lastConcatenatedAudioUrl.value
  })
}

const startEdit = (segmentId: number, segment: Segment) => {
  editingSegments.value.add(segmentId)
  editingValues.value[segmentId] = {
    original_text: segment.original_text,
    translated_text: segment.translated_text,
    speaker: segment.speaker
  }
}

const cancelEdit = (segmentId: number) => {
  editingSegments.value.delete(segmentId)
  delete editingValues.value[segmentId]
}

const saveEdit = async (segmentId: number) => {
  try {
    const editData = editingValues.value[segmentId]
    if (!editData) return

    logger.addLog('info', `开始保存段落编辑: ID ${segmentId}`, 'ProjectDetail')
    const response = await api.patch(`/projects/${props.projectId}/segments/${segmentId}/`, editData)

    ElMessage.success('保存成功')
    logger.addLog('success', `段落编辑保存成功: ID ${segmentId}`, 'ProjectDetail')

    editingSegments.value.delete(segmentId)
    delete editingValues.value[segmentId]
    loadSegments() // 重新加载数据
  } catch (error) {
    ElMessage.error('保存失败')
    logger.addLog('error', `段落编辑保存失败: ID ${segmentId}`, 'ProjectDetail')
    console.error('Save edit error:', error)
  }
}

const handleKeydown = (event: KeyboardEvent, segmentId: number) => {
  if (event.key === 'Escape') {
    cancelEdit(segmentId)
  } else if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    saveEdit(segmentId)
  }
}

const loadProjectSettings = () => {
  if (project.value) {
    projectSettings.value.name = project.value.name
    projectSettings.value.source_lang = project.value.source_lang
    projectSettings.value.target_lang = project.value.target_lang
    projectSettings.value.description = (project.value as any).description || ''

    // 确保 voice_mappings 是数组
    const voiceMappings = (project.value as any).voice_mappings
    projectSettings.value.voice_mappings = Array.isArray(voiceMappings) ? voiceMappings : []

    // 确保 custom_vocabulary 是数组
    const customVocabulary = (project.value as any).custom_vocabulary
    projectSettings.value.custom_vocabulary = Array.isArray(customVocabulary) ? customVocabulary : []
  }
}

const addVoiceMapping = () => {
  projectSettings.value.voice_mappings.push({
    speaker: 'SPEAKER_00',
    voice_id: 'ai_her_04'
  })
}

const removeVoiceMapping = (index: number) => {
  projectSettings.value.voice_mappings.splice(index, 1)
}

const addVocabularyItem = () => {
  projectSettings.value.custom_vocabulary.push({
    词汇: '北京',
    译文: 'Beijing'
  })
}

const removeVocabularyItem = (index: number) => {
  projectSettings.value.custom_vocabulary.splice(index, 1)
}

const importVocabularyBatch = () => {
  const lines = vocabularyBatchText.value.trim().split('\n')
  let successCount = 0

  lines.forEach(line => {
    const parts = line.split(',')
    if (parts.length >= 2) {
      projectSettings.value.custom_vocabulary.push({
        词汇: parts[0].trim(),
        译文: parts[1].trim()
      })
      successCount++
    }
  })

  if (successCount > 0) {
    ElMessage.success(`成功导入 ${successCount} 个词汇`)
    vocabularyBatchText.value = ''
  } else {
    ElMessage.error('导入失败，请检查格式')
  }
}

// 数据集相关计算属性和方法
const paginatedSegments = computed(() => {
  const start = (pagination.value.currentPage - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return segments.value.slice(start, end)
})

// 选择变化处理
const handleSelectionChange = (selection: any[]) => {
  selectedSegments.value = new Set(selection.map(item => item.id))
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
}

const handleCurrentChange = (page: number) => {
  pagination.value.currentPage = page
}

// 自动分配角色与情绪
const autoAssignRoles = async () => {
  ElMessage.info('自动分配角色与情绪功能开发中...')
  // TODO: 调用LLM API进行角色分配
}

// 显示批量修改角色对话框
const showBatchRoleDialog = () => {
  batchRoleForm.value.selectedCount = selectedSegments.value.size
  batchRoleForm.value.visible = true
}

// 执行批量角色修改
const executeBatchRoleChange = async () => {
  if (!batchRoleForm.value.newRole.trim()) {
    ElMessage.error('请输入新角色名称')
    return
  }

  ElMessage.info('批量修改角色功能开发中...')
  // TODO: 批量更新选中段落的角色
  batchRoleForm.value.visible = false
}

// 段落操作方法
const generateSegmentAudio = async (segmentId: number) => {
  ElMessage.info('生成音频功能开发中...')
  // TODO: 调用TTS API生成音频
}

const addSegmentAfter = (index: number) => {
  ElMessage.info('添加段落功能开发中...')
  // TODO: 在指定位置添加新段落
}

const deleteSegment = async (segmentId: number) => {
  const confirmed = await ElMessageBox.confirm('确定要删除这个段落吗？', '确认删除', {
    type: 'warning'
  })
  if (confirmed) {
    ElMessage.info('删除段落功能开发中...')
    // TODO: 删除段落
  }
}

const shortenTranslation = async (segmentId: number) => {
  ElMessage.info('翻译缩短功能开发中...')
  // TODO: 调用LLM缩短翻译
}

const lengthenTranslation = async (segmentId: number) => {
  ElMessage.info('翻译加长功能开发中...')
  // TODO: 调用LLM加长翻译
}

const handleSettingsClose = () => {
  showProjectSettings.value = false
}

const saveProjectSettings = async () => {
  try {
    const traceId = logger.startTrace('保存项目设置', {
      projectId: props.projectId,
      projectName: project.value?.name
    })

    logger.traceLog(traceId, 'info', '开始保存项目设置', 'ProjectDetail', {
      projectId: props.projectId
    })

    const response = await api.patch(`/projects/${props.projectId}/`, {
      name: projectSettings.value.name,
      description: projectSettings.value.description,
      source_lang: projectSettings.value.source_lang,
      target_lang: projectSettings.value.target_lang,
      voice_mappings: projectSettings.value.voice_mappings,
      custom_vocabulary: projectSettings.value.custom_vocabulary
    })

    ElMessage.success('项目设置保存成功')
    logger.traceLog(traceId, 'success', '项目设置保存成功', 'ProjectDetail', {
      projectId: props.projectId
    })
    logger.endTrace(traceId, 'success', '项目设置保存完成')

    showProjectSettings.value = false
    loadProject()
  } catch (error) {
    ElMessage.error('保存失败')
    logger.addLog('error', `项目设置保存失败: ${error}`, 'ProjectDetail', {
      projectId: props.projectId
    })
    console.error('Save project settings error:', error)
  }
}

// 视频和音频事件处理方法
const onVideoTimeUpdate = (time: number) => {
  currentPlayTime.value = time
  logger.addLog('debug', `视频播放时间更新: ${time}s`, 'VideoPlayer')
}

const onAudioTimeUpdate = (time: number) => {
  currentPlayTime.value = time
  logger.addLog('debug', `音频播放时间更新: ${time}s`, 'AudioTrack')
}

// 视频可见性控制
const onOriginalVideoVisibilityChange = (visible: boolean) => {
  isVideoVisible.value.original = visible
  logger.addLog('info', `原始视频${visible ? '显示' : '隐藏'}`, 'ProjectDetail')
}

const onTranslatedVideoVisibilityChange = (visible: boolean) => {
  isVideoVisible.value.translated = visible
  logger.addLog('info', `翻译视频${visible ? '显示' : '隐藏'}`, 'ProjectDetail')
}

// 音频可见性控制
const onTranslatedAudioVisibilityChange = (visible: boolean) => {
  isAudioVisible.value.translated = visible
  logger.addLog('info', `翻译音频${visible ? '显示' : '隐藏'}`, 'ProjectDetail')
}

const onOriginalAudioVisibilityChange = (visible: boolean) => {
  isAudioVisible.value.original = visible
  logger.addLog('info', `原始音频${visible ? '显示' : '隐藏'}`, 'ProjectDetail')
}

const onBackgroundAudioVisibilityChange = (visible: boolean) => {
  isAudioVisible.value.background = visible
  logger.addLog('info', `背景音频${visible ? '显示' : '隐藏'}`, 'ProjectDetail')
}

const onCompositeAudioVisibilityChange = (visible: boolean) => {
  isAudioVisible.value.composite = visible
  logger.addLog('info', `合成音频${visible ? '显示' : '隐藏'}`, 'ProjectDetail')
}

// 加载多媒体文件URL
const loadMediaUrls = () => {
  // 这里应该从后端API获取各种音频和视频文件的URL
  // 暂时使用项目中已有的音频URL作为示例
  if (lastConcatenatedAudioUrl.value) {
    translatedAudioUrl.value = lastConcatenatedAudioUrl.value
  }

  // TODO: 实现从后端获取其他音频文件URL的逻辑
  // originalAudioUrl.value = ...
  // backgroundAudioUrl.value = ...
  // compositeAudioUrl.value = ...
  // translatedVideoUrl.value = ...
}

onMounted(() => {
  loadProject()
  loadSegments()
  loadMediaUrls()
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
            <el-button @click="showProjectSettings = true" type="primary" size="small">
              <el-icon><Setting /></el-icon>
              项目设置
            </el-button>
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

    <!-- 数据集操作栏 -->
    <div style="margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 10px;">
      <!-- 批量操作 -->
      <el-button
        type="primary"
        @click="autoAssignRoles"
      >
        自动分配角色与情绪
      </el-button>

      <el-button
        type="warning"
        @click="showBatchRoleDialog"
        :disabled="selectedSegments.size === 0"
      >
        手工批量修改角色 ({{ selectedSegments.size }}个)
      </el-button>

      <!-- 传统批量操作 -->
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

      <!-- 导出操作 -->
      <el-button @click="exportSRT">
        <el-icon><Download /></el-icon>
        导出SRT
      </el-button>

      <el-button
        @click="concatenateAudio"
        type="success"
        :disabled="audioSegmentsCount === 0"
      >
        <el-icon><Download /></el-icon>
        拼接音频 ({{ audioSegmentsCount }}个)
      </el-button>

      <el-button
        @click="downloadAudio"
        type="primary"
        :disabled="!lastConcatenatedAudioUrl"
      >
        <el-icon><Download /></el-icon>
        下载完整音频
      </el-button>

      <el-button @click="loadSegments">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 视频预览区域 -->
    <div class="video-preview-section">
      <el-row :gutter="20">
        <el-col :span="12">
          <VideoPlayer
            title="原始视频预览"
            :video-url="project?.video_file_path"
            :default-visible="true"
            @visibility-change="onOriginalVideoVisibilityChange"
            @time-update="onVideoTimeUpdate"
          />
        </el-col>
        <el-col :span="12">
          <VideoPlayer
            title="翻译视频预览"
            :video-url="translatedVideoUrl"
            :default-visible="false"
            @visibility-change="onTranslatedVideoVisibilityChange"
            @time-update="onVideoTimeUpdate"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 数据集展示表格 -->
    <el-table
      :data="paginatedSegments"
      v-loading="segmentsLoading"
      stripe
      style="width: 100%"
      :row-class-name="({ row }) => {
        if (row.status === 'failed') return 'warning-row'
        if (editingSegments.has(row.id)) return 'editing-row'
        return ''
      }"
      @selection-change="handleSelectionChange"
    >
      <!-- 勾选框 -->
      <el-table-column type="selection" width="55" />

      <!-- 序号 -->
      <el-table-column prop="index" label="序号" width="80">
        <template #default="{ row }">
          <el-input
            v-if="editingSegments.has(row.id)"
            v-model="editingValues[row.id].index"
            size="small"
            type="number"
            @keydown="handleKeydown($event, row.id)"
          />
          <span v-else class="editable-text" @click="startEdit(row.id, row)">{{ row.index }}</span>
        </template>
      </el-table-column>

      <!-- 时间 -->
      <el-table-column label="时间" width="160">
        <template #default="{ row }">
          <div v-if="editingSegments.has(row.id)" style="display: flex; gap: 5px;">
            <el-input
              v-model="editingValues[row.id].start_time"
              size="small"
              type="number"
              step="0.1"
              style="width: 70px;"
              @keydown="handleKeydown($event, row.id)"
            />
            <span>-</span>
            <el-input
              v-model="editingValues[row.id].end_time"
              size="small"
              type="number"
              step="0.1"
              style="width: 70px;"
              @keydown="handleKeydown($event, row.id)"
            />
          </div>
          <span v-else class="editable-text" @click="startEdit(row.id, row)">{{ row.time_display }}</span>
        </template>
      </el-table-column>

      <!-- 说话人 -->
      <el-table-column prop="speaker" label="说话人" width="120">
        <template #default="{ row }">
          <el-input
            v-if="editingSegments.has(row.id)"
            v-model="editingValues[row.id].speaker"
            size="small"
            @keydown="handleKeydown($event, row.id)"
          />
          <span v-else class="editable-text" @click="startEdit(row.id, row)">{{ row.speaker }}</span>
        </template>
      </el-table-column>

      <!-- 原文本 -->
      <el-table-column prop="original_text" label="原文本" min-width="200">
        <template #default="{ row }">
          <el-input
            v-if="editingSegments.has(row.id)"
            v-model="editingValues[row.id].original_text"
            type="textarea"
            :rows="2"
            size="small"
            @keydown="handleKeydown($event, row.id)"
          />
          <div v-else class="editable-text text-content" @click="startEdit(row.id, row)">
            {{ row.original_text }}
          </div>
        </template>
      </el-table-column>

      <!-- 翻译文本 -->
      <el-table-column prop="translated_text" label="翻译文本" min-width="200">
        <template #default="{ row }">
          <el-input
            v-if="editingSegments.has(row.id)"
            v-model="editingValues[row.id].translated_text"
            type="textarea"
            :rows="2"
            size="small"
            @keydown="handleKeydown($event, row.id)"
          />
          <div v-else-if="row.translated_text" class="editable-text text-content" @click="startEdit(row.id, row)">
            {{ row.translated_text }}
          </div>
          <span v-else style="color: #999;">未翻译</span>
        </template>
      </el-table-column>

      <!-- 翻译音频 -->
      <el-table-column label="翻译音频" width="100">
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

      <!-- voice_id -->
      <el-table-column prop="voice_id" label="音色ID" width="120">
        <template #default="{ row }">
          <el-input
            v-if="editingSegments.has(row.id)"
            v-model="editingValues[row.id].voice_id"
            size="small"
            @keydown="handleKeydown($event, row.id)"
          />
          <span v-else class="editable-text" @click="startEdit(row.id, row)">{{ row.voice_id || '-' }}</span>
        </template>
      </el-table-column>

      <!-- 情绪参数 -->
      <el-table-column prop="emotion" label="情绪" width="100">
        <template #default="{ row }">
          <el-select
            v-if="editingSegments.has(row.id)"
            v-model="editingValues[row.id].emotion"
            size="small"
            @keydown="handleKeydown($event, row.id)"
          >
            <el-option label="自动" value="auto" />
            <el-option label="高兴" value="happy" />
            <el-option label="悲伤" value="sad" />
            <el-option label="愤怒" value="angry" />
            <el-option label="恐惧" value="fearful" />
            <el-option label="厌恶" value="disgusted" />
            <el-option label="惊讶" value="surprised" />
            <el-option label="平静" value="calm" />
          </el-select>
          <span v-else class="editable-text" @click="startEdit(row.id, row)">{{ row.emotion || 'auto' }}</span>
        </template>
      </el-table-column>

      <!-- 语速参数 -->
      <el-table-column prop="speed" label="语速" width="80">
        <template #default="{ row }">
          <el-input-number
            v-if="editingSegments.has(row.id)"
            v-model="editingValues[row.id].speed"
            size="small"
            :min="0.5"
            :max="2.0"
            :step="0.1"
            @keydown="handleKeydown($event, row.id)"
          />
          <span v-else class="editable-text" @click="startEdit(row.id, row)">{{ row.speed || 1.0 }}</span>
        </template>
      </el-table-column>

      <!-- ratio参数 -->
      <el-table-column prop="ratio" label="比例" width="80">
        <template #default="{ row }">
          <span :style="{ color: row.ratio > 1 ? '#f56c6c' : '#67c23a' }">
            {{ row.ratio ? row.ratio.toFixed(2) : '-' }}
          </span>
        </template>
      </el-table-column>

      <!-- 操作按钮 -->
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <div v-if="editingSegments.has(row.id)" class="edit-actions">
            <el-button size="small" type="primary" @click="saveEdit(row.id)">保存</el-button>
            <el-button size="small" @click="cancelEdit(row.id)">取消</el-button>
          </div>
          <div v-else class="segment-actions" style="display: flex; gap: 4px; flex-wrap: wrap;">
            <el-button size="small" @click="generateSegmentAudio(row.id)" type="primary">生成</el-button>
            <el-button size="small" @click="addSegmentAfter(row.index)" type="success">添加</el-button>
            <el-button size="small" @click="deleteSegment(row.id)" type="danger">删除</el-button>
            <el-button size="small" @click="shortenTranslation(row.id)" type="warning">缩短</el-button>
            <el-button size="small" @click="lengthenTranslation(row.id)" type="info">加长</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div style="margin-top: 20px; text-align: center;">
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="segments.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 音频轨道区域 -->
    <div class="audio-tracks-section">
      <h3 style="margin-bottom: 20px; color: #303133;">音频轨道</h3>

      <AudioTrack
        title="翻译音频预览"
        :audio-url="translatedAudioUrl"
        :default-visible="true"
        color="#409eff"
        @visibility-change="onTranslatedAudioVisibilityChange"
        @time-update="onAudioTimeUpdate"
      />

      <AudioTrack
        title="原始音频预览"
        :audio-url="originalAudioUrl"
        :default-visible="false"
        color="#67c23a"
        @visibility-change="onOriginalAudioVisibilityChange"
        @time-update="onAudioTimeUpdate"
      />

      <AudioTrack
        title="原始背景音预览"
        :audio-url="backgroundAudioUrl"
        :default-visible="false"
        color="#e6a23c"
        @visibility-change="onBackgroundAudioVisibilityChange"
        @time-update="onAudioTimeUpdate"
      />

      <AudioTrack
        title="翻译音频+背景音合成预览"
        :audio-url="compositeAudioUrl"
        :default-visible="false"
        color="#f56c6c"
        @visibility-change="onCompositeAudioVisibilityChange"
        @time-update="onAudioTimeUpdate"
      />
    </div>

    <!-- 批量修改角色对话框 -->
    <el-dialog
      v-model="batchRoleForm.visible"
      title="批量修改角色"
      width="400px"
    >
      <el-form :model="batchRoleForm" label-width="100px">
        <el-form-item label="新角色名称">
          <el-input v-model="batchRoleForm.newRole" placeholder="如 SPEAKER_01" />
        </el-form-item>
        <el-form-item label="选中段落">
          <span>{{ batchRoleForm.selectedCount }} 个段落</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchRoleForm.visible = false">取消</el-button>
          <el-button type="primary" @click="executeBatchRoleChange">确认修改</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 项目设置对话框 -->
    <el-dialog
      v-model="showProjectSettings"
      title="项目设置"
      width="80%"
      :before-close="handleSettingsClose"
    >
      <el-tabs type="border-card">
        <el-tab-pane label="基本设置" name="basic">
          <el-form :model="projectSettings" label-width="120px" size="default">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="项目名称">
                  <el-input v-model="projectSettings.name" placeholder="请输入项目名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="项目描述">
                  <el-input v-model="projectSettings.description" placeholder="请输入项目描述" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="源语言">
                  <el-select v-model="projectSettings.source_lang" style="width: 100%">
                    <el-option label="中文" value="zh" />
                    <el-option label="英语" value="en" />
                    <el-option label="日语" value="ja" />
                    <el-option label="韩语" value="ko" />
                    <el-option label="法语" value="fr" />
                    <el-option label="德语" value="de" />
                    <el-option label="西班牙语" value="es" />
                    <el-option label="俄语" value="ru" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="目标语言">
                  <el-select v-model="projectSettings.target_lang" style="width: 100%">
                    <el-option label="中文" value="zh" />
                    <el-option label="英语" value="en" />
                    <el-option label="日语" value="ja" />
                    <el-option label="韩语" value="ko" />
                    <el-option label="法语" value="fr" />
                    <el-option label="德语" value="de" />
                    <el-option label="西班牙语" value="es" />
                    <el-option label="俄语" value="ru" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="音色配置" name="voice">
          <div class="voice-config">
            <div class="voice-header">
              <h3>角色音色映射</h3>
              <el-button type="primary" @click="addVoiceMapping" size="small">
                添加音色配置
              </el-button>
            </div>

            <el-table :data="projectSettings.voice_mappings" border style="width: 100%">
              <el-table-column prop="speaker" label="说话人" width="200">
                <template #default="{ row, $index }">
                  <el-input v-model="row.speaker" placeholder="如 SPEAKER_00" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="voice_id" label="音色ID" width="300">
                <template #default="{ row, $index }">
                  <el-input v-model="row.voice_id" placeholder="如 ai_her_04" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row, $index }">
                  <el-button type="danger" @click="removeVoiceMapping($index)" size="small">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="专有词表" name="vocabulary">
          <div class="vocabulary-config">
            <div class="vocabulary-header">
              <h3>自定义词汇翻译</h3>
              <el-button type="primary" @click="addVocabularyItem" size="small">
                添加词汇
              </el-button>
            </div>

            <el-table :data="projectSettings.custom_vocabulary" border style="width: 100%">
              <el-table-column prop="词汇" label="原文词汇" width="250">
                <template #default="{ row, $index }">
                  <el-input v-model="row.词汇" placeholder="如：北京" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="译文" label="指定翻译" width="250">
                <template #default="{ row, $index }">
                  <el-input v-model="row.译文" placeholder="如：Beijing" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row, $index }">
                  <el-button type="danger" @click="removeVocabularyItem($index)" size="small">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div style="margin-top: 20px;">
              <h4>批量导入</h4>
              <el-input
                v-model="vocabularyBatchText"
                type="textarea"
                :rows="5"
                placeholder="每行格式：原文,译文&#10;例如：&#10;北京,Beijing&#10;上海,Shanghai&#10;苹果公司,Apple Inc."
              />
              <el-button @click="importVocabularyBatch" type="success" style="margin-top: 10px;">
                批量导入
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showProjectSettings = false">取消</el-button>
          <el-button type="primary" @click="saveProjectSettings">保存设置</el-button>
        </span>
      </template>
    </el-dialog>
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

/* 编辑模式下的行样式 */
:deep(.editing-row) {
  background-color: #f0f9ff !important;
  border-left: 3px solid #409eff;
}

/* 可编辑区域样式 */
.editable-text {
  cursor: pointer;
  padding: 8px;
  border: 1px solid transparent;
  border-radius: 4px;
  transition: all 0.2s;
}

.editable-text:hover {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
}

/* 编辑按钮组样式 */
.edit-actions {
  display: flex;
  gap: 4px;
}

.normal-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* 数据集表格样式 */
.text-content {
  max-width: 200px;
  word-break: break-all;
  line-height: 1.4;
}

.segment-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.segment-actions .el-button {
  margin: 0;
}

/* 音频播放器样式 */
.audio-player {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 分页样式 */
.el-pagination {
  justify-content: center;
}

/* 项目设置对话框样式 */
.voice-config, .vocabulary-config {
  width: 100%;
}

.voice-header, .vocabulary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.voice-header h3, .vocabulary-header h3 {
  margin: 0;
  color: #303133;
}

:deep(.el-dialog) {
  margin-top: 5vh !important;
}

:deep(.el-dialog__body) {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

:deep(.el-tabs__content) {
  padding: 20px 0;
}

:deep(.el-table) {
  margin-bottom: 20px;
}

:deep(.el-input-number) {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 视频预览区域样式 */
.video-preview-section {
  margin: 20px 0;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

/* 音频轨道区域样式 */
.audio-tracks-section {
  margin: 30px 0;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.audio-tracks-section h3 {
  margin: 0 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #409eff;
  color: #303133;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .video-preview-section .el-row {
    flex-direction: column;
  }

  .video-preview-section .el-col {
    width: 100% !important;
    margin-bottom: 15px;
  }
}

@media (max-width: 768px) {
  .video-preview-section,
  .audio-tracks-section {
    margin: 15px 0;
    padding: 15px;
  }
}
</style>