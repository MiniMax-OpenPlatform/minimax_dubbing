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
          @seeking="onVideoSeeking"
          @click="onVideoClick"
          @loadstart="onVideoLoadStart"
          @canplay="onVideoCanPlay"
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
    console.log('[VideoPlayer] 时间更新:', currentTime.value)
  }
}

const onVideoSeeked = () => {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
    emit('seek', currentTime.value)
    console.log('[VideoPlayer] 跳转事件:', currentTime.value)
  }
}

// 添加更多事件监听
const onVideoSeeking = () => {
  console.log('[VideoPlayer] 正在跳转...')
}

const onVideoClick = () => {
  console.log('[VideoPlayer] 视频被点击')
}

const onVideoLoadStart = () => {
  console.log('[VideoPlayer] 开始加载视频')
}

const onVideoCanPlay = () => {
  console.log('[VideoPlayer] 视频可以播放')

  // 检查详细状态
  if (videoRef.value) {
    const video = videoRef.value
    console.log('[VideoPlayer] 详细状态检查:')
    console.log('  - readyState:', video.readyState, getReadyStateText(video.readyState))
    console.log('  - duration:', video.duration)
    console.log('  - seekable.length:', video.seekable.length)
    console.log('  - seekable ranges:', video.seekable.length > 0 ? `${video.seekable.start(0)} - ${video.seekable.end(0)}` : 'none')
    console.log('  - currentTime:', video.currentTime)
    console.log('  - paused:', video.paused)
    console.log('  - networkState:', video.networkState)

    // 检查是否需要修复 seekable 问题
    checkAndFixSeekable()
  }
}

// 检查并修复 seekable 问题
const checkAndFixSeekable = () => {
  if (!videoRef.value) return

  const video = videoRef.value
  const isSeekableInvalid = video.seekable.length === 0 ||
    (video.seekable.length > 0 && video.seekable.end(0) === 0)

  if (isSeekableInvalid && video.duration > 0) {
    console.log('[VideoPlayer] 检测到 seekable 异常，尝试修复...')

    // 方法1: 强制重新加载
    setTimeout(() => {
      if (videoRef.value) {
        const currentSrc = videoRef.value.src
        console.log('[VideoPlayer] 执行强制重新加载')
        videoRef.value.load()

        // 再次检查
        setTimeout(() => {
          if (videoRef.value && videoRef.value.seekable.length > 0) {
            console.log('[VideoPlayer] 修复成功，seekable 范围:',
              `${videoRef.value.seekable.start(0)} - ${videoRef.value.seekable.end(0)}`)
          } else {
            console.log('[VideoPlayer] 修复失败，可能需要服务器端解决')
          }
        }, 1000)
      }
    }, 500)
  }
}

const getReadyStateText = (state: number): string => {
  switch (state) {
    case 0: return 'HAVE_NOTHING'
    case 1: return 'HAVE_METADATA'
    case 2: return 'HAVE_CURRENT_DATA'
    case 3: return 'HAVE_FUTURE_DATA'
    case 4: return 'HAVE_ENOUGH_DATA'
    default: return 'UNKNOWN'
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
watch(() => props.videoUrl, (newUrl) => {
  console.log('[VideoPlayer] URL变化:', newUrl)

  if (videoRef.value && newUrl) {
    // 重置状态
    currentTime.value = 0
    duration.value = 0

    // 强制重新加载视频
    videoRef.value.load()

    console.log('[VideoPlayer] 视频重新加载完成')
  } else if (!newUrl) {
    // URL为空时清空状态
    currentTime.value = 0
    duration.value = 0
  }
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