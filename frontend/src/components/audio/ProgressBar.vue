<template>
  <div class="progress-bar">
    <el-slider
      :model-value="currentTime"
      @change="handleChange"
      @input="handleInput"
      :min="0"
      :max="Math.max(duration, 1)"
      :step="0.1"
      :show-tooltip="true"
      :format-tooltip="formatTime"
      :disabled="duration <= 0"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  currentTime: number
  duration: number
}

defineProps<Props>()

const emit = defineEmits<{
  'seek-to': [time: number]
  'progress-input': [value: number]
}>()

// 事件处理函数
const handleChange = (value: number) => {
  console.log('Slider change:', value)
  emit('seek-to', value)
}

const handleInput = (value: number) => {
  console.log('Slider input:', value)
  emit('progress-input', value)
}

// 格式化时间显示
const formatTime = (value: number): string => {
  if (!value || isNaN(value)) return '00:00'

  const minutes = Math.floor(value / 60)
  const seconds = Math.floor(value % 60)
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.progress-bar {
  margin-top: 8px;
}

:deep(.el-slider__runway) {
  height: 6px; /* 增加进度条高度便于拖拽 */
  background-color: #f0f2f5;
}

:deep(.el-slider__bar) {
  background-color: #409eff;
}

:deep(.el-slider__button) {
  width: 16px; /* 增加拖拽按钮尺寸 */
  height: 16px;
  border: 2px solid #409eff;
  background-color: white;
}

:deep(.el-slider__button:hover) {
  transform: scale(1.1); /* 悬停时轻微放大 */
  transition: transform 0.2s ease;
}
</style>