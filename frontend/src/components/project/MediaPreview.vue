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
          ref="videoPlayerRef"
          v-if="currentMediaUrl"
          :title="getCurrentMediaLabel()"
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
        <div v-if="currentMediaUrl" class="audio-player-wrapper">
          <!-- 基础音频播放器 -->
          <BasicAudioPlayer
            ref="simplePlayerRef"
            :key="`${selectedMedia}-${props.audioKey}`"
            :audio-url="currentMediaUrl"
            @time-update="handleAudioTimeUpdate"
            @duration-change="handleAudioDurationChange"
          />

          <!-- 波形图 - 仅在翻译音频模式下显示 -->
          <div v-if="selectedMedia === 'translated_audio'" class="waveform-wrapper">
            <AudioWaveform
              :audio-url="currentMediaUrl"
              :current-time="audioCurrentTime"
              :duration="audioDuration"
            />
          </div>
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
import { computed, ref, watch, watchEffect, nextTick, onMounted } from 'vue'
import { VideoCamera, Microphone, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VideoPlayer from '../VideoPlayer.vue'
import BasicAudioPlayer from '../audio/BasicAudioPlayer.vue'
import AudioWaveform from '../audio/AudioWaveform.vue'

// 动态获取后端基础URL用于媒体文件
const getBackendBaseUrl = () => {
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  const port = hostname === 'localhost' || hostname === '127.0.0.1' ? ':5172' : ':5172'
  return `${protocol}//${hostname}${port}`
}

const BACKEND_BASE_URL = getBackendBaseUrl()

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

// 解析时间字符串为秒数
const parseTimeToSeconds = (timeStr: string | number): number => {
  if (typeof timeStr === 'number') return timeStr
  if (!timeStr) return 0

  // 如果是 HH:MM:SS,mmm 格式 (SRT格式)
  const srtMatch = timeStr.toString().match(/^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/)
  if (srtMatch) {
    const [, hours, minutes, seconds, milliseconds] = srtMatch
    return parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds) + parseInt(milliseconds) / 1000
  }

  // 如果是数字字符串，直接解析
  const numValue = parseFloat(timeStr.toString())
  return isNaN(numValue) ? 0 : numValue
}


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
      url: props.project?.video_url ? `${BACKEND_BASE_URL}${props.project.video_url}` : null,
      available: !!props.project?.video_url,
      priority: 2,
      type: 'video'
    },
    {
      key: 'original_audio',
      label: '原始音频（人声）',
      url: props.project?.audio_url ? `${BACKEND_BASE_URL}${props.project.audio_url}` : null,
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
      url: props.project?.background_audio_url ? `${BACKEND_BASE_URL}${props.project.background_audio_url}` : null,
      available: !!props.project?.background_audio_url,
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

// 监听concatenatedAudioUrl和audioKey变化，强制更新音频
watch([() => props.concatenatedAudioUrl, () => props.audioKey], ([newUrl, newKey]) => {
  if (selectedMedia.value === 'translated_audio' && newUrl) {
    // audioKey变化会触发组件重新创建，清除缓存的跳转请求
    pendingSeekTime.value = null
  }
})

// 当前媒体信息
const currentMedia = computed(() => {
  return mediaOptions.value.find(option => option.key === selectedMedia.value) || null
})

const currentMediaUrl = computed(() => {
  const url = currentMedia.value?.url
  if (!url) return null

  // 为翻译音频添加时间戳来绕过浏览器缓存
  if (selectedMedia.value === 'translated_audio' && props.audioKey) {
    const separator = url.includes('?') ? '&' : '?'
    return `${url}${separator}t=${props.audioKey}`
  }

  return url
})
const isVideoType = computed(() => currentMedia.value?.type === 'video')

// 音频播放相关状态
const videoPlayerRef = ref()
const simplePlayerRef = ref()
const currentTime = ref(0)
const audioDuration = ref(0)
const audioCurrentTime = ref(0)

// 计算翻译后的段落数据
const translatedSegments = computed(() => {
  return props.segments.filter(segment => segment.translated_audio_url)
})

// 事件处理函数
const handleMediaChange = (value: string) => {
  selectedMedia.value = value
}

const handleVideoSeek = (time: number) => {
  // 更新当前时间
  currentTime.value = time
  // 触发时间更新事件，让父组件知道时间已更改
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


// 组件挂载时初始化
onMounted(() => {
  // 初始化项目数据
  initializeDefaultMedia()
})

// 音频播放器事件处理
const handleAudioTimeUpdate = (time: number) => {
  audioCurrentTime.value = time
  currentTime.value = time
  emit('timeUpdate', time)
}

const handleAudioDurationChange = (duration: number) => {
  audioDuration.value = duration
}

// 独立播放器事件处理（保持兼容性）
const handleSimplePlayerTimeUpdate = (time: number) => {
  // 同步时间状态
  currentTime.value = time
  // 同步时间到父组件
  emit('timeUpdate', time)
}

const handleSimplePlayerSeek = (time: number) => {
  // 同步时间状态
  currentTime.value = time
  // 处理独立播放器的跳转事件
  emit('timeUpdate', time)
}

// 监听simplePlayerRef的变化，执行缓存的跳转
watch(() => simplePlayerRef.value, (newRef) => {
  if (newRef && pendingSeekTime.value !== null) {
    nextTick(() => {
      if (simplePlayerRef.value && pendingSeekTime.value !== null) {
        simplePlayerRef.value.seekTo(pendingSeekTime.value)
        pendingSeekTime.value = null
      }
    })
  }
})


// 缓存的跳转请求
const pendingSeekTime = ref<number | null>(null)

// 段落跳转函数
const seekToSegmentStart = (segment: Segment) => {
  const startTimeInSeconds = parseTimeToSeconds(segment.start_time)

  // 如果是视频类型，更新视频位置
  if (isVideoType.value && videoPlayerRef.value?.seekTo) {
    videoPlayerRef.value.seekTo(startTimeInSeconds)
  }
  // 如果是音频类型，使用独立播放器跳转
  else if (!isVideoType.value) {
    if (simplePlayerRef.value) {
      simplePlayerRef.value.seekTo(startTimeInSeconds)
      pendingSeekTime.value = null // 清除缓存
    } else if (currentMediaUrl.value) {
      pendingSeekTime.value = startTimeInSeconds
    }
  }

  // 触发时间更新事件
  emit('timeUpdate', startTimeInSeconds)
}

// 暴露方法给父组件
defineExpose({
  seekToSegmentStart
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

/* 音频播放器容器 */
.audio-player-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

/* 波形图容器 */
.waveform-wrapper {
  background: white;
  border-radius: 6px;
  padding: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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