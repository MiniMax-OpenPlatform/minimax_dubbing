import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../utils/api'
import { useSegmentSelection } from './useSegmentSelection'
import { useSegmentValidation } from './useSegmentValidation'
import { useSegmentBatch } from './useSegmentBatch'

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

interface EditState {
  saving: Set<number>
  dirty: Set<number>
}

export function useInlineEditor(projectId: number) {
  const editState = reactive<EditState>({
    saving: new Set(),
    dirty: new Set()
  })

  // 使用其他composables
  const {
    selectedSegments,
    selectedCount,
    hasSelection,
    selectSegment,
    clearSelection,
    toggleSelectAll,
    isSelected,
    getSelectionStats
  } = useSegmentSelection()

  const {
    validateField,
    validateSegment,
    setFieldError,
    clearFieldError,
    hasSegmentErrors,
    validateForTranslation,
    validateForTTS
  } = useSegmentValidation()

  const {
    batchTranslate: batchTranslateOp,
    batchTTS: batchTTSOp,
    batchUpdateProperty,
    batchDelete,
    batchDuplicate,
    isAnyBatchRunning
  } = useSegmentBatch(projectId)

  // 防抖定时器
  let saveTimeouts = new Map<string, number>()

  // 字段变更处理
  const handleFieldChange = async (segment: Segment, field: string, value: any) => {
    // 清除之前的定时器
    const timeoutKey = `${segment.id}_${field}`
    if (saveTimeouts.has(timeoutKey)) {
      clearTimeout(saveTimeouts.get(timeoutKey))
    }

    // 实时验证
    const error = validateField(field, value)
    if (error) {
      setFieldError(segment.id, field, error)
      return
    } else {
      clearFieldError(segment.id, field)
    }

    // 标记为脏数据
    editState.dirty.add(segment.id)

    // 防抖保存
    const timeoutId = window.setTimeout(async () => {
      try {
        editState.saving.add(segment.id)

        await api.patch(`/projects/${projectId}/segments/${segment.id}/`, {
          [field]: value
        })

        editState.dirty.delete(segment.id)
      } catch (error: any) {
        ElMessage.error(`保存失败: ${error.message}`)
      } finally {
        editState.saving.delete(segment.id)
        saveTimeouts.delete(timeoutKey)
      }
    }, 800)

    saveTimeouts.set(timeoutKey, timeoutId)
  }

  // 单个翻译
  const translateSingle = async (segment: Segment) => {
    // 验证
    const validation = validateForTranslation([segment])
    if (!validation.valid) {
      ElMessage.error(validation.errors[0])
      return
    }

    try {
      segment.status = 'translating'

      const response = await api.post(`/projects/${projectId}/segments/${segment.id}/translate/`)

      if (response.data.success) {
        segment.translated_text = response.data.translated_text
        segment.status = 'translated'
        ElMessage.success('翻译完成')
      } else {
        throw new Error(response.data.error || '翻译失败')
      }
    } catch (error: any) {
      segment.status = 'pending'
      ElMessage.error(`翻译失败: ${error.message}`)
    }
  }

  // 生成TTS
  const generateTTS = async (segment: Segment) => {
    // 验证
    const validation = validateForTTS([segment])
    if (!validation.valid) {
      ElMessage.error(validation.errors[0])
      return
    }

    try {
      segment.status = 'tts_processing'

      const response = await api.post(`/projects/${projectId}/segments/${segment.id}/tts/`)

      if (response.data.success) {
        segment.translated_audio_url = response.data.audio_url
        segment.t_tts_duration = response.data.duration
        segment.ratio = response.data.ratio
        segment.status = 'completed'
        ElMessage.success('TTS生成完成')
      } else {
        throw new Error(response.data.error || 'TTS生成失败')
      }
    } catch (error: any) {
      segment.status = 'translated'
      ElMessage.error(`TTS生成失败: ${error.message}`)
    }
  }

  // 播放音频
  const playAudio = (segment: Segment) => {
    if (!segment.translated_audio_url) {
      ElMessage.warning('该段落没有音频文件')
      return
    }

    const audio = new Audio(segment.translated_audio_url)
    audio.play().catch(error => {
      ElMessage.error('音频播放失败')
      console.error('Audio play error:', error)
    })
  }

  // 复制段落
  const duplicateRow = async (segment: Segment): Promise<Segment | null> => {
    try {
      const newSegmentData = {
        ...segment,
        id: undefined,
        index: segment.index + 0.1,
        status: 'pending',
        translated_text: '',
        translated_audio_url: '',
        t_tts_duration: 0,
        ratio: 0
      }

      const response = await api.post(`/projects/${projectId}/segments/`, newSegmentData)

      if (response.data.id) {
        ElMessage.success('段落复制成功')
        return response.data
      } else {
        throw new Error('复制失败')
      }
    } catch (error: any) {
      ElMessage.error(`复制失败: ${error.message}`)
      return null
    }
  }

  // 删除段落
  const deleteRow = async (segment: Segment): Promise<boolean> => {
    try {
      await api.delete(`/projects/${projectId}/segments/${segment.id}/`)

      // 从选择中移除
      selectedSegments.value = selectedSegments.value.filter(s => s.id !== segment.id)

      ElMessage.success('段落删除成功')
      return true
    } catch (error: any) {
      ElMessage.error(`删除失败: ${error.message}`)
      return false
    }
  }

  // 批量翻译
  const batchTranslate = async () => {
    if (selectedSegments.value.length === 0) {
      ElMessage.warning('请先选择要翻译的段落')
      return
    }

    const success = await batchTranslateOp(selectedSegments.value)
    if (success) {
      clearSelection()
    }
  }

  // 批量TTS
  const batchTTS = async () => {
    if (selectedSegments.value.length === 0) {
      ElMessage.warning('请先选择要生成TTS的段落')
      return
    }

    const success = await batchTTSOp(selectedSegments.value)
    if (success) {
      clearSelection()
    }
  }

  // 选择变更处理
  const handleSelectionChange = (segments: Segment[]) => {
    selectedSegments.value = segments
  }

  // 批量更新属性
  const updateProperty = async (property: string, value: any) => {
    if (selectedSegments.value.length === 0) {
      ElMessage.warning('请先选择要更新的段落')
      return
    }

    return await batchUpdateProperty(selectedSegments.value, property, value)
  }

  // 批量删除选中
  const deleteSelected = async () => {
    if (selectedSegments.value.length === 0) {
      ElMessage.warning('请先选择要删除的段落')
      return
    }

    const success = await batchDelete(selectedSegments.value)
    if (success) {
      clearSelection()
    }
  }

  // 批量复制选中
  const duplicateSelected = async () => {
    if (selectedSegments.value.length === 0) {
      ElMessage.warning('请先选择要复制的段落')
      return
    }

    const success = await batchDuplicate(selectedSegments.value)
    if (success) {
      clearSelection()
    }
  }

  // 保存所有更改
  const saveAll = async () => {
    if (editState.dirty.size === 0) {
      ElMessage.info('没有未保存的更改')
      return
    }

    // 立即保存所有脏数据
    for (const timeoutId of saveTimeouts.values()) {
      clearTimeout(timeoutId)
    }
    saveTimeouts.clear()

    ElMessage.success('所有更改已保存')
    editState.dirty.clear()
  }

  // 计算属性
  const isDirty = computed(() => editState.dirty.size > 0)
  const isSaving = computed(() => editState.saving.size > 0)
  const hasErrors = computed(() => hasSegmentErrors)

  return {
    // 状态
    editState,
    selectedSegments,
    selectedCount,
    hasSelection,
    isDirty,
    isSaving,
    hasErrors,
    isAnyBatchRunning,

    // 选择操作
    selectSegment,
    clearSelection,
    toggleSelectAll,
    isSelected,
    getSelectionStats,

    // 编辑操作
    handleFieldChange,
    translateSingle,
    generateTTS,
    playAudio,
    duplicateRow,
    deleteRow,

    // 批量操作
    batchTranslate,
    batchTTS,
    updateProperty,
    deleteSelected,
    duplicateSelected,
    handleSelectionChange,

    // 保存操作
    saveAll
  }
}