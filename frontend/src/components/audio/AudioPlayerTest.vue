<template>
  <div class="audio-player-test">
    <h2>独立音频播放器测试</h2>

    <!-- 音频URL输入 -->
    <div class="url-input">
      <el-input
        v-model="testAudioUrl"
        placeholder="输入音频URL进行测试"
        style="width: 500px; margin-right: 12px;"
      />
      <el-button @click="loadAudio" type="primary">加载音频</el-button>
      <el-button @click="useDefaultAudio" type="success">使用示例音频</el-button>
    </div>

    <!-- 当前音频信息 -->
    <div class="current-audio" v-if="currentAudioUrl">
      <p><strong>当前音频:</strong> {{ currentAudioUrl }}</p>
    </div>

    <!-- 独立音频播放器 -->
    <div class="player-container">
      <h3>独立播放器</h3>
      <SimpleAudioPlayer
        ref="audioPlayerRef"
        :audio-url="currentAudioUrl"
        :show-status="true"
        @time-update="onTimeUpdate"
        @play="onPlay"
        @pause="onPause"
        @ended="onEnded"
        @seek="onSeek"
      />
    </div>

    <!-- 事件日志 -->
    <div class="event-log">
      <h3>事件日志</h3>
      <div class="log-container">
        <div
          v-for="(log, index) in eventLogs"
          :key="index"
          class="log-item"
        >
          <span class="log-time">{{ log.time }}</span>
          <span class="log-event">{{ log.event }}</span>
          <span class="log-data">{{ log.data }}</span>
        </div>
      </div>
      <el-button @click="clearLogs" size="small">清空日志</el-button>
    </div>

    <!-- 控制按钮 -->
    <div class="control-buttons">
      <h3>外部控制测试</h3>
      <el-button @click="testSeekTo(10)" type="primary">跳转到10秒</el-button>
      <el-button @click="testSeekTo(30)" type="primary">跳转到30秒</el-button>
      <el-button @click="testSeekTo(60)" type="primary">跳转到60秒</el-button>
      <el-button @click="testPlay" type="success">外部播放</el-button>
      <el-button @click="testPause" type="warning">外部暂停</el-button>
      <el-button @click="getPlayerInfo" type="info">获取播放器信息</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import SimpleAudioPlayer from './SimpleAudioPlayer.vue'

// 组件引用
const audioPlayerRef = ref()

// 测试数据
const testAudioUrl = ref('')
const currentAudioUrl = ref('')

// 事件日志
const eventLogs = ref<Array<{time: string, event: string, data: string}>>([])

// 添加日志
const addLog = (event: string, data: any = '') => {
  const now = new Date()
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

  eventLogs.value.unshift({
    time: timeStr,
    event,
    data: typeof data === 'object' ? JSON.stringify(data) : String(data)
  })

  // 保持最多50条日志
  if (eventLogs.value.length > 50) {
    eventLogs.value = eventLogs.value.slice(0, 50)
  }
}

// 音频URL操作
const loadAudio = () => {
  if (!testAudioUrl.value.trim()) {
    ElMessage.warning('请输入音频URL')
    return
  }

  currentAudioUrl.value = testAudioUrl.value.trim()
  addLog('音频加载', currentAudioUrl.value)
}

const useDefaultAudio = () => {
  // 使用一个公共的测试音频URL
  const defaultUrl = 'https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3'
  testAudioUrl.value = defaultUrl
  currentAudioUrl.value = defaultUrl
  addLog('使用示例音频', defaultUrl)
}

// 播放器事件处理
const onTimeUpdate = (time: number) => {
  // 每5秒记录一次时间更新（避免日志过多）
  if (Math.floor(time) % 5 === 0 && time > 0) {
    addLog('时间更新', `${time.toFixed(1)}秒`)
  }
}

const onPlay = () => {
  addLog('开始播放', '')
}

const onPause = () => {
  addLog('暂停播放', '')
}

const onEnded = () => {
  addLog('播放结束', '')
}

const onSeek = (time: number) => {
  addLog('跳转', `${time.toFixed(1)}秒`)
}

// 外部控制测试
const testSeekTo = (time: number) => {
  if (audioPlayerRef.value) {
    audioPlayerRef.value.seekTo(time)
    addLog('外部跳转', `${time}秒`)
  } else {
    ElMessage.warning('播放器未初始化')
  }
}

const testPlay = () => {
  if (audioPlayerRef.value) {
    audioPlayerRef.value.play()
    addLog('外部播放', '')
  }
}

const testPause = () => {
  if (audioPlayerRef.value) {
    audioPlayerRef.value.pause()
    addLog('外部暂停', '')
  }
}

const getPlayerInfo = () => {
  if (audioPlayerRef.value) {
    const info = {
      currentTime: audioPlayerRef.value.getCurrentTime(),
      duration: audioPlayerRef.value.getDuration(),
      isPlaying: audioPlayerRef.value.isPlaying()
    }
    addLog('播放器信息', JSON.stringify(info))
    ElMessage.info(`当前时间: ${info.currentTime.toFixed(1)}s, 总时长: ${info.duration.toFixed(1)}s, 播放中: ${info.isPlaying}`)
  }
}

// 清空日志
const clearLogs = () => {
  eventLogs.value = []
}
</script>

<style scoped>
.audio-player-test {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.url-input {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.current-audio {
  background: #f0f2f5;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 20px;
  font-size: 14px;
}

.player-container {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.event-log {
  margin-bottom: 20px;
}

.log-container {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 10px;
}

.log-item {
  display: flex;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  margin-bottom: 4px;
  padding: 2px 0;
}

.log-time {
  color: #6c757d;
  margin-right: 12px;
  min-width: 60px;
}

.log-event {
  color: #007bff;
  margin-right: 12px;
  min-width: 80px;
  font-weight: bold;
}

.log-data {
  color: #28a745;
  word-break: break-all;
}

.control-buttons {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.control-buttons .el-button {
  margin-right: 8px;
  margin-bottom: 8px;
}

h2, h3 {
  color: #2c3e50;
  margin-bottom: 16px;
}

h2 {
  text-align: center;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}
</style>