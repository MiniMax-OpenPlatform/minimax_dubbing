import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../utils/api'

interface Segment {
  id: number
  index: number
  status: string
  original_text: string
  translated_text: string
  voice_id: string
  emotion: string
  speed: number
  [key: string]: any
}

interface BatchOperation {
  type: string
  segmentIds: number[]
  data?: any
  progress?: number
  status?: 'pending' | 'running' | 'completed' | 'failed'
}

export function useSegmentBatch(projectId: number) {
  const batchOperations = ref<Map<string, BatchOperation>>(new Map())
  const isAnyBatchRunning = ref(false)

  // 批量翻译
  const batchTranslate = async (segments: Segment[]): Promise<boolean> => {
    const pendingSegments = segments.filter(s => s.status === 'pending')

    if (pendingSegments.length === 0) {
      ElMessage.warning('没有待翻译的段落')
      return false
    }

    try {
      await ElMessageBox.confirm(
        `确定要翻译选中的 ${pendingSegments.length} 个段落吗？`,
        '批量翻译确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        }
      )

      const operationId = `translate_${Date.now()}`
      const segmentIds = pendingSegments.map(s => s.id)

      // 创建批量操作记录
      batchOperations.value.set(operationId, {
        type: 'translate',
        segmentIds,
        status: 'running',
        progress: 0
      })

      isAnyBatchRunning.value = true

      // 更新段落状态
      pendingSegments.forEach(segment => {
        segment.status = 'translating'
      })

      // 调用API
      const response = await api.post(`/projects/${projectId}/batch_translate/`, {
        segment_ids: segmentIds
      })

      if (response.data.success) {
        ElMessage.success(`批量翻译已开始，共${pendingSegments.length}个段落`)

        // 启动进度监控
        monitorBatchProgress(operationId, 'translate', segmentIds)

        return true
      } else {
        throw new Error(response.data.error || '批量翻译启动失败')
      }

    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(`批量翻译失败: ${error.message}`)
        // 恢复段落状态
        pendingSegments.forEach(segment => {
          segment.status = 'pending'
        })
      }
      isAnyBatchRunning.value = false
      return false
    }
  }

  // 批量TTS
  const batchTTS = async (segments: Segment[]): Promise<boolean> => {
    const translatedSegments = segments.filter(s =>
      s.status === 'translated' && s.translated_text?.trim()
    )

    if (translatedSegments.length === 0) {
      ElMessage.warning('没有可生成TTS的段落（需要已翻译且有译文内容）')
      return false
    }

    try {
      await ElMessageBox.confirm(
        `确定要为选中的 ${translatedSegments.length} 个段落生成TTS吗？`,
        '批量TTS确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        }
      )

      const operationId = `tts_${Date.now()}`
      const segmentIds = translatedSegments.map(s => s.id)

      // 创建批量操作记录
      batchOperations.value.set(operationId, {
        type: 'tts',
        segmentIds,
        status: 'running',
        progress: 0
      })

      isAnyBatchRunning.value = true

      // 更新段落状态
      translatedSegments.forEach(segment => {
        segment.status = 'tts_processing'
      })

      // 调用API
      const response = await api.post(`/projects/${projectId}/batch_tts/`)

      if (response.data.success) {
        ElMessage.success(`批量TTS已开始，共${translatedSegments.length}个段落`)

        // 启动进度监控
        monitorBatchProgress(operationId, 'tts', segmentIds)

        return true
      } else {
        throw new Error(response.data.error || '批量TTS启动失败')
      }

    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(`批量TTS失败: ${error.message}`)
        // 恢复段落状态
        translatedSegments.forEach(segment => {
          segment.status = 'translated'
        })
      }
      isAnyBatchRunning.value = false
      return false
    }
  }

  // 批量更新属性
  const batchUpdateProperty = async (
    segments: Segment[],
    property: string,
    value: any
  ): Promise<boolean> => {
    if (segments.length === 0) {
      ElMessage.warning('请先选择要更新的段落')
      return false
    }

    try {
      const propertyLabels: Record<string, string> = {
        voice_id: '音色',
        emotion: '情感',
        speed: '语速',
        speaker: '说话人'
      }

      const label = propertyLabels[property] || property

      await ElMessageBox.confirm(
        `确定要将选中的 ${segments.length} 个段落的${label}统一设置为"${value}"吗？`,
        `批量设置${label}`,
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        }
      )

      const segmentIds = segments.map(s => s.id)

      // 调用API
      const response = await api.post(`/projects/${projectId}/segments/batch_update/`, {
        segment_ids: segmentIds,
        [property]: value
      })

      if (response.data.success) {
        // 立即更新本地数据
        segments.forEach(segment => {
          segment[property] = value
          // 如果修改了语音相关设置，需要重新生成TTS
          if (['voice_id', 'emotion', 'speed'].includes(property) && segment.status === 'completed') {
            segment.status = 'translated'
            segment.translated_audio_url = ''
            segment.t_tts_duration = 0
            segment.ratio = 0
          }
        })

        ElMessage.success(`批量设置${label}成功，共更新${segments.length}个段落`)
        return true
      } else {
        throw new Error(response.data.error || '批量更新失败')
      }

    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(`批量设置失败: ${error.message}`)
      }
      return false
    }
  }

  // 批量删除
  const batchDelete = async (segments: Segment[]): Promise<boolean> => {
    if (segments.length === 0) {
      ElMessage.warning('请先选择要删除的段落')
      return false
    }

    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${segments.length} 个段落吗？此操作不可恢复！`,
        '批量删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      const segmentIds = segments.map(s => s.id)

      // 调用API
      const response = await api.post(`/projects/${projectId}/segments/batch_delete/`, {
        segment_ids: segmentIds
      })

      if (response.data.success) {
        ElMessage.success(`批量删除成功，共删除${segments.length}个段落`)
        return true
      } else {
        throw new Error(response.data.error || '批量删除失败')
      }

    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(`批量删除失败: ${error.message}`)
      }
      return false
    }
  }

  // 批量复制
  const batchDuplicate = async (segments: Segment[]): Promise<boolean> => {
    if (segments.length === 0) {
      ElMessage.warning('请先选择要复制的段落')
      return false
    }

    try {
      await ElMessageBox.confirm(
        `确定要复制选中的 ${segments.length} 个段落吗？`,
        '批量复制确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        }
      )

      const segmentData = segments.map(segment => ({
        ...segment,
        id: undefined,
        index: segment.index + 0.1,
        status: 'pending',
        translated_audio_url: '',
        t_tts_duration: 0,
        ratio: 0
      }))

      // 调用API
      const response = await api.post(`/projects/${projectId}/segments/batch_create/`, {
        segments: segmentData
      })

      if (response.data.success) {
        ElMessage.success(`批量复制成功，共复制${segments.length}个段落`)
        return true
      } else {
        throw new Error(response.data.error || '批量复制失败')
      }

    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(`批量复制失败: ${error.message}`)
      }
      return false
    }
  }

  // 监控批量操作进度
  const monitorBatchProgress = async (
    operationId: string,
    type: string,
    segmentIds: number[]
  ) => {
    const operation = batchOperations.value.get(operationId)
    if (!operation) return

    const checkProgress = async () => {
      try {
        const response = await api.get(`/projects/${projectId}/segments/`, {
          params: { ids: segmentIds.join(',') }
        })

        const segments = response.data.results || response.data
        const targetStatus = type === 'translate' ? 'translated' : 'completed'
        const processingStatus = type === 'translate' ? 'translating' : 'tts_processing'

        const completed = segments.filter((s: Segment) => s.status === targetStatus).length
        const stillProcessing = segments.some((s: Segment) => s.status === processingStatus)

        // 更新进度
        operation.progress = Math.round((completed / segmentIds.length) * 100)

        if (!stillProcessing) {
          // 操作完成
          operation.status = 'completed'
          operation.progress = 100

          const failed = segments.filter((s: Segment) => s.status === 'failed').length
          const success = completed

          ElMessage.success(
            `批量${type === 'translate' ? '翻译' : 'TTS'}完成！成功: ${success}个，失败: ${failed}个`
          )

          batchOperations.value.delete(operationId)
          checkIfAnyBatchRunning()
          return
        }

        // 继续监控
        setTimeout(checkProgress, 2000)

      } catch (error) {
        console.error('检查批量操作进度失败:', error)
        operation.status = 'failed'
        batchOperations.value.delete(operationId)
        checkIfAnyBatchRunning()
      }
    }

    checkProgress()
  }

  // 检查是否有批量操作在运行
  const checkIfAnyBatchRunning = () => {
    isAnyBatchRunning.value = Array.from(batchOperations.value.values())
      .some(op => op.status === 'running')
  }

  // 取消批量操作
  const cancelBatchOperation = async (operationId: string): Promise<boolean> => {
    const operation = batchOperations.value.get(operationId)
    if (!operation) return false

    try {
      await ElMessageBox.confirm(
        '确定要取消这个批量操作吗？',
        '取消操作确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '返回',
          type: 'warning'
        }
      )

      // 调用API取消操作
      await api.post(`/projects/${projectId}/cancel_batch_operation/`, {
        operation_id: operationId
      })

      operation.status = 'failed'
      batchOperations.value.delete(operationId)
      checkIfAnyBatchRunning()

      ElMessage.info('批量操作已取消')
      return true

    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error('取消操作失败')
      }
      return false
    }
  }

  // 获取批量操作状态
  const getBatchOperationStatus = (operationId: string) => {
    return batchOperations.value.get(operationId)
  }

  // 获取所有正在运行的批量操作
  const getRunningOperations = () => {
    return Array.from(batchOperations.value.entries())
      .filter(([_, op]) => op.status === 'running')
      .map(([id, op]) => ({ id, ...op }))
  }

  return {
    batchOperations,
    isAnyBatchRunning,
    batchTranslate,
    batchTTS,
    batchUpdateProperty,
    batchDelete,
    batchDuplicate,
    cancelBatchOperation,
    getBatchOperationStatus,
    getRunningOperations
  }
}