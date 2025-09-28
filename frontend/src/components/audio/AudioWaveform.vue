<template>
  <div class="audio-waveform" :class="{ loaded: isLoaded }" ref="containerRef">
    <canvas
      ref="canvasRef"
      :width="canvasWidth"
      :height="canvasHeight"
      class="waveform-canvas"
    />
    <div
      v-if="isLoaded && duration > 0"
      class="progress-line"
      :style="{ left: progressPercent + '%' }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

interface Props {
  audioUrl: string | null
  currentTime?: number
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  currentTime: 0,
  duration: 0
})

// Refs
const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()

// State
const canvasWidth = ref(800)
const canvasHeight = ref(80)
const waveformData = ref<number[]>([])
const isLoaded = ref(false)
const resizeObserver = ref<ResizeObserver>()

// Computed
const progressPercent = computed(() => {
  if (!props.duration || props.duration === 0) return 0
  return Math.min((props.currentTime / props.duration) * 100, 100)
})

// 加载音频并分析波形数据
const loadAudioWaveform = async (url: string) => {
  if (!url) return

  try {
    isLoaded.value = false
    waveformData.value = []

    // 创建AudioContext
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()

    // 获取音频数据
    const response = await fetch(url)
    const arrayBuffer = await response.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

    // 提取波形数据
    const channelData = audioBuffer.getChannelData(0) // 使用第一个声道
    const samples = Math.min(canvasWidth.value, 2000) // 限制采样点数量
    const blockSize = Math.floor(channelData.length / samples)
    const waveData: number[] = []

    for (let i = 0; i < samples; i++) {
      let sum = 0
      for (let j = 0; j < blockSize; j++) {
        sum += Math.abs(channelData[i * blockSize + j] || 0)
      }
      waveData.push(sum / blockSize)
    }

    // 归一化数据
    const max = Math.max(...waveData)
    if (max > 0) {
      waveformData.value = waveData.map(val => val / max)
    } else {
      waveformData.value = new Array(samples).fill(0)
    }

    isLoaded.value = true

    // 关闭AudioContext以释放资源
    await audioContext.close()

    // 绘制波形
    await nextTick()
    drawWaveform()

  } catch (error) {
    console.error('音频波形加载失败:', error)
    // 生成静默波形作为fallback
    waveformData.value = new Array(canvasWidth.value).fill(0)
    isLoaded.value = true
    drawWaveform()
  }
}

// 绘制波形图
const drawWaveform = () => {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空画布
  ctx.clearRect(0, 0, canvasWidth.value, canvasHeight.value)

  if (waveformData.value.length === 0) return

  // 设置样式
  const barWidth = canvasWidth.value / waveformData.value.length
  const centerY = canvasHeight.value / 2

  // 绘制波形条
  waveformData.value.forEach((amplitude, index) => {
    const barHeight = amplitude * (canvasHeight.value * 0.8)
    const x = index * barWidth

    // 设置颜色 - 已播放部分和未播放部分用不同颜色
    const progress = (props.currentTime / Math.max(props.duration, 1)) * waveformData.value.length
    const isPlayed = index < progress

    ctx.fillStyle = isPlayed ? '#409eff' : '#e4e7ed'

    // 绘制上下对称的波形条
    ctx.fillRect(x, centerY - barHeight / 2, Math.max(barWidth - 1, 1), barHeight)
  })
}

// 处理容器尺寸变化
const handleResize = () => {
  const container = containerRef.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  canvasWidth.value = Math.floor(rect.width)

  nextTick(() => {
    drawWaveform()
  })
}

// 监听音频URL变化
watch(() => props.audioUrl, (newUrl) => {
  if (newUrl) {
    loadAudioWaveform(newUrl)
  } else {
    waveformData.value = []
    isLoaded.value = false
    drawWaveform()
  }
}, { immediate: true })

// 监听播放进度变化
watch(() => props.currentTime, () => {
  if (isLoaded.value) {
    drawWaveform()
  }
})

// 监听画布尺寸变化
watch([canvasWidth, canvasHeight], () => {
  nextTick(() => {
    drawWaveform()
  })
})

// 组件挂载
onMounted(() => {
  // 监听容器尺寸变化
  if (containerRef.value) {
    resizeObserver.value = new ResizeObserver(handleResize)
    resizeObserver.value.observe(containerRef.value)
    handleResize() // 初始化尺寸
  }
})

// 组件卸载
onUnmounted(() => {
  if (resizeObserver.value && containerRef.value) {
    resizeObserver.value.unobserve(containerRef.value)
  }
})
</script>

<style scoped>
.audio-waveform {
  position: relative;
  width: 100%;
  height: 80px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

.waveform-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.progress-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #f56c6c;
  pointer-events: none;
  transition: left 0.1s ease;
  z-index: 1;
}

/* 加载状态 */
.audio-waveform:not(.loaded) .waveform-canvas {
  opacity: 0.5;
}
</style>