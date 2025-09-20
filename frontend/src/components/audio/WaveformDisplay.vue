<template>
  <div class="waveform-container" ref="waveformContainer">
    <!-- 波形分析加载状态 -->
    <div v-if="isAnalyzing" class="waveform-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <el-text type="primary" size="small">正在分析音频波形...</el-text>
    </div>

    <!-- 波形图区域 -->
    <canvas
      v-else
      ref="waveformCanvas"
      class="waveform-canvas"
      @click="handleCanvasClick"
    ></canvas>

    <!-- 进度指示器 -->
    <div
      class="progress-indicator"
      :style="{ left: progressPercentage + '%' }"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'

interface Props {
  waveformData: number[]
  currentTime: number
  duration: number
  color: string
  isAnalyzing: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'seek-to-position': [event: MouseEvent]
}>()

const waveformCanvas = ref<HTMLCanvasElement>()
const waveformContainer = ref<HTMLDivElement>()
const retryCount = ref(0)
const maxRetries = 5

const progressPercentage = computed(() => {
  return props.duration > 0 ? (props.currentTime / props.duration) * 100 : 0
})

const handleCanvasClick = (event: MouseEvent) => {
  emit('seek-to-position', event)
}

// 绘制波形图
const drawWaveform = () => {
  const canvas = waveformCanvas.value
  const container = waveformContainer.value

  if (!canvas || !container || props.waveformData.length === 0) {
    // 如果Canvas或容器不存在，且组件可见且未超过重试次数，稍后重试
    if (props.waveformData.length > 0 && (!canvas || !container) && retryCount.value < maxRetries) {
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

  // 设置canvas尺寸，增加高度以提升波形可见性
  const containerWidth = container.clientWidth
  if (containerWidth > 0) {
    canvas.width = containerWidth
    canvas.height = 80 // 增加高度从60到80
  } else {
    // 如果容器宽度为0，使用默认宽度
    canvas.width = 600
    canvas.height = 80 // 增加高度从60到80
  }

  const width = canvas.width
  const height = canvas.height
  const barWidth = width / props.waveformData.length
  const progressPoint = (props.currentTime / props.duration) * width

  // 重置重试计数器（成功绘制）
  retryCount.value = 0

  // 清空画布
  ctx.clearRect(0, 0, width, height)

  // 绘制波形，增强可见性
  props.waveformData.forEach((amplitude, index) => {
    const x = index * barWidth
    const barHeight = amplitude * height * 0.9 // 增加高度比例从0.8到0.9
    const y = (height - barHeight) / 2

    // 根据播放进度设置颜色
    if (x < progressPoint) {
      ctx.fillStyle = props.color // 已播放部分
    } else {
      ctx.fillStyle = '#c0c4cc' // 未播放部分，使用更深的颜色提高对比度
    }

    // 绘制波形条，无间距以创建连续波形
    ctx.fillRect(x, y, Math.ceil(barWidth), barHeight)
  })
}

// 监听数据变化重新绘制
watch([() => props.waveformData, () => props.currentTime], () => {
  if (!props.isAnalyzing) {
    drawWaveform()
  }
})

onMounted(() => {
  // 监听窗口大小变化，重新绘制波形
  window.addEventListener('resize', drawWaveform)

  // 初始绘制
  nextTick(() => {
    drawWaveform()
  })
})

// 暴露方法给父组件
defineExpose({
  redraw: drawWaveform
})
</script>

<style scoped>
.waveform-container {
  position: relative;
  height: 80px; /* 增加容器高度匹配canvas */
  background: #f8f9fa;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05); /* 添加内阴影增强立体感 */
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
  width: 1px; /* 减少进度指示器宽度 */
  background: #f56c6c;
  pointer-events: none;
  transition: left 0.1s ease;
  z-index: 10; /* 确保在波形之上 */
}

.waveform-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  background: #f5f7fa;
}

.loading-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>