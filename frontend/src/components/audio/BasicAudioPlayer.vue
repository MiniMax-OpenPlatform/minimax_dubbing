<template>
  <div class="basic-audio-player">
    <!-- 纯原生HTML5音频播放器 -->
    <audio
      ref="audioRef"
      :src="audioUrl"
      controls
      preload="metadata"
      style="width: 100%;"
      @canplay="checkAndFixSeekable"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
    ></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  audioUrl?: string
  showStatus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  audioUrl: '',
  showStatus: false
})

const emit = defineEmits<{
  'time-update': [time: number]
  'seek': [time: number]
  'duration-change': [duration: number]
}>()

const audioRef = ref<HTMLAudioElement>()
const currentTime = ref(0)
const duration = ref(0)

// 时间更新事件
const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    emit('time-update', currentTime.value)
  }
}

// 元数据加载完成事件
const onLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
    emit('duration-change', duration.value)
  }
}

// 检查并修复 seekable 问题
const checkAndFixSeekable = () => {
  if (!audioRef.value) return

  const audio = audioRef.value
  const isSeekableInvalid = audio.seekable.length === 0 ||
    (audio.seekable.length > 0 && audio.seekable.end(0) === 0)

  if (isSeekableInvalid && audio.duration > 0) {
    // 强制重新加载以修复 seekable 异常
    setTimeout(() => {
      if (audioRef.value) {
        audioRef.value.load()
      }
    }, 500)
  }
}

// 监听URL变化
watch(() => props.audioUrl, (newUrl) => {
  if (audioRef.value && newUrl) {
    audioRef.value.load()
  }
})

// 暴露跳转方法和状态
defineExpose({
  seekTo: (time: number) => {
    if (audioRef.value) {
      audioRef.value.currentTime = time
    }
  },
  currentTime,
  duration
})
</script>

<style scoped>
.basic-audio-player {
  padding: 16px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.status {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
  text-align: center;
}
</style>