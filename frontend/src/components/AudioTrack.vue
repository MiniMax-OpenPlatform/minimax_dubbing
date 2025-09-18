<template>
  <div class="audio-track-container">
    <div class="track-header">
      <h4>{{ title }}</h4>
      <div class="track-controls">
        <el-switch
          v-model="isVisible"
          :active-text="isVisible ? '显示' : '隐藏'"
          @change="$emit('visibility-change', isVisible)"
        />
        <el-button
          v-if="audioUrl && isVisible"
          @click="downloadAudio"
          type="primary"
          size="small"
        >
          <el-icon><Download /></el-icon>
          下载
        </el-button>
      </div>
    </div>

    <div v-if="isVisible" class="track-content">
      <div class="audio-wrapper">
        <!-- 音频播放器 -->
        <div class="audio-controls">
          <el-button-group>
            <el-button
              @click="togglePlay"
              :type="isPlaying ? 'danger' : 'primary'"
              :disabled="!audioUrl"
              size="small"
            >
              <el-icon>
                <VideoPlay v-if="!isPlaying" />
                <VideoPause v-else />
              </el-icon>
              {{ isPlaying ? '暂停' : '播放' }}
            </el-button>
            <el-button
              @click="stopAudio"
              :disabled="!audioUrl"
              size="small"
            >
              <el-icon><CircleClose /></el-icon>
              停止
            </el-button>
          </el-button-group>

          <div class="time-info">
            <span>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
          </div>

          <div class="volume-control">
            <el-icon><Microphone /></el-icon>
            <el-slider
              v-model="volume"
              :min="0"
              :max="100"
              :show-tooltip="false"
              @change="updateVolume"
              style="width: 80px; margin-left: 8px;"
            />
          </div>
        </div>

        <!-- 当没有音频时显示提示 -->
        <div v-if="!audioUrl" class="no-audio-notice">
          <el-text type="info" size="small">暂无音频文件，显示示例波形</el-text>
        </div>

        <!-- 波形分析加载状态 -->
        <div v-if="isAnalyzingWaveform" class="waveform-loading">
          <el-loading-spinner size="small" />
          <el-text type="primary" size="small">正在分析音频波形...</el-text>
        </div>

        <!-- 波形图区域 -->
        <div class="waveform-container" ref="waveformContainer">
          <canvas
            ref="waveformCanvas"
            class="waveform-canvas"
            @click="seekToPosition"
          ></canvas>

          <!-- 进度指示器 -->
          <div
            class="progress-indicator"
            :style="{ left: progressPercentage + '%' }"
          ></div>
        </div>

        <!-- 进度条 -->
        <div class="progress-bar">
          <el-slider
            v-model="progressValue"
            :min="0"
            :max="duration"
            :step="0.1"
            :show-tooltip="false"
            @change="seekTo"
            @input="onProgressInput"
          />
        </div>

        <!-- 隐藏的音频元素 -->
        <audio
          ref="audioRef"
          :src="audioUrl"
          preload="metadata"
          @loadedmetadata="onAudioLoaded"
          @timeupdate="onTimeUpdate"
          @ended="onAudioEnded"
          @loadstart="onLoadStart"
          @canplay="onCanPlay"
          @error="onAudioError"
        ></audio>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Download, VideoPlay, VideoPause, CircleClose, Microphone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 全局波形缓存（跨组件共享）
const globalWaveformCache = new Map<string, number[]>()

interface Props {
  title: string
  audioUrl?: string
  defaultVisible?: boolean
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultVisible: true,
  color: '#409eff'
})

const emit = defineEmits<{
  'visibility-change': [visible: boolean]
  'time-update': [time: number]
}>()

const audioRef = ref<HTMLAudioElement>()
const waveformCanvas = ref<HTMLCanvasElement>()
const waveformContainer = ref<HTMLDivElement>()
const isVisible = ref(props.defaultVisible)
const isPlaying = ref(false)
const duration = ref(0)
const currentTime = ref(0)
const progressValue = ref(0)
const volume = ref(80)
const waveformData = ref<number[]>([])
const retryCount = ref(0)
const maxRetries = 5
const isAnalyzingWaveform = ref(false)

const progressPercentage = computed(() => {
  return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
})

const onAudioLoaded = async () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
    audioRef.value.volume = volume.value / 100
    await generateWaveform()
  }
}

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    progressValue.value = currentTime.value
    emit('time-update', currentTime.value)
    drawWaveform()
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
    generateWaveform()
  }
}

const onAudioError = (event: Event) => {
  console.error('[AudioTrack] 音频加载错误:', props.title, event, props.audioUrl)
  ElMessage.error(`音频加载失败: ${props.title}`)
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
  if (!waveformContainer.value || !audioRef.value) return

  const rect = waveformContainer.value.getBoundingClientRect()
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

const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds)) return '00:00'

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

const downloadAudio = () => {
  if (!props.audioUrl) {
    ElMessage.error('音频文件不存在')
    return
  }

  try {
    const link = document.createElement('a')
    link.href = props.audioUrl
    link.download = `${props.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}.mp3`
    link.click()
    ElMessage.success('音频下载已开始')
  } catch (error) {
    ElMessage.error('下载失败')
    console.error('Download error:', error)
  }
}

// 生成波形数据（使用Web Audio API分析真实音频）
const generateWaveform = async () => {

  // 重置重试计数器
  retryCount.value = 0

  // 设置加载状态
  isAnalyzingWaveform.value = true

  // 如果没有音频URL，生成默认波形用于展示
  if (!props.audioUrl) {
    const sampleCount = 200
    const samples: number[] = []

    for (let i = 0; i < sampleCount; i++) {
      // 生成随机波形数据用于预览
      const amplitude = Math.random() * 0.8 + 0.2
      samples.push(amplitude)
    }

    waveformData.value = samples

    // 结束加载状态
    isAnalyzingWaveform.value = false

    await nextTick()
    drawWaveform()
    return
  }

  // 检查缓存
  if (globalWaveformCache.has(props.audioUrl)) {
    waveformData.value = globalWaveformCache.get(props.audioUrl)!
    isAnalyzingWaveform.value = false
    await nextTick()
    drawWaveform()
    return
  }

  // 使用Web Audio API分析真实音频文件
  try {

    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const response = await fetch(props.audioUrl)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const arrayBuffer = await response.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

    // 获取音频数据（使用第一个声道）
    const rawData = audioBuffer.getChannelData(0)
    const sampleCount = 200 // 波形条数
    const blockSize = Math.floor(rawData.length / sampleCount)
    const samples: number[] = []

    for (let i = 0; i < sampleCount; i++) {
      let sum = 0
      for (let j = 0; j < blockSize; j++) {
        sum += Math.abs(rawData[i * blockSize + j])
      }
      // 计算平均振幅并标准化到0-1范围
      const amplitude = (sum / blockSize)
      samples.push(Math.min(amplitude * 2, 1)) // 放大2倍但限制在1以内
    }

    waveformData.value = samples

    // 缓存波形数据
    globalWaveformCache.set(props.audioUrl, samples)

    // 关闭音频上下文以释放资源
    audioContext.close()

    // 结束加载状态
    isAnalyzingWaveform.value = false

    await nextTick()
    drawWaveform()

  } catch (error) {
    console.error('[AudioTrack] 音频波形分析失败:', props.title, error)

    // 分析失败时使用默认波形
    const sampleCount = 200
    const samples: number[] = []

    for (let i = 0; i < sampleCount; i++) {
      const amplitude = Math.random() * 0.4 + 0.1 // 更低的默认波形
      samples.push(amplitude)
    }

    waveformData.value = samples

    // 结束加载状态（即使失败）
    isAnalyzingWaveform.value = false

    await nextTick()
    drawWaveform()
  }
}

// 绘制波形图
const drawWaveform = () => {
  const canvas = waveformCanvas.value
  const container = waveformContainer.value

  if (!canvas || !container || waveformData.value.length === 0) {
    // 如果Canvas或容器不存在，且组件可见且未超过重试次数，稍后重试
    if (waveformData.value.length > 0 && (!canvas || !container) && isVisible.value && retryCount.value < maxRetries) {
      retryCount.value++
      setTimeout(() => {
        drawWaveform()
      }, 200 + retryCount.value * 100) // 递增延迟
    }
    return
  }

  const ctx = canvas.getContext('2d')
  if (!ctx) {
    return
  }

  // 设置canvas尺寸
  const containerWidth = container.clientWidth
  if (containerWidth > 0) {
    canvas.width = containerWidth
    canvas.height = 60
  } else {
    // 如果容器宽度为0，使用默认宽度
    canvas.width = 600
    canvas.height = 60
  }

  const width = canvas.width
  const height = canvas.height
  const barWidth = width / waveformData.value.length
  const progressPoint = (currentTime.value / duration.value) * width

  // 重置重试计数器（成功绘制）
  retryCount.value = 0

  // 清空画布
  ctx.clearRect(0, 0, width, height)

  // 绘制波形
  waveformData.value.forEach((amplitude, index) => {
    const x = index * barWidth
    const barHeight = amplitude * height * 0.8
    const y = (height - barHeight) / 2

    // 根据播放进度设置颜色
    if (x < progressPoint) {
      ctx.fillStyle = props.color // 已播放部分
    } else {
      ctx.fillStyle = '#e4e7ed' // 未播放部分
    }

    ctx.fillRect(x, y, barWidth - 1, barHeight)
  })
}

// 监听音频URL变化
watch(() => props.audioUrl, (newUrl, oldUrl) => {
  isPlaying.value = false
  currentTime.value = 0
  duration.value = 0
  progressValue.value = 0
  waveformData.value = []

  // 如果有新的URL，等待下一个tick后重新加载和分析
  if (newUrl && audioRef.value) {
    nextTick(() => {
      if (audioRef.value) {
        audioRef.value.load()
        // 重新生成波形数据
        generateWaveform()
      }
    })
  }
})

// 监听可见性变化，重新绘制波形
watch(isVisible, async (visible) => {
  // 重置重试计数器
  retryCount.value = 0

  if (visible && waveformData.value.length > 0) {
    await nextTick()
    drawWaveform()
  }
})

onMounted(() => {
  // 监听窗口大小变化，重新绘制波形
  window.addEventListener('resize', drawWaveform)

  // 如果没有音频URL，也生成默认波形用于测试
  if (!props.audioUrl) {
    // 使用更长的延迟确保DOM完全渲染
    setTimeout(() => {
      generateWaveform()
    }, 300 + Math.random() * 200) // 随机延迟避免同时执行
  }
})

// 暴露方法给父组件
defineExpose({
  play: togglePlay,
  pause: stopAudio,
  seekTo,
  audioElement: audioRef
})
</script>

<style scoped>
.audio-track-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  margin-bottom: 16px;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
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

.audio-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.audio-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.time-info {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

.volume-control {
  display: flex;
  align-items: center;
  color: #909399;
}

.waveform-container {
  position: relative;
  height: 60px;
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  overflow: hidden;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.progress-indicator {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #f56c6c;
  pointer-events: none;
  transition: left 0.1s ease;
}

.progress-bar {
  margin-top: 8px;
}

.no-audio-notice {
  text-align: center;
  padding: 8px;
  background: #f0f9ff;
  border: 1px dashed #409eff;
  border-radius: 4px;
  margin-bottom: 12px;
}

.waveform-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-bottom: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .track-header {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }

  .track-controls {
    justify-content: space-between;
  }

  .audio-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .volume-control {
    justify-content: center;
  }
}

:deep(.el-slider__runway) {
  height: 4px;
}

:deep(.el-slider__button) {
  width: 12px;
  height: 12px;
}
</style>