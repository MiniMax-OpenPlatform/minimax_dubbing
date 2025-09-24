<template>
  <div class="simple-audio-player">
    <!-- 音频文件 -->
    <audio
      ref="audioRef"
      :src="audioUrl"
      preload="metadata"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      @error="onError"
    ></audio>

    <!-- 波形显示区域 -->
    <div class="waveform-section">
      <SimpleWaveform
        ref="waveformRef"
        :current-time="currentTime"
        :duration="totalDuration"
        :is-playing="isPlaying"
        @seek="onWaveformSeek"
      />
    </div>

    <!-- 播放器控制界面 -->
    <div class="player-controls">
      <!-- 播放/暂停按钮 -->
      <el-button
        :icon="isPlaying ? VideoPause : VideoPlay"
        circle
        type="primary"
        @click="togglePlay"
        :disabled="!audioUrl || !isLoaded"
        size="default"
      />

      <!-- 时间显示 -->
      <span class="time-display">{{ formatTime(currentTime) }}</span>

      <!-- 进度条 -->
      <div class="progress-container">
        <el-slider
          v-model="sliderValue"
          :min="0"
          :max="totalDuration"
          :step="0.1"
          :show-tooltip="true"
          :format-tooltip="formatTime"
          @input="onSliderInput"
          @change="onSliderChange"
          :disabled="!audioUrl || !isLoaded || totalDuration <= 0"
          class="progress-slider"
        />
      </div>

      <!-- 总时长显示 -->
      <span class="time-display">{{ formatTime(totalDuration) }}</span>
    </div>


    <!-- 状态信息 -->
    <div class="player-status" v-if="showStatus">
      <span>{{ statusText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'
import SimpleWaveform from './SimpleWaveform.vue'


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
}>()

// 组件引用
const audioRef = ref<HTMLAudioElement>()
const waveformRef = ref()

// 播放状态
const isPlaying = ref(false)
const isLoaded = ref(false)
const currentTime = ref(0)
const totalDuration = ref(0)
const sliderValue = ref(0)

// 用户交互状态
const isUserSeeking = ref(false)


// 状态文本
const statusText = ref('准备中...')

// 格式化时间显示
const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}


// 音频事件处理
const onLoadedMetadata = () => {
  if (audioRef.value) {
    totalDuration.value = audioRef.value.duration || 0
    isLoaded.value = true
    statusText.value = '可播放'
    console.log('音频加载完成，时长:', totalDuration.value)

    // 音频加载完成后，手动触发波形生成
    if (waveformRef.value && props.audioUrl) {
      setTimeout(() => {
        waveformRef.value.generateWaveformFor(props.audioUrl)
      }, 200)
    }
  }
}

const onTimeUpdate = () => {
  if (audioRef.value && !isUserSeeking.value) {
    const newTime = audioRef.value.currentTime
    currentTime.value = newTime
    sliderValue.value = newTime
    emit('time-update', newTime)
  }
}

const onEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
  sliderValue.value = 0
  statusText.value = '播放结束'
}

const onError = (event: Event) => {
  console.error('音频加载错误:', event)
  isLoaded.value = false
  statusText.value = '加载失败'
}

// 播放控制
const togglePlay = async () => {
  if (!audioRef.value || !isLoaded.value) return

  try {
    if (isPlaying.value) {
      audioRef.value.pause()
      isPlaying.value = false
      statusText.value = '已暂停'
    } else {
      await audioRef.value.play()
      isPlaying.value = true
      statusText.value = '正在播放'
    }
  } catch (error) {
    console.error('播放控制失败:', error)
  }
}

// 进度条控制 - 核心功能
const onSliderInput = (value: number) => {
  console.log('拖动进度条:', value)
  isUserSeeking.value = true
  currentTime.value = value
}

const onSliderChange = (value: number) => {
  console.log('进度条拖动完成，跳转到:', value)
  if (!audioRef.value || !isLoaded.value) {
    isUserSeeking.value = false
    return
  }

  // 直接设置音频位置
  audioRef.value.currentTime = value
  currentTime.value = value

  emit('seek', value)

  // 恢复时间更新
  setTimeout(() => {
    isUserSeeking.value = false
  }, 100)
}

// 波形点击控制 - 使用与进度条相同的逻辑
const onWaveformSeek = (time: number) => {
  console.log('波形跳转到:', time)

  // 使用与进度条相同的处理逻辑
  onSliderChange(time)
}

// 监听音频URL变化
watch(() => props.audioUrl, (newUrl, oldUrl) => {
  if (newUrl && newUrl !== '') {
    // 只有URL真正变化时才重置状态
    if (newUrl !== oldUrl) {
      // 重置状态
      isPlaying.value = false
      isLoaded.value = false
      currentTime.value = 0
      totalDuration.value = 0
      sliderValue.value = 0
      statusText.value = '加载中...'

      nextTick(() => {
        if (audioRef.value) {
          audioRef.value.load()
        }
      })
    }
  } else {
    // 清空音频
    isPlaying.value = false
    isLoaded.value = false
    currentTime.value = 0
    totalDuration.value = 0
    sliderValue.value = 0
    statusText.value = '无音频'
  }
}, { immediate: true })

// 暴露方法给父组件
defineExpose({
  seekTo: (time: number) => {
    if (audioRef.value && isLoaded.value) {
      console.log('跳转到时间:', time, '(不自动播放)')
      // 设置音频位置但不播放
      audioRef.value.currentTime = time
      currentTime.value = time
      sliderValue.value = time
      // 发出跳转事件
      emit('seek', time)
      emit('time-update', time)
      // 不调用play()，让用户手动控制播放
    } else {
      console.log('音频未加载，无法跳转到:', time)
    }
  },
  getCurrentTime: () => currentTime.value,
  getDuration: () => totalDuration.value,
  isPlaying: () => isPlaying.value
})
</script>

<style scoped>
.simple-audio-player {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.waveform-section {
  margin-bottom: 16px;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-display {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  color: #606266;
  min-width: 45px;
  text-align: center;
}

.progress-container {
  flex: 1;
  margin: 0 8px;
}

.progress-slider {
  margin: 0;
}

.progress-slider :deep(.el-slider__runway) {
  height: 6px;
  background-color: #f0f2f5;
  border-radius: 3px;
}

.progress-slider :deep(.el-slider__bar) {
  background-color: #409eff;
  border-radius: 3px;
}

.progress-slider :deep(.el-slider__button) {
  width: 16px;
  height: 16px;
  border: 2px solid #409eff;
  background-color: white;
}

.progress-slider :deep(.el-slider__button:hover) {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}


.player-status {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f2f5;
  font-size: 12px;
  color: #606266;
  text-align: center;
}

/* 禁用状态样式 */
.player-controls :deep(.is-disabled) {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>