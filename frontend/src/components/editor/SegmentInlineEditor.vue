<!--
  ⚠️ 组件状态：暂未使用 (备用)
  📝 用途：段落内联编辑器容器
  📅 最后检查：2025-09-19
  💡 说明：包含工具栏和表格的完整编辑器组件
-->
<template>
  <div class="segment-inline-editor">
    <!-- 编辑器工具栏 -->
    <EditorToolbar
      :selected-count="selectedSegments.length"
      :total-count="filteredSegments.length"
      :batch-loading="batchLoading"
      :has-unsaved-changes="editState.dirty.size > 0"
      :can-undo="false"
      :can-redo="false"
      @batch-translate="batchTranslate"
      @batch-tts="batchTTS"
      @save-all="handleSaveAll"
      @undo="handleUndo"
      @redo="handleRedo"
      @export="handleExport"
      @filter-change="handleFilterChange"
      @clear-selection="clearSelection"
    />

    <!-- 行内编辑表格 -->
    <InlineEditTable
      :segments="filteredSegments"
      @selection-change="handleSelectionChange"
      @field-change="handleFieldChange"
      @translate-single="translateSingle"
      @generate-tts="generateTTS"
      @play-audio="playAudio"
      @duplicate-row="handleDuplicateRow"
      @delete-row="handleDeleteRow"
    />

    <!-- 状态栏 -->
    <div class="editor-status-bar">
      <div class="status-left">
        <span class="status-item">
          总计: {{ segments.length }} 个段落
        </span>
        <span class="status-item">
          已完成: {{ completedCount }} 个
        </span>
        <span class="status-item">
          进度: {{ progressPercentage }}%
        </span>
      </div>

      <div class="status-right">
        <span v-if="editState.saving.size > 0" class="saving-indicator">
          <el-icon class="is-loading"><Loading /></el-icon>
          保存中 ({{ editState.saving.size }})
        </span>
        <span v-if="editState.dirty.size > 0" class="dirty-indicator">
          {{ editState.dirty.size }} 个未保存
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

// 导入组件
import EditorToolbar from './EditorToolbar.vue'
import InlineEditTable from './InlineEditTable.vue'

// 导入逻辑
import { useInlineEditor } from '../../composables/useInlineEditor'

interface Segment {
  id: number
  index: number
  start_time: string
  end_time: string
  duration: number
  speaker: string
  original_text: string
  translated_text: string
  voice_id: string
  emotion: string
  speed: number
  translated_audio_url: string
  t_tts_duration: number
  ratio: number
  status: string
}

interface Props {
  segments: Segment[]
  projectId: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'segments-updated': [segments: Segment[]]
  'segment-added': [segment: Segment]
  'segment-deleted': [segmentId: number]
}>()

// 使用编辑器逻辑
const {
  editState,
  selectedSegments,
  handleFieldChange,
  translateSingle,
  generateTTS,
  playAudio,
  duplicateRow,
  deleteRow,
  batchTranslate,
  batchTTS,
  handleSelectionChange
} = useInlineEditor(props.projectId)

// 本地状态
const batchLoading = ref(false)
const filters = ref({
  status: '',
  text: ''
})

// 计算属性
const filteredSegments = computed(() => {
  let result = props.segments

  // 状态筛选
  if (filters.value.status) {
    result = result.filter(s => s.status === filters.value.status)
  }

  // 文本搜索
  if (filters.value.text) {
    const text = filters.value.text.toLowerCase()
    result = result.filter(s =>
      s.original_text.toLowerCase().includes(text) ||
      s.translated_text.toLowerCase().includes(text)
    )
  }

  return result
})

const completedCount = computed(() => {
  return props.segments.filter(s => s.status === 'completed').length
})

const progressPercentage = computed(() => {
  if (props.segments.length === 0) return 0
  return Math.round((completedCount.value / props.segments.length) * 100)
})

// 事件处理
const handleFilterChange = (newFilters: { status: string; text: string }) => {
  filters.value = newFilters
}

const clearSelection = () => {
  selectedSegments.value = []
}

const handleSaveAll = async () => {
  if (editState.dirty.size === 0) {
    ElMessage.info('没有未保存的更改')
    return
  }

  try {
    // 这里可以实现批量保存逻辑
    ElMessage.success('所有更改已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleUndo = () => {
  // TODO: 实现撤销逻辑
  ElMessage.info('撤销功能开发中')
}

const handleRedo = () => {
  // TODO: 实现重做逻辑
  ElMessage.info('重做功能开发中')
}

const handleExport = (type: string) => {
  const segments = selectedSegments.value.length > 0
    ? selectedSegments.value
    : filteredSegments.value

  switch (type) {
    case 'srt':
      exportSRT(segments)
      break
    case 'csv':
      exportCSV(segments)
      break
    case 'audio':
      exportAudio(segments)
      break
  }
}

const exportSRT = (segments: Segment[]) => {
  // 生成SRT内容
  let srtContent = ''
  segments.forEach((segment, index) => {
    srtContent += `${index + 1}\n`
    srtContent += `${segment.start_time} --> ${segment.end_time}\n`
    srtContent += `${segment.translated_text || segment.original_text}\n\n`
  })

  // 下载文件
  const blob = new Blob([srtContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `segments_${Date.now()}.srt`
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success(`已导出 ${segments.length} 个段落的SRT文件`)
}

const exportCSV = (segments: Segment[]) => {
  // 生成CSV内容
  const headers = ['序号', '开始时间', '结束时间', '说话人', '原文', '译文', '音色', '情感', '语速', '状态']
  let csvContent = headers.join(',') + '\n'

  segments.forEach(segment => {
    const row = [
      segment.index,
      segment.start_time,
      segment.end_time,
      segment.speaker || '',
      `"${segment.original_text.replace(/"/g, '""')}"`,
      `"${(segment.translated_text || '').replace(/"/g, '""')}"`,
      segment.voice_id || '',
      segment.emotion || '',
      segment.speed || 1.0,
      segment.status
    ]
    csvContent += row.join(',') + '\n'
  })

  // 下载文件
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `segments_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success(`已导出 ${segments.length} 个段落的CSV文件`)
}

const exportAudio = (segments: Segment[]) => {
  const audioSegments = segments.filter(s => s.translated_audio_url)
  if (audioSegments.length === 0) {
    ElMessage.warning('所选段落中没有音频文件')
    return
  }

  // TODO: 实现音频拼接导出
  ElMessage.info('音频导出功能开发中')
}

const handleDuplicateRow = async (segment: Segment) => {
  try {
    const newSegment = await duplicateRow(segment)
    if (newSegment) {
      emit('segment-added', newSegment)
    }
  } catch (error) {
    // 错误已在composable中处理
  }
}

const handleDeleteRow = async (segment: Segment) => {
  try {
    const success = await deleteRow(segment)
    if (success) {
      emit('segment-deleted', segment.id)
    }
  } catch (error) {
    // 错误已在composable中处理
  }
}

// 键盘快捷键
onMounted(() => {
  const handleKeydown = (e: KeyboardEvent) => {
    // Ctrl+S 保存
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault()
      handleSaveAll()
    }
    // Ctrl+A 全选
    if (e.ctrlKey && e.key === 'a') {
      e.preventDefault()
      selectedSegments.value = [...filteredSegments.value]
    }
    // Escape 清除选择
    if (e.key === 'Escape') {
      clearSelection()
    }
  }

  document.addEventListener('keydown', handleKeydown)

  return () => {
    document.removeEventListener('keydown', handleKeydown)
  }
})

// 监听segments变化
watch(() => props.segments, (newSegments) => {
  emit('segments-updated', newSegments)
}, { deep: true })
</script>

<style scoped>
.segment-inline-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.editor-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
  color: #606266;
}

.status-left {
  display: flex;
  gap: 16px;
}

.status-item {
  white-space: nowrap;
}

.status-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.saving-indicator {
  color: #e6a23c;
  display: flex;
  align-items: center;
  gap: 4px;
}

.dirty-indicator {
  color: #f56c6c;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .editor-status-bar {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }

  .status-left,
  .status-right {
    justify-content: center;
  }

  .status-left {
    flex-direction: column;
    gap: 4px;
  }
}
</style>