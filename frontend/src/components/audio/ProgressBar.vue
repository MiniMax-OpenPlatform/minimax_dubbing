<template>
  <div class="progress-bar">
    <el-slider
      :model-value="currentTime"
      @update:model-value="$emit('seek-to', $event)"
      @input="$emit('progress-input', $event)"
      :min="0"
      :max="duration"
      :step="0.1"
      :show-tooltip="false"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  currentTime: number
  duration: number
}

defineProps<Props>()

defineEmits<{
  'seek-to': [time: number]
  'progress-input': [value: number]
}>()
</script>

<style scoped>
.progress-bar {
  margin-top: 8px;
}

:deep(.el-slider__runway) {
  height: 4px;
}

:deep(.el-slider__button) {
  width: 12px;
  height: 12px;
}
</style>