<template>
  <div class="project-detail-container">
    <!-- 媒体预览 -->
    <MediaPreview
      :project="project"
      :segments="segments"
      :concatenated-audio-url="concatenatedAudioUrl"
      :audio-key="audioKey"
      @segment-click="handleSegmentClick"
      @time-update="handleTimeUpdate"
    />

    <!-- 段落数据表格 -->
    <SegmentTable
      :segments="segments"
      :table-height="600"
      :batch-tts-loading="batchTtsLoading"
      @update-segment="updateSegment"
      @batch-tts="batchTts"
      @row-click="handleSegmentClick"
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 导入子组件
import MediaPreview from './MediaPreview.vue'
import SegmentTable from './SegmentTable.vue'
import ProjectSettings from './ProjectSettings.vue'

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
</script>

<style scoped>
.project-detail-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background-color: #f5f7fa;
}

@media (max-width: 768px) {
  .project-detail-container {
    padding: 12px;
  }
}
</style>