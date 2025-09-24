<template>
  <div class="pure-audio-player">
    <!-- 静态波形图 -->
    <StaticWaveform @seek="onWaveformSeek" />

    <!-- 纯原生HTML5音频播放器，无任何JavaScript干预 -->
    <audio
      ref="audioRef"
      :src="audioUrl"
      controls
      preload="metadata"
      style="width: 100%;"
    ></audio>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import StaticWaveform from './StaticWaveform.vue'

interface Props {
  audioUrl?: string
  showStatus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  audioUrl: '',
  showStatus: false
})

const audioRef = ref<HTMLAudioElement>()

// 处理波形点击跳转
const onWaveformSeek = (time: number) => {
  if (audioRef.value) {
    audioRef.value.currentTime = time
  }
}

// 暴露最简单的跳转方法
defineExpose({
  seekTo: (time: number) => {
    if (audioRef.value) {
      audioRef.value.currentTime = time
    }
  }
})
</script>

<style scoped>
.pure-audio-player {
  padding: 16px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}
</style>