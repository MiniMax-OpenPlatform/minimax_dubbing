<template>
  <div class="audio-track-container">
    <div class="track-header">
      <h4>{{ title }}</h4>
      <div class="track-controls">
        <el-switch
          v-model="isVisible"
          :active-text="isVisible ? '显示' : '隐藏'"
          @change="$emit('visibility-change', isVisible)"
        />
        <el-button
          v-if="audioUrl && isVisible"
          @click="downloadAudio"
          type="primary"
          size="small"
        >
          <el-icon><Download /></el-icon>
          下载
        </el-button>
      </div>
    </div>

    <div v-if="isVisible" class="track-content">
      <div class="audio-wrapper">
        <!-- 音频播放控制器 -->
        <AudioController
          :is-playing="isPlaying"
          :has-audio="!!audioUrl"
          :current-time="currentTime"
          :duration="duration"
          :volume="volume"
          @toggle-play="togglePlay"
          @stop="stopAudio"
          @volume-change="updateVolume"
        />

        <!-- 当没有音频时显示提示 -->
        <div v-if="!audioUrl" class="no-audio-notice">
          <el-text type="info" size="small">暂无音频文件，显示示例波形</el-text>
        </div>

        <!-- 波形显示 -->
        <WaveformDisplay
          :waveform-data="waveformData"
          :current-time="currentTime"
          :duration="duration"
          :color="color"
          :is-analyzing="isAnalyzingWaveform"
          @seek-to-position="seekToPosition"
        />

        <!-- 进度条 -->
        <ProgressBar
          :current-time="progressValue"
          :duration="duration"
          @seek-to="seekTo"
          @progress-input="onProgressInput"
        />

        <!-- 隐藏的音频元素 -->
        <audio
          ref="audioRef"
          :src="audioUrl"
          preload="metadata"
          @loadedmetadata="onAudioLoaded"
          @timeupdate="onTimeUpdate"
          @ended="onAudioEnded"
          @loadstart="onLoadStart"
          @canplay="onCanPlay"
          @error="onAudioError"
        ></audio>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 导入子组件
import AudioController from './audio/AudioController.vue'
import WaveformDisplay from './audio/WaveformDisplay.vue'
import ProgressBar from './audio/ProgressBar.vue'

// 导入composable
import { useAudioWaveform } from '../composables/useAudioWaveform'

interface Props {
  title: string
  audioUrl?: string
  defaultVisible?: boolean
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultVisible: true,
  color: '#409eff'
})

const emit = defineEmits<{
  'visibility-change': [visible: boolean]
  'time-update': [time: number]
}>()

const audioRef = ref<HTMLAudioElement>()
const isVisible = ref(props.defaultVisible)
const isPlaying = ref(false)
const duration = ref(0)
const currentTime = ref(0)
const progressValue = ref(0)
const volume = ref(80)

// 使用audio waveform composable
const { waveformData, isAnalyzingWaveform, generateWaveform } = useAudioWaveform()

const onAudioLoaded = async () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
    audioRef.value.volume = volume.value / 100
    await generateWaveform(props.audioUrl)
  }
}

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    progressValue.value = currentTime.value
    emit('time-update', currentTime.value)
  }
}

const onAudioEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
  progressValue.value = 0
}

const onLoadStart = () => {
  // Audio loading started
}

const onCanPlay = () => {
  if (audioRef.value && duration.value === 0) {
    duration.value = audioRef.value.duration
    generateWaveform(props.audioUrl)
  }
}

const onAudioError = (event: Event) => {
  console.error('[AudioTrack] 音频加载错误:', props.title, event, props.audioUrl)
  ElMessage.error(`音频加载失败: ${props.title}`)
}

const togglePlay = () => {
  if (!audioRef.value) return

  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

const stopAudio = () => {
  if (!audioRef.value) return

  audioRef.value.pause()
  audioRef.value.currentTime = 0
  isPlaying.value = false
  currentTime.value = 0
  progressValue.value = 0
}

const seekTo = (time: number) => {
  if (audioRef.value) {
    audioRef.value.currentTime = time
    currentTime.value = time
  }
}

const onProgressInput = (value: number) => {
  currentTime.value = value
}

const seekToPosition = (event: MouseEvent) => {
  if (!audioRef.value) return

  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percentage = x / rect.width
  const time = percentage * duration.value

  seekTo(time)
}

const updateVolume = (value: number) => {
  if (audioRef.value) {
    audioRef.value.volume = value / 100
  }
}

const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds)) return '00:00'

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

const downloadAudio = () => {
  if (!props.audioUrl) {
    ElMessage.error('音频文件不存在')
    return
  }

  try {
    const link = document.createElement('a')
    link.href = props.audioUrl
    link.download = `${props.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}.mp3`
    link.click()
    ElMessage.success('音频下载已开始')
  } catch (error) {
    ElMessage.error('下载失败')
    console.error('Download error:', error)
  }
}


// 监听音频URL变化
watch(() => props.audioUrl, (newUrl, oldUrl) => {
  isPlaying.value = false
  currentTime.value = 0
  duration.value = 0
  progressValue.value = 0

  // 如果有新的URL，等待下一个tick后重新加载和分析
  if (newUrl && audioRef.value) {
    nextTick(() => {
      if (audioRef.value) {
        audioRef.value.load()
        // 重新生成波形数据
        generateWaveform(newUrl)
      }
    })
  }
})

onMounted(() => {
  // 如果没有音频URL，也生成默认波形用于测试
  if (!props.audioUrl) {
    // 使用更长的延迟确保DOM完全渲染
    setTimeout(() => {
      generateWaveform()
    }, 300 + Math.random() * 200) // 随机延迟避免同时执行
  }
})

// 暴露方法给父组件
defineExpose({
  play: togglePlay,
  pause: stopAudio,
  seekTo,
  audioElement: audioRef
})
</script>

<style scoped>
.audio-track-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  margin-bottom: 16px;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.track-header h4 {
  margin: 0;
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.track-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.track-content {
  padding: 16px;
}

.audio-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.no-audio-notice {
  text-align: center;
  padding: 8px;
  background: #f0f9ff;
  border: 1px dashed #409eff;
  border-radius: 4px;
  margin-bottom: 12px;
}


/* 响应式设计 */
@media (max-width: 768px) {
  .track-header {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }

  .track-controls {
    justify-content: space-between;
  }
}

</style>