<template>
  <div class="media-preview-compact">
    <!-- 顶部控制栏：下拉选择 + 操作按钮 -->
    <div class="control-bar">
      <el-select
        v-model="selectedMedia"
        placeholder="选择媒体类型"
        size="small"
        class="media-selector"
        @change="handleMediaChange"
      >
        <el-option
          v-for="option in mediaOptions"
          :key="option.key"
          :label="option.label"
          :value="option.key"
          :disabled="!option.available"
        >
          <span>{{ option.label }}</span>
          <span v-if="!option.available" class="disabled-hint">（暂无）</span>
        </el-option>
      </el-select>

      <div class="action-buttons">
        <span v-if="currentMediaUrl" class="status-text available">可播放</span>
        <span v-else class="status-text unavailable">暂无文件</span>
        <el-button v-if="currentMediaUrl" size="small" type="primary" @click="downloadMedia">
          <el-icon><Download /></el-icon>下载
        </el-button>
      </div>
    </div>

    <!-- 媒体播放区 -->
    <div class="media-player-area">
      <!-- 视频播放器 -->
      <div v-if="isVideoType" class="video-container">
        <VideoPlayer
          v-if="currentMediaUrl"
          :video-url="currentMediaUrl"
          @seek="handleVideoSeek"
        />
        <div v-else class="media-placeholder">
          <el-icon><VideoCamera /></el-icon>
          <p>{{ getPlaceholderText() }}</p>
        </div>
      </div>

      <!-- 音频播放器 -->
      <div v-else class="audio-container">
        <div v-if="currentMediaUrl" class="simple-audio-player">
          <!-- 音频播放控制器 -->
          <AudioController
            :is-playing="isPlaying"
            :has-audio="!!currentMediaUrl"
            :current-time="currentTime"
            :duration="duration"
            :volume="volume"
            @toggle-play="togglePlay"
            @stop="stopAudio"
            @volume-change="updateVolume"
          />

          <!-- 波形显示 -->
          <WaveformDisplay
            :waveform-data="waveformData"
            :current-time="currentTime"
            :duration="duration"
            :color="'#409eff'"
            :is-analyzing="isAnalyzingWaveform"
            @seek-to-position="seekToPosition"
          />

          <!-- 进度条 -->
          <ProgressBar
            :current-time="progressValue"
            :duration="duration"
            @seek-to="seekTo"
            @progress-input="onProgressInput"
          />

          <!-- 隐藏的音频元素 -->
          <audio
            ref="audioRef"
            :src="currentMediaUrl"
            preload="metadata"
            @loadedmetadata="onAudioLoaded"
            @timeupdate="onTimeUpdate"
            @ended="onAudioEnded"
            @loadstart="onLoadStart"
            @canplay="onCanPlay"
            @error="onAudioError"
          ></audio>
        </div>
        <div v-else class="media-placeholder">
          <el-icon><Microphone /></el-icon>
          <p>{{ getPlaceholderText() }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect, nextTick, onMounted } from 'vue'
import { VideoCamera, Microphone, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VideoPlayer from '../VideoPlayer.vue'
import AudioController from '../audio/AudioController.vue'
import WaveformDisplay from '../audio/WaveformDisplay.vue'
import ProgressBar from '../audio/ProgressBar.vue'
import { useAudioWaveform } from '../../composables/useAudioWaveform'

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
  finalMixedAudioUrl?: string | null
}>()

const emit = defineEmits<{
  segmentClick: [segment: Segment]
  timeUpdate: [time: number]
}>()

// 媒体选项定义
interface MediaOption {
  key: string
  label: string
  url: string | null
  available: boolean
  priority: number
  type: 'video' | 'audio'
}

// 计算媒体选项
const mediaOptions = computed<MediaOption[]>(() => {
  const options: MediaOption[] = [
    {
      key: 'translated_audio',
      label: '翻译音频',
      url: props.concatenatedAudioUrl,
      available: !!props.concatenatedAudioUrl,
      priority: 1,
      type: 'audio'
    },
    {
      key: 'original_video',
      label: '原始视频',
      url: props.project?.video_url || null,
      available: !!props.project?.video_url,
      priority: 2,
      type: 'video'
    },
    {
      key: 'original_audio',
      label: '原始音频',
      url: props.project?.audio_url || null,
      available: !!props.project?.audio_url,
      priority: 3,
      type: 'audio'
    },
    {
      key: 'translated_video',
      label: '翻译视频',
      url: null, // 暂时没有翻译视频
      available: false,
      priority: 4,
      type: 'video'
    },
    {
      key: 'background_audio',
      label: '背景音',
      url: null, // 暂时没有背景音
      available: false,
      priority: 5,
      type: 'audio'
    },
    {
      key: 'mixed_audio',
      label: '混合音频',
      url: props.finalMixedAudioUrl || null,
      available: !!props.finalMixedAudioUrl,
      priority: 6,
      type: 'audio'
    }
  ]

  // 按优先级排序，可用的在前
  return options.sort((a, b) => {
    if (a.available !== b.available) {
      return a.available ? -1 : 1
    }
    return a.priority - b.priority
  })
})

// 当前选中的媒体
const selectedMedia = ref<string>('')

// 初始化默认选择（选择第一个可用的媒体）
const initializeDefaultMedia = () => {
  const firstAvailable = mediaOptions.value.find(option => option.available)
  if (firstAvailable) {
    selectedMedia.value = firstAvailable.key
  }
}

// 监听媒体选项变化，自动初始化
watchEffect(() => {
  if (!selectedMedia.value || !mediaOptions.value.find(opt => opt.key === selectedMedia.value)?.available) {
    initializeDefaultMedia()
  }
})

// 当前媒体信息
const currentMedia = computed(() => {
  return mediaOptions.value.find(option => option.key === selectedMedia.value) || null
})

const currentMediaUrl = computed(() => currentMedia.value?.url || null)
const isVideoType = computed(() => currentMedia.value?.type === 'video')

// 音频播放相关状态
const audioRef = ref<HTMLAudioElement>()
const isPlaying = ref(false)
const duration = ref(0)
const currentTime = ref(0)
const progressValue = ref(0)
const volume = ref(80)

// 使用音频波形功能
const { waveformData, isAnalyzingWaveform, generateWaveform } = useAudioWaveform()

// 计算翻译后的段落数据
const translatedSegments = computed(() => {
  return props.segments.filter(segment => segment.translated_audio_url)
})

// 事件处理函数
const handleMediaChange = (value: string) => {
  selectedMedia.value = value
}

const handleVideoSeek = (time: number) => {
  emit('timeUpdate', time)
}

const downloadMedia = () => {
  if (currentMediaUrl.value) {
    const link = document.createElement('a')
    link.href = currentMediaUrl.value
    link.download = `${getCurrentMediaLabel()}.${isVideoType.value ? 'mp4' : 'mp3'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

// 音频播放相关函数
const onAudioLoaded = async () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
    audioRef.value.volume = volume.value / 100
    await generateWaveform(currentMediaUrl.value)
  }
}

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    progressValue.value = currentTime.value
    emit('timeUpdate', currentTime.value)
  }
}

const onAudioEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
  progressValue.value = 0
}

const onLoadStart = () => {
  // Audio loading started
}

const onCanPlay = () => {
  if (audioRef.value && duration.value === 0) {
    duration.value = audioRef.value.duration
    generateWaveform(currentMediaUrl.value)
  }
}

const onAudioError = (event: Event) => {
  console.error('[MediaPreview] 音频加载错误:', event, currentMediaUrl.value)
  ElMessage.error('音频加载失败')
}

const togglePlay = () => {
  if (!audioRef.value) return

  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

const stopAudio = () => {
  if (!audioRef.value) return

  audioRef.value.pause()
  audioRef.value.currentTime = 0
  isPlaying.value = false
  currentTime.value = 0
  progressValue.value = 0
}

const seekTo = (time: number) => {
  if (audioRef.value) {
    audioRef.value.currentTime = time
    currentTime.value = time
  }
}

const onProgressInput = (value: number) => {
  currentTime.value = value
}

const seekToPosition = (event: MouseEvent) => {
  if (!audioRef.value) return

  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percentage = x / rect.width
  const time = percentage * duration.value

  seekTo(time)
}

const updateVolume = (value: number) => {
  if (audioRef.value) {
    audioRef.value.volume = value / 100
  }
}

const getCurrentMediaLabel = () => {
  return currentMedia.value?.label || '未知媒体'
}

const getPlaceholderText = () => {
  if (!currentMedia.value) return '请选择媒体类型'
  return `暂无${currentMedia.value.label}文件`
}

const getSegmentsForMedia = () => {
  if (selectedMedia.value === 'translated_audio') {
    return translatedSegments.value
  }
  return props.segments
}

// 监听音频URL变化
watchEffect(() => {
  const newUrl = currentMediaUrl.value
  if (newUrl && !isVideoType.value) {
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
    progressValue.value = 0

    // 等待下一个tick后重新加载和分析
    nextTick(() => {
      if (audioRef.value) {
        audioRef.value.load()
        generateWaveform(newUrl)
      }
    })
  }
})

// 组件挂载时初始化
onMounted(() => {
  if (!currentMediaUrl.value && !isVideoType.value) {
    // 如果没有音频URL，生成默认波形用于测试
    setTimeout(() => {
      generateWaveform()
    }, 300)
  }
})
</script>

<style scoped>
.media-preview-compact {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

/* 顶部控制栏样式 */
.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  height: 30px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  gap: 12px;
}

.media-selector {
  width: 140px;
  flex-shrink: 0;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-buttons .el-button {
  padding: 4px 8px;
  height: 24px;
  font-size: 12px;
}

.status-text {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-text.available {
  color: #67c23a;
  background: #f0f9ff;
}

.status-text.unavailable {
  color: #909399;
  background: #f5f5f5;
}

.disabled-hint {
  color: #c0c4cc;
  font-size: 12px;
}

/* 媒体播放区样式 */
.media-player-area {
  flex: 1;
  padding: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}


.video-container,
.audio-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.simple-audio-player {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.media-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  color: #909399;
  font-size: 14px;
  gap: 12px;
  min-height: 200px;
}

.media-placeholder .el-icon {
  font-size: 32px;
}

.media-placeholder p {
  margin: 0;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-bar {
    flex-direction: column;
    height: auto;
    gap: 8px;
    padding: 8px;
  }

  .media-selector {
    width: 100%;
  }

  .action-buttons {
    width: 100%;
    justify-content: center;
  }
}
</style>