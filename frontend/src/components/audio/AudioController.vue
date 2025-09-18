<template>
  <div class="audio-controls">
    <el-button-group>
      <el-button
        @click="$emit('toggle-play')"
        :type="isPlaying ? 'danger' : 'primary'"
        :disabled="!hasAudio"
        size="small"
      >
        <el-icon>
          <VideoPlay v-if="!isPlaying" />
          <VideoPause v-else />
        </el-icon>
        {{ isPlaying ? '暂停' : '播放' }}
      </el-button>
      <el-button
        @click="$emit('stop')"
        :disabled="!hasAudio"
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
        :model-value="volume"
        @update:model-value="$emit('volume-change', $event)"
        :min="0"
        :max="100"
        :show-tooltip="false"
        style="width: 80px; margin-left: 8px;"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { VideoPlay, VideoPause, CircleClose, Microphone } from '@element-plus/icons-vue'

interface Props {
  isPlaying: boolean
  hasAudio: boolean
  currentTime: number
  duration: number
  volume: number
}

defineProps<Props>()

defineEmits<{
  'toggle-play': []
  'stop': []
  'volume-change': [volume: number]
}>()

const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds)) return '00:00'

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
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

/* 响应式设计 */
@media (max-width: 768px) {
  .audio-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .volume-control {
    justify-content: center;
  }
}
</style>