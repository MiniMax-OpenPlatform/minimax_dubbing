<template>
  <div class="media-preview-container">
    <!-- 左侧：原始媒体预览 -->
    <div class="original-media-section">
      <h3 class="section-title">原始媒体</h3>

      <!-- 原始视频预览 -->
      <div class="media-track">
        <div class="track-header">
          <h4>原始视频预览</h4>
          <div class="track-controls">
            <el-switch v-model="showOriginalVideo" size="small" />
            <el-button v-if="project?.video_url && showOriginalVideo" size="small" type="primary">
              <el-icon><Download /></el-icon>下载
            </el-button>
          </div>
        </div>
        <div v-if="showOriginalVideo" class="track-content">
          <VideoPlayer
            v-if="project?.video_url"
            :video-url="project.video_url"
            @seek="handleVideoSeek"
          />
          <div v-else class="media-placeholder">
            <el-icon><VideoCamera /></el-icon>
            <p>暂无视频文件</p>
          </div>
        </div>
      </div>

      <!-- 原始音频预览 -->
      <div class="media-track">
        <div class="track-header">
          <h4>原始音频预览</h4>
          <div class="track-controls">
            <el-switch v-model="showOriginalAudio" size="small" />
            <el-button v-if="project?.audio_url && showOriginalAudio" size="small" type="primary">
              <el-icon><Download /></el-icon>下载
            </el-button>
          </div>
        </div>
        <div v-if="showOriginalAudio" class="track-content">
          <AudioTrack
            v-if="project?.audio_url"
            :key="`original-${project.id}`"
            title="原始音频"
            :audio-url="project.audio_url"
            :segments="segments"
            track-type="original"
            :default-visible="true"
            @segment-click="$emit('segmentClick', $event)"
            @time-update="$emit('timeUpdate', $event)"
          />
          <div v-else class="no-audio-placeholder">
            <p>暂无音频文件</p>
          </div>
        </div>
      </div>

      <!-- 原始背景音预览 -->
      <div class="media-track">
        <div class="track-header">
          <h4>原始背景音预览</h4>
          <div class="track-controls">
            <el-switch v-model="showOriginalBg" size="small" />
            <el-button v-if="project?.background_audio_url && showOriginalBg" size="small" type="primary">
              <el-icon><Download /></el-icon>下载
            </el-button>
          </div>
        </div>
        <div v-if="showOriginalBg" class="track-content">
          <div class="no-audio-placeholder">
            <p>暂无背景音文件</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：翻译媒体预览 -->
    <div class="translated-media-section">
      <h3 class="section-title">翻译媒体</h3>

      <!-- 翻译视频预览 -->
      <div class="media-track">
        <div class="track-header">
          <h4>翻译视频预览</h4>
          <div class="track-controls">
            <el-switch v-model="showTranslatedVideo" size="small" />
          </div>
        </div>
        <div v-if="showTranslatedVideo" class="track-content">
          <div class="media-placeholder">
            <el-icon><VideoCamera /></el-icon>
            <p>翻译后的视频将在这里显示</p>
          </div>
        </div>
      </div>

      <!-- 翻译音频预览 -->
      <div class="media-track">
        <div class="track-header">
          <h4>翻译音频预览</h4>
          <div class="track-controls">
            <el-switch v-model="showTranslatedAudio" size="small" />
            <el-button v-if="concatenatedAudioUrl && showTranslatedAudio" size="small" type="primary">
              <el-icon><Download /></el-icon>下载
            </el-button>
          </div>
        </div>
        <div v-if="showTranslatedAudio" class="track-content">
          <AudioTrack
            :key="`translated-${project?.id || 0}-${audioKey}`"
            title="翻译音频"
            :audio-url="concatenatedAudioUrl"
            :segments="translatedSegments"
            track-type="translated"
            :default-visible="true"
            @segment-click="$emit('segmentClick', $event)"
            @time-update="$emit('timeUpdate', $event)"
          />
        </div>
      </div>

      <!-- 翻译音频+背景音合成预览 -->
      <div class="media-track">
        <div class="track-header">
          <h4>翻译音频+背景音合成预览</h4>
          <div class="track-controls">
            <el-switch v-model="showMixedAudio" size="small" />
            <el-button v-if="finalMixedAudioUrl && showMixedAudio" size="small" type="primary">
              <el-icon><Download /></el-icon>下载
            </el-button>
          </div>
        </div>
        <div v-if="showMixedAudio" class="track-content">
          <div class="no-audio-placeholder">
            <p>暂无合成音频文件</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { VideoCamera, Download } from '@element-plus/icons-vue'
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

// 获取最终混音音频URL
const finalMixedAudioUrl = computed(() => {
  return props.finalMixedAudioUrl
})

// 显示/隐藏状态
const showOriginalVideo = ref(false)
const showOriginalAudio = ref(false)
const showOriginalBg = ref(false)
const showTranslatedVideo = ref(false)
const showTranslatedAudio = ref(false)
const showMixedAudio = ref(false)

const handleVideoSeek = (time: number) => {
  // 处理视频跳转，可以同步音频播放位置
  // 这里可以添加视频和音频同步的逻辑
}
</script>

<style scoped>
.media-preview-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.original-media-section,
.translated-media-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 2px solid #e4e7ed;
  text-align: center;
}

.original-media-section .section-title {
  color: #409eff;
  border-bottom-color: #409eff;
}

.translated-media-section .section-title {
  color: #67c23a;
  border-bottom-color: #67c23a;
}

.media-placeholder {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  color: #909399;
  font-size: 14px;
  gap: 8px;
}

.media-placeholder .el-icon {
  font-size: 32px;
}

@media (max-width: 1200px) {
  .media-preview-container {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .section-title {
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .media-preview-container {
    padding: 16px;
    gap: 16px;
  }

  .section-title {
    font-size: 14px;
    margin-bottom: 12px;
  }

  .media-placeholder {
    height: 150px;
    font-size: 12px;
  }

  .media-placeholder .el-icon {
    font-size: 24px;
  }
}

.media-track {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  margin-bottom: 12px;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
}

.track-header h4 {
  margin: 0;
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.track-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.track-content {
  padding: 16px;
}

.no-audio-placeholder {
  text-align: center;
  padding: 20px;
  color: #909399;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>