// 项目相关类型定义
export interface Project {
  id: number
  name: string
  source_lang: string
  target_lang: string
  status: string
  created_at: string
  segment_count: number
  completed_segment_count: number
  progress_percentage: number
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

export interface UploadForm {
  srt_file: File | null
  project_name: string
}

// 状态相关类型
export type ProjectStatus = 'draft' | 'processing' | 'completed' | 'failed'
export type SegmentStatus = 'pending' | 'translating' | 'translated' | 'tts_processing' | 'completed' | 'failed' | 'silent'