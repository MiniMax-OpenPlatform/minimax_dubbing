import { ref, computed } from 'vue'
import api from '../utils/api'
import { ElMessage } from 'element-plus'

export interface Project {
  id: number
  name: string
  source_lang: string
  target_lang: string
  status: string
  segment_count: number
  completed_segment_count: number
  progress_percentage: number
  video_url?: string
  audio_url?: string
  description?: string
  default_voice_id?: string
  default_emotion?: string
  default_speed?: number
  auto_align?: boolean
  skip_empty_segments?: boolean
}

export interface Segment {
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

export function useProjectData(projectId: number) {
  const project = ref<Project | null>(null)
  const segments = ref<Segment[]>([])
  const loading = ref(false)

  // 计算属性
  const isProjectLoaded = computed(() => !!project.value)
  const hasSegments = computed(() => segments.value.length > 0)
  const projectProgress = computed(() => project.value?.progress_percentage || 0)

  // 加载项目数据
  const loadProject = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/`)
      project.value = response.data
      console.log('项目数据加载完成:', response.data)
      return response.data
    } catch (error) {
      console.error('加载项目数据失败:', error)
      ElMessage.error('加载项目数据失败')
      throw error
    }
  }

  // 加载段落数据
  const loadSegments = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/segments/`)
      console.log('段落数据响应:', response.data)

      // 检查响应数据格式
      const segmentData = Array.isArray(response.data) ? response.data : response.data.results || []

      // 确保 segmentData 是数组
      if (!Array.isArray(segmentData)) {
        console.warn('段落数据不是数组格式:', segmentData)
        segments.value = []
        return []
      }

      segments.value = segmentData.map((segment: any) => ({
        ...segment
      }))
      console.log('段落数据加载完成:', segmentData.length, '个段落')
      return segments.value
    } catch (error) {
      console.error('加载段落数据失败:', error)
      ElMessage.error('加载段落数据失败')
      throw error
    }
  }

  // 刷新所有数据
  const refreshData = async () => {
    loading.value = true
    try {
      await Promise.all([
        loadProject(),
        loadSegments()
      ])
      console.log('项目数据刷新完成', { projectId })
    } catch (error) {
      console.error('刷新数据失败', error)
      ElMessage.error('刷新数据失败')
    } finally {
      loading.value = false
    }
  }

  // 更新项目信息
  const updateProject = async (updates: Partial<Project>) => {
    try {
      await api.patch(`/projects/${projectId}/`, updates)
      if (project.value) {
        project.value = { ...project.value, ...updates }
      }
      console.log('项目更新成功', updates)
      ElMessage.success('项目更新成功')
    } catch (error) {
      console.error('项目更新失败', error)
      ElMessage.error('项目更新失败')
      throw error
    }
  }

  // 更新段落
  const updateSegment = async (segment: Segment) => {
    try {
      await api.patch(`/projects/${projectId}/segments/${segment.id}/`, segment)

      // 更新本地数据
      const index = segments.value.findIndex(s => s.id === segment.id)
      if (index !== -1) {
        segments.value[index] = { ...segment }
      }

      console.log('段落更新成功', { segmentId: segment.id })
    } catch (error) {
      console.error('更新段落失败', error)
      ElMessage.error('更新段落失败')
      throw error
    }
  }

  return {
    // 状态
    project,
    segments,
    loading,

    // 计算属性
    isProjectLoaded,
    hasSegments,
    projectProgress,

    // 方法
    loadProject,
    loadSegments,
    refreshData,
    updateProject,
    updateSegment
  }
}