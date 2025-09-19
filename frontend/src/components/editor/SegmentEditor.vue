<template>
  <div class="segment-editor">
    <!-- 编辑器工具栏 -->
    <EditorToolbar
      :selected-count="selectedSegments.length"
      :total-count="segments.length"
      :batch-loading="batchLoading"
      @batch-translate="handleBatchTranslate"
      @batch-tts="handleBatchTts"
      @batch-edit="showBatchEditor = true"
      @export="handleExport"
      @filter="handleFilter"
      @clear-selection="clearSelection"
    />

    <!-- 编辑表格 -->
    <EditableTable
      :segments="filteredSegments"
      :selected-segments="selectedSegments"
      :editing-row="editingRowId"
      :validation-errors="validationErrors"
      @selection-change="handleSelectionChange"
      @row-edit="handleRowEdit"
      @row-save="handleRowSave"
      @row-cancel="handleRowCancel"
      @cell-change="handleCellChange"
      @play-audio="handlePlayAudio"
      @single-tts="handleSingleTts"
    />

    <!-- 批量编辑面板 -->
    <BatchEditPanel
      v-model="showBatchEditor"
      :selected-segments="selectedSegments"
      @apply="handleBatchApply"
    />

    <!-- 状态栏 -->
    <EditorStatusBar
      :segments="segments"
      :selected-count="selectedSegments.length"
      :has-unsaved-changes="hasUnsavedChanges"
      @save-all="handleSaveAll"
      @undo="handleUndo"
      @redo="handleRedo"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

// 导入子组件
import EditorToolbar from './EditorToolbar.vue'
import EditableTable from './EditableTable.vue'
import BatchEditPanel from './BatchEditPanel.vue'
import EditorStatusBar from './EditorStatusBar.vue'

// 导入编辑逻辑
import { useSegmentEditor } from '../../composables/useSegmentEditor'
import { useSegmentValidation } from '../../composables/useSegmentValidation'
import { useEditHistory } from '../../composables/useEditHistory'

interface Props {
  segments: Segment[]
  projectId: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'segments-updated': [segments: Segment[]]
  'batch-tts': [segmentIds: number[]]
  'export': [type: string, segments: Segment[]]
}>()

// 编辑状态管理
const {
  selectedSegments,
  editingRowId,
  batchLoading,
  filteredSegments,
  handleSelectionChange,
  handleRowEdit,
  handleRowSave,
  handleRowCancel,
  handleCellChange,
  clearSelection
} = useSegmentEditor(props.segments)

// 验证逻辑
const {
  validationErrors,
  validateSegment,
  validateBatch
} = useSegmentValidation()

// 编辑历史
const {
  hasUnsavedChanges,
  saveState,
  handleUndo,
  handleRedo
} = useEditHistory()

// 批量编辑面板状态
const showBatchEditor = ref(false)

// 批量操作处理
const handleBatchTranslate = async () => {
  if (selectedSegments.value.length === 0) {
    ElMessage.warning('请先选择要翻译的段落')
    return
  }

  batchLoading.value = true
  try {
    // 调用批量翻译API
    const segmentIds = selectedSegments.value.map(s => s.id)
    // TODO: 实现批量翻译逻辑
    ElMessage.success('批量翻译已开始')
  } catch (error) {
    ElMessage.error('批量翻译失败')
  } finally {
    batchLoading.value = false
  }
}

const handleBatchTts = () => {
  if (selectedSegments.value.length === 0) {
    ElMessage.warning('请先选择要生成TTS的段落')
    return
  }

  const segmentIds = selectedSegments.value.map(s => s.id)
  emit('batch-tts', segmentIds)
}

const handleBatchApply = (updates: Record<string, any>) => {
  const updatedSegments = selectedSegments.value.map(segment => ({
    ...segment,
    ...updates
  }))

  // 保存编辑历史
  saveState(props.segments)

  // 应用批量更新
  emit('segments-updated', updatedSegments)

  ElMessage.success(`批量更新了 ${selectedSegments.value.length} 个段落`)
  showBatchEditor.value = false
}

const handleExport = (type: string) => {
  const segments = selectedSegments.value.length > 0
    ? selectedSegments.value
    : filteredSegments.value

  emit('export', type, segments)
}

const handleFilter = (filterOptions: any) => {
  // TODO: 实现筛选逻辑
}

const handlePlayAudio = (audioUrl: string) => {
  // TODO: 实现音频播放
}

const handleSingleTts = async (segment: Segment) => {
  if (!segment.translated_text) {
    ElMessage.warning('请先翻译该段落')
    return
  }

  try {
    // TODO: 实现单个TTS生成
    ElMessage.success('TTS生成成功')
  } catch (error) {
    ElMessage.error('TTS生成失败')
  }
}

const handleSaveAll = () => {
  // TODO: 保存所有未保存的更改
  ElMessage.success('所有更改已保存')
}

// 监听segments变化
watch(() => props.segments, (newSegments) => {
  // 更新内部状态
}, { deep: true })
</script>

<style scoped>
.segment-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}
</style>