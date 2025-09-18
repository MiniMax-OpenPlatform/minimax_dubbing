import { ref } from 'vue'
import api from '../utils/api'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import type { Segment } from './useProjectData'

export function useAudioOperations(projectId: number) {
  const batchTtsLoading = ref(false)
  const concatenatedAudioUrl = ref<string | null>(null)
  const audioKey = ref(0)

  // 批量TTS
  const batchTts = async () => {
    try {
      const result = await ElMessageBox.confirm(
        '确定要对选中的段落进行批量TTS处理吗？这可能需要一些时间。',
        '批量TTS确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      if (result === 'confirm') {
        batchTtsLoading.value = true
        const response = await api.post(`/projects/${projectId}/segments/batch_tts/`)

        ElMessage.success('批量TTS处理完成')
        console.log('批量TTS完成', { projectId })

        audioKey.value++
        return response.data
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('批量TTS失败', error)
        ElMessage.error('批量TTS处理失败')
        throw error
      }
    } finally {
      batchTtsLoading.value = false
    }
  }

  // 单个段落TTS
  const singleTts = async (segment: Segment) => {
    try {
      const response = await api.post(`/projects/${projectId}/segments/${segment.id}/tts/`)
      ElMessage.success(`段落 ${segment.index} TTS处理完成`)
      audioKey.value++
      return response.data
    } catch (error) {
      console.error('TTS处理失败', error)
      ElMessage.error('TTS处理失败')
      throw error
    }
  }

  // 合成音频
  const concatenateAudio = async () => {
    try {
      const loadingInstance = ElLoading.service({
        lock: true,
        text: '正在合成音频...',
        background: 'rgba(0, 0, 0, 0.7)'
      })

      const response = await api.post(`/projects/${projectId}/concatenate_audio/`)
      concatenatedAudioUrl.value = response.data.audio_url
      audioKey.value++

      ElMessage.success('音频合成完成')
      console.log('音频合成完成', { audioUrl: response.data.audio_url })

      loadingInstance.close()
      return response.data
    } catch (error) {
      console.error('音频合成失败', error)
      ElMessage.error('音频合成失败')
      throw error
    }
  }

  // 播放音频
  const playAudio = (audioUrl: string) => {
    if (!audioUrl) {
      ElMessage.warning('没有可播放的音频')
      return
    }

    try {
      const audio = new Audio(audioUrl)
      audio.play().catch(() => {
        ElMessage.error('音频播放失败')
      })
    } catch (error) {
      ElMessage.error('音频播放失败')
    }
  }

  // 下载音频
  const downloadAudio = (audioUrl: string, filename?: string) => {
    if (!audioUrl) {
      ElMessage.warning('没有可下载的音频')
      return
    }

    try {
      const link = document.createElement('a')
      link.href = audioUrl
      link.download = filename || 'audio.mp3'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      ElMessage.error('音频下载失败')
    }
  }

  // 批量音频操作
  const batchAudioOperations = {
    // 批量TTS选中的段落
    batchTtsSelected: async (selectedSegments: Segment[]) => {
      if (selectedSegments.length === 0) {
        ElMessage.warning('请先选择要处理的段落')
        return
      }

      const translatedCount = selectedSegments.filter(s => s.translated_text).length
      if (translatedCount === 0) {
        ElMessage.warning('所选段落中没有翻译文本')
        return
      }

      try {
        const result = await ElMessageBox.confirm(
          `确定要对选中的 ${translatedCount} 个已翻译段落进行TTS处理吗？`,
          '批量TTS确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )

        if (result === 'confirm') {
          batchTtsLoading.value = true
          const segmentIds = selectedSegments
            .filter(s => s.translated_text)
            .map(s => s.id)

          const response = await api.post(`/projects/${projectId}/segments/batch_tts/`, {
            segment_ids: segmentIds
          })

          ElMessage.success(`批量TTS处理完成，处理了 ${translatedCount} 个段落`)
          audioKey.value++
          return response.data
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量TTS失败', error)
          ElMessage.error('批量TTS处理失败')
          throw error
        }
      } finally {
        batchTtsLoading.value = false
      }
    },

    // 导出选中段落的音频
    exportSelectedAudio: async (selectedSegments: Segment[]) => {
      const audioSegments = selectedSegments.filter(s => s.translated_audio_url)
      if (audioSegments.length === 0) {
        ElMessage.warning('所选段落中没有可导出的音频')
        return
      }

      try {
        const loadingInstance = ElLoading.service({
          lock: true,
          text: '正在导出音频...',
          background: 'rgba(0, 0, 0, 0.7)'
        })

        const response = await api.post(`/projects/${projectId}/export_audio/`, {
          segment_ids: audioSegments.map(s => s.id)
        })

        // 下载文件
        downloadAudio(response.data.audio_url, `project_${projectId}_selected.mp3`)
        ElMessage.success(`成功导出 ${audioSegments.length} 个段落的音频`)

        loadingInstance.close()
        return response.data
      } catch (error) {
        console.error('音频导出失败', error)
        ElMessage.error('音频导出失败')
        throw error
      }
    }
  }

  return {
    // 状态
    batchTtsLoading,
    concatenatedAudioUrl,
    audioKey,

    // 方法
    batchTts,
    singleTts,
    concatenateAudio,
    playAudio,
    downloadAudio,

    // 批量操作
    batchAudioOperations
  }
}