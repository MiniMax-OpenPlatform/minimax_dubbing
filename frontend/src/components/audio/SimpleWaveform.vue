<template>
  <div class="simple-waveform" ref="waveformContainer">
    <!-- 加载状态 -->
    <div v-if="isAnalyzing" class="waveform-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span class="loading-text">分析音频波形...</span>
    </div>

    <!-- 波形区域 -->
    <div v-else class="waveform-area" @click="handleWaveformClick">
      <canvas
        ref="waveformCanvas"
        class="waveform-canvas"
      ></canvas>

      <!-- 进度指示线 -->
      <div
        class="progress-line"
        :style="{ left: progressPercentage + '%' }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'

interface Props {
  currentTime: number
  duration: number
  isPlaying: boolean
}

const props = withDefaults(defineProps<Props>(), {
  currentTime: 0,
  duration: 0,
  isPlaying: false
})

const emit = defineEmits<{
  'seek': [time: number]
}>()

// 组件引用
const waveformContainer = ref<HTMLDivElement>()
const waveformCanvas = ref<HTMLCanvasElement>()

// 波形状态
const waveformData = ref<number[]>([])
const isAnalyzing = ref(false)

// 计算进度百分比
const progressPercentage = computed(() => {
  return props.duration > 0 ? (props.currentTime / props.duration) * 100 : 0
})

// 生成波形数据
const generateWaveform = async (audioUrl?: string) => {
  isAnalyzing.value = true

  // 如果没有音频URL，生成默认波形
  if (!audioUrl) {
    const sampleCount = 150
    const samples: number[] = []

    for (let i = 0; i < sampleCount; i++) {
      const progress = i / sampleCount
      let amplitude = 0.05 // 基础值

      // 创建几个活跃区域模拟真实音频
      if ((progress > 0.1 && progress < 0.3) ||
          (progress > 0.5 && progress < 0.8) ||
          (progress > 0.85 && progress < 0.95)) {
        const wave = Math.sin(i * 0.15) * 0.3 + 0.3
        const noise = (Math.random() - 0.5) * 0.2
        amplitude = Math.max(0.1, Math.min(0.7, wave + noise))
      } else {
        amplitude = Math.random() * 0.1 + 0.02
      }

      samples.push(amplitude)
    }

    waveformData.value = samples
    isAnalyzing.value = false
    return
  }

  // 实际音频文件分析
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const response = await fetch(audioUrl)

    if (!response.ok) {
      throw new Error(`Failed to fetch audio: ${response.status}`)
    }

    const arrayBuffer = await response.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

    // 处理音频数据
    const rawData = audioBuffer.getChannelData(0)
    const sampleCount = 150
    const blockSize = Math.floor(rawData.length / sampleCount)
    const samples: number[] = []

    for (let i = 0; i < sampleCount; i++) {
      let sum = 0
      for (let j = 0; j < blockSize; j++) {
        sum += Math.abs(rawData[i * blockSize + j])
      }

      let amplitude = sum / blockSize

      // 增强小音量的可见性
      if (amplitude < 0.1) {
        amplitude = Math.min(amplitude * 4, 0.15)
      } else {
        amplitude = Math.min(amplitude * 2, 0.8)
      }

      amplitude = Math.max(amplitude, 0.02)
      samples.push(amplitude)
    }

    waveformData.value = samples
    audioContext.close()

  } catch (error) {
    console.error('波形分析失败:', error)

    // 失败时生成默认波形
    const sampleCount = 150
    const samples: number[] = []
    for (let i = 0; i < sampleCount; i++) {
      samples.push(Math.random() * 0.5 + 0.1)
    }
    waveformData.value = samples
  }

  isAnalyzing.value = false
}

// 绘制波形
const drawWaveform = () => {
  const canvas = waveformCanvas.value
  const container = waveformContainer.value

  if (!canvas || !container || waveformData.value.length === 0) {
    return
  }

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 设置画布尺寸
  const width = container.clientWidth
  const height = 50
  canvas.width = width
  canvas.height = height

  // 清空画布
  ctx.clearRect(0, 0, width, height)

  const barWidth = width / waveformData.value.length
  const progressPoint = (props.currentTime / props.duration) * width

  // 绘制波形条
  waveformData.value.forEach((amplitude, index) => {
    const x = index * barWidth
    const barHeight = amplitude * height * 0.8
    const y = (height - barHeight) / 2

    // 根据播放进度设置颜色
    if (x < progressPoint) {
      ctx.fillStyle = '#409eff' // 已播放：蓝色
    } else {
      ctx.fillStyle = '#dcdfe6' // 未播放：灰色
    }

    ctx.fillRect(x, y, Math.ceil(barWidth), barHeight)
  })
}

// 处理波形点击事件 - 只做可视化，不直接控制播放
const handleWaveformClick = (event: MouseEvent) => {
  if (props.duration <= 0) return

  const container = waveformContainer.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percentage = x / rect.width
  const time = percentage * props.duration

  // 只发送事件，让父组件决定是否跳转
  emit('seek', time)
}

// 手动生成波形，供外部调用
const generateWaveformFor = (audioUrl: string) => {
  if (audioUrl) {
    generateWaveform(audioUrl)
  } else {
    generateWaveform()
  }
}

// 监听时间变化重绘波形
watch([() => props.currentTime, () => waveformData.value], () => {
  if (!isAnalyzing.value) {
    nextTick(() => {
      drawWaveform()
    })
  }
})

// 组件挂载
onMounted(() => {
  // 初始生成默认波形
  generateWaveform()

  // 监听窗口大小变化
  window.addEventListener('resize', drawWaveform)
})

// 暴露方法
defineExpose({
  generateWaveformFor,
  refresh: generateWaveform
})
</script>

<style scoped>
.simple-waveform {
  width: 100%;
  height: 60px;
  background: #fafbfc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
}

.waveform-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  color: #606266;
  font-size: 12px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 12px;
}

.waveform-area {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: pointer;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.progress-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #f56c6c;
  border-radius: 1px;
  pointer-events: none;
  transition: left 0.1s ease;
  z-index: 10;
}

.waveform-area:hover {
  background: #f0f2f5;
}
</style>