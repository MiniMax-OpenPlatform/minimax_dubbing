<template>
  <div class="basic-audio-player">
    <!-- 波形显示区域 -->
    <SimpleWaveform
      ref="waveformRef"
      :current-time="currentTime"
      :duration="duration"
      :is-playing="isPlaying"
      @seek="onWaveformSeek"
    />

    <!-- 纯原生HTML5音频播放器 -->
    <audio
      ref="audioRef"
      :src="audioUrl"
      controls
      preload="metadata"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @play="onPlay"
      @pause="onPause"
      style="width: 100%; margin-top: 8px;"
    ></audio>

    <!-- 状态显示 -->
    <div v-if="showStatus" class="status">
      当前时间: {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import SimpleWaveform from './SimpleWaveform.vue'

interface Props {
  audioUrl?: string
  showStatus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  audioUrl: '',
  showStatus: false
})

const emit = defineEmits<{
  'time-update': [time: number]
  'seek': [time: number]
}>()

const audioRef = ref<HTMLAudioElement>()
const waveformRef = ref()
const currentTime = ref(0)
const duration = ref(0)
const isPlaying = ref(false)

// 格式化时间
const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 音频元数据加载完成
const onLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration || 0

    // 通知波形组件生成波形数据
    if (waveformRef.value && props.audioUrl) {
      waveformRef.value.generateWaveformFor(props.audioUrl)
    }
  }
}

// 时间更新
const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    duration.value = audioRef.value.duration || 0
    emit('time-update', currentTime.value)
  }
}

// 播放状态变化
const onPlay = () => {
  isPlaying.value = true
}

const onPause = () => {
  isPlaying.value = false
}

// 波形点击跳转 - 只设置位置，不干预播放逻辑
const onWaveformSeek = (time: number) => {
  if (audioRef.value) {
    audioRef.value.currentTime = time
    emit('seek', time)
  }
}

// 监听URL变化
watch(() => props.audioUrl, (newUrl) => {
  if (audioRef.value && newUrl) {
    audioRef.value.load()
  }
})

// 暴露跳转方法
defineExpose({
  seekTo: (time: number) => {
    if (audioRef.value) {
      audioRef.value.currentTime = time
      emit('seek', time)
    }
  },
  getCurrentTime: () => currentTime.value,
  getDuration: () => duration.value
})
</script>

<style scoped>
.basic-audio-player {
  padding: 16px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.status {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
  text-align: center;
}
</style>