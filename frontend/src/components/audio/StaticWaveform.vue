<template>
  <div class="static-waveform">
    <canvas
      ref="canvasRef"
      :width="800"
      :height="60"
      @click="onWaveformClick"
      class="waveform-canvas"
    ></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const emit = defineEmits<{
  seek: [time: number]
}>()

const canvasRef = ref<HTMLCanvasElement>()

// 固定的模拟波形数据
const waveformData = [
  0.1, 0.3, 0.5, 0.2, 0.4, 0.6, 0.3, 0.1, 0.4, 0.7,
  0.2, 0.5, 0.3, 0.6, 0.1, 0.4, 0.5, 0.2, 0.3, 0.6,
  0.4, 0.1, 0.5, 0.3, 0.7, 0.2, 0.4, 0.6, 0.1, 0.3,
  0.5, 0.2, 0.4, 0.3, 0.6, 0.1, 0.5, 0.4, 0.2, 0.7,
  0.3, 0.1, 0.4, 0.6, 0.2, 0.5, 0.3, 0.1, 0.4, 0.5,
  0.2, 0.6, 0.3, 0.1, 0.4, 0.5, 0.7, 0.2, 0.3, 0.4,
  0.1, 0.5, 0.2, 0.6, 0.3, 0.4, 0.1, 0.5, 0.2, 0.3,
  0.6, 0.4, 0.1, 0.5, 0.3, 0.2, 0.4, 0.6, 0.1, 0.3,
  0.5, 0.2, 0.4, 0.3, 0.6, 0.1, 0.5, 0.4, 0.2, 0.3,
  0.1, 0.4, 0.6, 0.2, 0.5, 0.3, 0.1, 0.4, 0.5, 0.2
]

// 绘制静态波形
const drawWaveform = () => {
  if (!canvasRef.value) return

  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空画布
  ctx.clearRect(0, 0, 800, 60)

  const barWidth = 800 / waveformData.length
  const centerY = 30

  // 绘制波形条
  waveformData.forEach((amplitude, index) => {
    const x = index * barWidth
    const barHeight = amplitude * 50

    ctx.fillStyle = '#dcdfe6'
    ctx.fillRect(x, centerY - barHeight / 2, Math.max(1, barWidth - 1), barHeight)
  })
}

// 处理点击事件
const onWaveformClick = (event: MouseEvent) => {
  if (!canvasRef.value) return

  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const clickRatio = x / 800
  const clickTime = clickRatio * 15 // 假设音频长度15秒

  console.log('静态波形点击跳转到:', clickTime)
  emit('seek', Math.max(0, Math.min(clickTime, 15)))
}

// 组件挂载后绘制
onMounted(() => {
  drawWaveform()
})
</script>

<style scoped>
.static-waveform {
  width: 100%;
  margin: 8px 0;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  background: #fafbfc;
}

.waveform-canvas {
  width: 100%;
  height: 60px;
  cursor: pointer;
  display: block;
}

.waveform-canvas:hover {
  background-color: #f0f2f5;
}
</style>