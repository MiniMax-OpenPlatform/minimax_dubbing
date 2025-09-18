<template>
  <div class="audio-player">
    <div class="player-controls">
      <el-button
        :icon="isPlaying ? VideoPause : VideoPlay"
        :type="isPlaying ? 'warning' : 'primary'"
        size="small"
        circle
        @click="togglePlay"
        :disabled="!audioUrl"
      />

      <span class="time-display">
        {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
      </span>

      <el-slider
        v-model="progress"
        :disabled="!audioUrl"
        :show-tooltip="false"
        style="flex: 1; margin: 0 15px;"
        @change="handleProgressChange"
      />

      <el-button
        :icon="isMuted ? Mute : Microphone"
        size="small"
        circle
        @click="toggleMute"
        :disabled="!audioUrl"
      />

      <el-slider
        v-model="volume"
        :max="100"
        :show-tooltip="false"
        style="width: 80px;"
        @change="handleVolumeChange"
      />
    </div>

    <!-- 波形可视化区域 -->
    <div v-if="showWaveform" class="waveform-container">
      <canvas
        ref="waveformCanvas"
        :width="waveformWidth"
        :height="waveformHeight"
        @click="handleWaveformClick"
      />
    </div>

    <!-- 隐藏的audio元素 -->
    <audio
      ref="audioElement"
      :src="audioUrl"
      @loadedmetadata="handleLoadedMetadata"
      @timeupdate="handleTimeUpdate"
      @ended="handleEnded"
      @error="handleError"
      preload="metadata"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { VideoPlay, VideoPause, Microphone, Mute } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  audioUrl?: string
  showWaveform?: boolean
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  audioUrl: '',
  showWaveform: true,
  height: 60
})

const emit = defineEmits<{
  timeUpdate: [currentTime: number, duration: number]
  play: []
  pause: []
  ended: []
}>()

const audioElement = ref<HTMLAudioElement>()
const waveformCanvas = ref<HTMLCanvasElement>()

const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(80)
const isMuted = ref(false)
const progress = ref(0)

const waveformWidth = ref(800)
const waveformHeight = computed(() => props.height)
const waveformData = ref<Float32Array | null>(null)

// 格式化时间显示
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 播放/暂停切换
const togglePlay = () => {
  if (!audioElement.value || !props.audioUrl) return

  if (isPlaying.value) {
    audioElement.value.pause()
    emit('pause')
  } else {
    audioElement.value.play()
    emit('play')
  }
  isPlaying.value = !isPlaying.value
}

// 静音切换
const toggleMute = () => {
  if (!audioElement.value) return

  isMuted.value = !isMuted.value
  audioElement.value.muted = isMuted.value
}

// 音量调整
const handleVolumeChange = (newVolume: number) => {
  if (!audioElement.value) return

  audioElement.value.volume = newVolume / 100
  if (newVolume > 0 && isMuted.value) {
    isMuted.value = false
    audioElement.value.muted = false
  }
}

// 进度调整
const handleProgressChange = (newProgress: number) => {
  if (!audioElement.value || duration.value === 0) return

  const newTime = (newProgress / 100) * duration.value
  audioElement.value.currentTime = newTime
}

// 波形点击跳转
const handleWaveformClick = (event: MouseEvent) => {
  if (!audioElement.value || duration.value === 0) return

  const canvas = event.currentTarget as HTMLCanvasElement
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const clickRatio = x / canvas.width
  const newTime = clickRatio * duration.value

  audioElement.value.currentTime = newTime
}

// 音频事件处理
const handleLoadedMetadata = () => {
  if (!audioElement.value) return

  duration.value = audioElement.value.duration
  loadWaveformData()
}

const handleTimeUpdate = () => {
  if (!audioElement.value) return

  currentTime.value = audioElement.value.currentTime
  progress.value = duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0

  emit('timeUpdate', currentTime.value, duration.value)
}

const handleEnded = () => {
  isPlaying.value = false
  progress.value = 0
  currentTime.value = 0
  emit('ended')
}

const handleError = (error: Event) => {
  console.error('Audio playback error:', error)
  ElMessage.error('音频播放失败')
  isPlaying.value = false
}

// 加载波形数据
const loadWaveformData = async () => {
  if (!props.showWaveform || !props.audioUrl) return

  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const response = await fetch(props.audioUrl)
    const arrayBuffer = await response.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

    const channelData = audioBuffer.getChannelData(0)
    const samples = 1000 // 采样点数
    const blockSize = Math.floor(channelData.length / samples)
    const filteredData = new Float32Array(samples)

    for (let i = 0; i < samples; i++) {
      let sum = 0
      for (let j = 0; j < blockSize; j++) {
        sum += Math.abs(channelData[i * blockSize + j] || 0)
      }
      filteredData[i] = sum / blockSize
    }

    waveformData.value = filteredData
    drawWaveform()
  } catch (error) {
    console.warn('Failed to load waveform data:', error)
  }
}

// 绘制波形
const drawWaveform = () => {
  if (!waveformCanvas.value || !waveformData.value) return

  const canvas = waveformCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const width = canvas.width
  const height = canvas.height
  const data = waveformData.value
  const barWidth = width / data.length

  // 绘制波形
  ctx.fillStyle = '#409eff'
  for (let i = 0; i < data.length; i++) {
    const barHeight = (data[i] * height) * 0.8
    const x = i * barWidth
    const y = (height - barHeight) / 2

    ctx.fillRect(x, y, barWidth - 1, barHeight)
  }

  // 绘制播放进度
  if (duration.value > 0) {
    const progressX = (currentTime.value / duration.value) * width
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
    ctx.fillRect(0, 0, progressX, height)

    // 进度线
    ctx.strokeStyle = '#ff4757'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(progressX, 0)
    ctx.lineTo(progressX, height)
    ctx.stroke()
  }
}

// 监听时间更新重绘波形
watch([currentTime, waveformData], () => {
  if (props.showWaveform) {
    drawWaveform()
  }
})

// 监听音频URL变化
watch(() => props.audioUrl, (newUrl) => {
  if (newUrl && audioElement.value) {
    // 重置状态
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
    progress.value = 0
    waveformData.value = null

    // 加载新音频
    audioElement.value.load()
  }
})

// 初始化
onMounted(() => {
  if (audioElement.value) {
    audioElement.value.volume = volume.value / 100
  }

  // 设置canvas大小
  const updateCanvasSize = () => {
    if (waveformCanvas.value) {
      const container = waveformCanvas.value.parentElement
      if (container) {
        waveformWidth.value = container.clientWidth
      }
    }
  }

  updateCanvasSize()
  window.addEventListener('resize', updateCanvasSize)

  onUnmounted(() => {
    window.removeEventListener('resize', updateCanvasSize)
  })
})
</script>

<style scoped>
.audio-player {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.time-display {
  font-family: monospace;
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.waveform-container {
  width: 100%;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
}

.waveform-container canvas {
  display: block;
  width: 100%;
  cursor: pointer;
}
</style>