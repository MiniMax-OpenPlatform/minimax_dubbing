<template>
  <div class="media-preview-section">
    <!-- 原音频预览 -->
    <div class="media-container">
      <h4>原音频</h4>
      <div class="media-group">
        <VideoPlayer
          v-if="project?.video_url"
          :video-url="project.video_url"
          @seek="handleVideoSeek"
        />
        <div v-else class="media-placeholder">
          <p>暂无视频文件</p>
        </div>

        <div class="audio-tracks-group">
          <AudioTrack
            v-if="project?.audio_url"
            :key="`original-${project.id}`"
            title="原音频"
            :audio-url="project.audio_url"
            :segments="segments"
            track-type="original"
            @segment-click="$emit('segmentClick', $event)"
            @time-update="$emit('timeUpdate', $event)"
          />
          <div v-else class="media-placeholder">
            <p>暂无音频文件</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 翻译音频预览 -->
    <div class="media-container">
      <h4>翻译音频</h4>
      <div class="media-group">
        <div class="translated-video-placeholder">
          <p>翻译后的视频将在这里显示</p>
        </div>

        <div class="audio-tracks-group">
          <AudioTrack
            :key="`translated-${project?.id || 0}-${audioKey}`"
            title="翻译音频"
            :audio-url="concatenatedAudioUrl"
            :segments="translatedSegments"
            track-type="translated"
            @segment-click="$emit('segmentClick', $event)"
            @time-update="$emit('timeUpdate', $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VideoPlayer from '../VideoPlayer.vue'
import AudioTrack from '../AudioTrack.vue'

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
  video_url?: string
  audio_url?: string
  source_lang: string
  target_lang: string
  status: string
  segment_count: number
  completed_segment_count: number
  progress_percentage: number
  description?: string
}

const props = defineProps<{
  project: Project | null
  segments: Segment[]
  concatenatedAudioUrl: string | null
  audioKey: number
}>()

defineEmits<{
  segmentClick: [segment: Segment]
  timeUpdate: [time: number]
}>()

// 计算翻译后的段落数据
const translatedSegments = computed(() => {
  return props.segments.filter(segment => segment.translated_audio_url)
})

const handleVideoSeek = (time: number) => {
  // 处理视频跳转，可以同步音频播放位置
  // 这里可以添加视频和音频同步的逻辑
}
</script>

<style scoped>
.media-preview-section {
  margin-bottom: 20px;
}

.media-container {
  margin-bottom: 20px;
}

.media-container h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.media-group {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.audio-tracks-group {
  flex: 1;
  min-width: 0;
}

.media-placeholder,
.translated-video-placeholder {
  width: 400px;
  height: 225px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  color: #909399;
  font-size: 14px;
}

@media (max-width: 1200px) {
  .media-group {
    flex-direction: column;
    gap: 16px;
  }

  .media-placeholder,
  .translated-video-placeholder {
    width: 100%;
    max-width: 600px;
  }
}

@media (max-width: 768px) {
  .media-container h4 {
    font-size: 14px;
  }

  .media-placeholder,
  .translated-video-placeholder {
    height: 180px;
    font-size: 12px;
  }
}
</style>