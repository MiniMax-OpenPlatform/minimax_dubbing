import { ref } from 'vue'
import api from '../utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Segment } from './useProjectData'

export function useSegmentOperations(projectId: number) {
  const selectedSegments = ref<Segment[]>([])

  // 选择段落
  const selectSegment = (segment: Segment, selected: boolean) => {
    if (selected) {
      if (!selectedSegments.value.find(s => s.id === segment.id)) {
        selectedSegments.value.push(segment)
      }
    } else {
      selectedSegments.value = selectedSegments.value.filter(s => s.id !== segment.id)
    }
  }

  // 清除选择
  const clearSelection = () => {
    selectedSegments.value = []
  }

  // 全选/取消全选
  const toggleSelectAll = (segments: Segment[], selectAll: boolean) => {
    if (selectAll) {
      selectedSegments.value = [...segments]
    } else {
      clearSelection()
    }
  }

  // 批量翻译
  const batchTranslate = async (segments?: Segment[]) => {
    const segmentsToTranslate = segments || selectedSegments.value
    const pendingSegments = segmentsToTranslate.filter(s => s.status === 'pending')

    if (pendingSegments.length === 0) {
      ElMessage.warning('没有待翻译的段落')
      return
    }

    try {
      const result = await ElMessageBox.confirm(
        `确定要翻译选中的 ${pendingSegments.length} 个段落吗？`,
        '批量翻译确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      if (result === 'confirm') {
        const response = await api.post(`/projects/${projectId}/batch_translate/`, {
          segment_ids: pendingSegments.map(s => s.id)
        })

        ElMessage.success(`批量翻译完成，处理了 ${pendingSegments.length} 个段落`)
        return response.data
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('批量翻译失败', error)
        ElMessage.error('批量翻译失败')
        throw error
      }
    }
  }

  // 批量设置语音参数
  const batchSetVoice = async (voiceId: string, segments?: Segment[]) => {
    const segmentsToUpdate = segments || selectedSegments.value
    if (segmentsToUpdate.length === 0) {
      ElMessage.warning('请先选择要设置的段落')
      return
    }

    try {
      const response = await api.post(`/projects/${projectId}/segments/batch_update/`, {
        segment_ids: segmentsToUpdate.map(s => s.id),
        updates: { voice_id: voiceId }
      })

      ElMessage.success(`成功为 ${segmentsToUpdate.length} 个段落设置音色`)
      return response.data
    } catch (error) {
      console.error('批量设置音色失败', error)
      ElMessage.error('批量设置音色失败')
      throw error
    }
  }

  const batchSetEmotion = async (emotion: string, segments?: Segment[]) => {
    const segmentsToUpdate = segments || selectedSegments.value
    if (segmentsToUpdate.length === 0) {
      ElMessage.warning('请先选择要设置的段落')
      return
    }

    try {
      const response = await api.post(`/projects/${projectId}/segments/batch_update/`, {
        segment_ids: segmentsToUpdate.map(s => s.id),
        updates: { emotion }
      })

      ElMessage.success(`成功为 ${segmentsToUpdate.length} 个段落设置情感`)
      return response.data
    } catch (error) {
      console.error('批量设置情感失败', error)
      ElMessage.error('批量设置情感失败')
      throw error
    }
  }

  const batchSetSpeed = async (speed: number, segments?: Segment[]) => {
    const segmentsToUpdate = segments || selectedSegments.value
    if (segmentsToUpdate.length === 0) {
      ElMessage.warning('请先选择要设置的段落')
      return
    }

    try {
      const response = await api.post(`/projects/${projectId}/segments/batch_update/`, {
        segment_ids: segmentsToUpdate.map(s => s.id),
        updates: { speed }
      })

      ElMessage.success(`成功为 ${segmentsToUpdate.length} 个段落设置语速`)
      return response.data
    } catch (error) {
      console.error('批量设置语速失败', error)
      ElMessage.error('批量设置语速失败')
      throw error
    }
  }

  const batchSetSpeaker = async (speaker: string, segments?: Segment[]) => {
    const segmentsToUpdate = segments || selectedSegments.value
    if (segmentsToUpdate.length === 0) {
      ElMessage.warning('请先选择要设置的段落')
      return
    }

    try {
      const response = await api.post(`/projects/${projectId}/segments/batch_update/`, {
        segment_ids: segmentsToUpdate.map(s => s.id),
        updates: { speaker }
      })

      ElMessage.success(`成功为 ${segmentsToUpdate.length} 个段落设置说话人`)
      return response.data
    } catch (error) {
      console.error('批量设置说话人失败', error)
      ElMessage.error('批量设置说话人失败')
      throw error
    }
  }

  // 批量删除
  const batchDelete = async (segments?: Segment[]) => {
    const segmentsToDelete = segments || selectedSegments.value
    if (segmentsToDelete.length === 0) {
      ElMessage.warning('请先选择要删除的段落')
      return
    }

    try {
      const result = await ElMessageBox.confirm(
        `确定要删除选中的 ${segmentsToDelete.length} 个段落吗？此操作不可撤销。`,
        '批量删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      if (result === 'confirm') {
        const response = await api.post(`/projects/${projectId}/segments/batch_delete/`, {
          segment_ids: segmentsToDelete.map(s => s.id)
        })

        ElMessage.success(`成功删除 ${segmentsToDelete.length} 个段落`)
        clearSelection()
        return response.data
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('批量删除失败', error)
        ElMessage.error('批量删除失败')
        throw error
      }
    }
  }

  // 导出操作
  const exportOperations = {
    // 导出SRT
    exportSrt: async (segments?: Segment[]) => {
      const segmentsToExport = segments || selectedSegments.value
      try {
        const response = await api.post(`/projects/${projectId}/export_srt/`, {
          segment_ids: segmentsToExport.length > 0 ? segmentsToExport.map(s => s.id) : undefined
        })

        // 下载文件
        const blob = new Blob([response.data], { type: 'text/plain;charset=utf-8' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `project_${projectId}.srt`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        ElMessage.success('SRT文件导出成功')
      } catch (error) {
        console.error('SRT导出失败', error)
        ElMessage.error('SRT导出失败')
        throw error
      }
    },

    // 导出CSV
    exportCsv: async (segments?: Segment[]) => {
      const segmentsToExport = segments || selectedSegments.value
      try {
        const response = await api.post(`/projects/${projectId}/export_csv/`, {
          segment_ids: segmentsToExport.length > 0 ? segmentsToExport.map(s => s.id) : undefined
        })

        // 下载文件
        const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `project_${projectId}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        ElMessage.success('CSV文件导出成功')
      } catch (error) {
        console.error('CSV导出失败', error)
        ElMessage.error('CSV导出失败')
        throw error
      }
    }
  }

  // 获取选择状态统计
  const getSelectionStats = () => {
    const stats = {
      total: selectedSegments.value.length,
      pending: 0,
      translated: 0,
      completed: 0,
      failed: 0,
      hasAudio: 0
    }

    selectedSegments.value.forEach(segment => {
      switch (segment.status) {
        case 'pending':
          stats.pending++
          break
        case 'translated':
          stats.translated++
          break
        case 'completed':
          stats.completed++
          break
        case 'failed':
          stats.failed++
          break
      }

      if (segment.translated_audio_url) {
        stats.hasAudio++
      }
    })

    return stats
  }

  return {
    // 状态
    selectedSegments,

    // 选择操作
    selectSegment,
    clearSelection,
    toggleSelectAll,

    // 批量操作
    batchTranslate,
    batchSetVoice,
    batchSetEmotion,
    batchSetSpeed,
    batchSetSpeaker,
    batchDelete,

    // 导出操作
    exportOperations,

    // 统计
    getSelectionStats
  }
}