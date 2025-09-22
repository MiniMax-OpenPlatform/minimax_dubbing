<template>
  <div class="video-player-container">
    <div class="video-content">
      <div v-if="videoUrl" class="video-wrapper">
        <video
          ref="videoRef"
          :src="videoUrl"
          controls
          preload="metadata"
          class="video-element"
          @loadedmetadata="onVideoLoaded"
          @timeupdate="onTimeUpdate"
          @seeked="onVideoSeeked"
        >
          您的浏览器不支持视频播放
        </video>

        <div class="video-info">
          <span class="duration">时长: {{ formatTime(duration) }}</span>
          <span class="current-time">当前: {{ formatTime(currentTime) }}</span>
        </div>
      </div>

      <div v-else class="no-video">
        <el-empty description="暂无视频文件" :image-size="80" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  title: string
  videoUrl?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'time-update': [time: number]
  'seek': [time: number]
}>()

const videoRef = ref<HTMLVideoElement>()
const duration = ref(0)
const currentTime = ref(0)

const onVideoLoaded = () => {
  if (videoRef.value) {
    duration.value = videoRef.value.duration
  }
}

const onTimeUpdate = () => {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
    emit('time-update', currentTime.value)
  }
}

const onVideoSeeked = () => {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
    emit('seek', currentTime.value)
  }
}

const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds)) return '00:00'

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}


// 暴露方法给父组件
const seekTo = (time: number) => {
  if (videoRef.value) {
    videoRef.value.currentTime = time
  }
}

const play = () => {
  if (videoRef.value) {
    videoRef.value.play()
  }
}

const pause = () => {
  if (videoRef.value) {
    videoRef.value.pause()
  }
}

defineExpose({
  seekTo,
  play,
  pause,
  videoElement: videoRef
})

// 监听视频URL变化
watch(() => props.videoUrl, () => {
  currentTime.value = 0
  duration.value = 0
})
</script>

<style scoped>
.video-player-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}


.video-content {
  padding: 16px;
}

.video-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-element {
  width: 100%;
  max-height: 300px;
  border-radius: 6px;
  background: #000;
}

.video-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  padding: 0 4px;
}

.no-video {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 120px;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .video-element {
    max-height: 200px;
  }
}
</style>