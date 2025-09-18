<template>
  <tr>
    <!-- 选择框 -->
    <td>
      <el-checkbox
        :model-value="isSelected"
        @update:model-value="$emit('select', segment, $event)"
      />
    </td>

    <!-- 序号 -->
    <td class="segment-index">{{ segment.index }}</td>

    <!-- 时间 -->
    <td class="time-display">
      <div class="time-group">
        <label>开始:</label>
        <el-input
          v-model="localSegment.start_time"
          size="small"
          @blur="saveChanges"
        />
      </div>
      <div class="time-group">
        <label>结束:</label>
        <el-input
          v-model="localSegment.end_time"
          size="small"
          @blur="saveChanges"
        />
      </div>
    </td>

    <!-- 说话人 -->
    <td>
      <el-input
        v-model="localSegment.speaker"
        size="small"
        placeholder="说话人"
        @blur="saveChanges"
      />
    </td>

    <!-- 原文 -->
    <td>
      <el-input
        v-model="localSegment.original_text"
        type="textarea"
        :rows="2"
        resize="none"
        @blur="saveChanges"
      />
    </td>

    <!-- 译文 -->
    <td>
      <el-input
        v-model="localSegment.translated_text"
        type="textarea"
        :rows="2"
        resize="none"
        placeholder="翻译文本"
        @blur="saveChanges"
      />
    </td>

    <!-- 语音设置 -->
    <td>
      <div class="voice-settings">
        <el-select
          v-model="localSegment.voice_id"
          size="small"
          placeholder="音色"
          @change="saveChanges"
        >
          <el-option label="通用女声" value="female_001" />
          <el-option label="通用男声" value="male_001" />
          <el-option label="温柔女声" value="female_002" />
          <el-option label="磁性男声" value="male_002" />
        </el-select>
        <el-select
          v-model="localSegment.emotion"
          size="small"
          placeholder="情感"
          @change="saveChanges"
        >
          <el-option label="平静" value="calm" />
          <el-option label="开心" value="happy" />
          <el-option label="悲伤" value="sad" />
          <el-option label="愤怒" value="angry" />
        </el-select>
        <el-input-number
          v-model="localSegment.speed"
          :min="0.5"
          :max="2.0"
          :step="0.1"
          size="small"
          @change="saveChanges"
        />
      </div>
    </td>

    <!-- 状态 -->
    <td>
      <el-tag
        :type="getStatusType(segment.status)"
        size="small"
      >
        {{ getStatusText(segment.status) }}
      </el-tag>
    </td>

    <!-- 时长信息 -->
    <td class="duration-info">
      <div>原: {{ formatDuration(segment.duration) }}s</div>
      <div v-if="segment.t_tts_duration">
        TTS: {{ formatDuration(segment.t_tts_duration) }}s
      </div>
      <div v-if="segment.ratio">
        比例: {{ segment.ratio.toFixed(2) }}
      </div>
    </td>

    <!-- 操作 -->
    <td>
      <div class="row-actions">
        <el-button
          size="small"
          type="primary"
          @click="$emit('tts', segment)"
          :disabled="!segment.translated_text"
        >
          TTS
        </el-button>
        <el-button
          size="small"
          v-if="segment.translated_audio_url"
          @click="playAudio"
        >
          播放
        </el-button>
      </div>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Segment {
  id: number
  index: number
  start_time: string
  end_time: string
  duration: number
  speaker: string
  original_text: string
  translated_text: string
  voice_id: string
  emotion: string
  speed: number
  translated_audio_url: string
  t_tts_duration: number
  ratio: number
  status: string
}

const props = defineProps<{
  segment: Segment
  isSelected: boolean
}>()

const emit = defineEmits<{
  select: [segment: Segment, selected: boolean]
  update: [segment: Segment]
  tts: [segment: Segment]
}>()

// 本地编辑状态
const localSegment = ref({ ...props.segment })

// 监听props变化
watch(() => props.segment, (newSegment) => {
  localSegment.value = { ...newSegment }
}, { deep: true })

// 保存更改
const saveChanges = () => {
  if (hasChanges()) {
    emit('update', { ...localSegment.value })
  }
}

// 检查是否有更改
const hasChanges = () => {
  const original = props.segment
  const current = localSegment.value

  return (
    original.start_time !== current.start_time ||
    original.end_time !== current.end_time ||
    original.speaker !== current.speaker ||
    original.original_text !== current.original_text ||
    original.translated_text !== current.translated_text ||
    original.voice_id !== current.voice_id ||
    original.emotion !== current.emotion ||
    original.speed !== current.speed
  )
}

// 状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'processing':
    case 'translating':
    case 'tts_processing': return 'warning'
    case 'failed': return 'danger'
    case 'silent': return 'info'
    default: return ''
  }
}

// 状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '待处理'
    case 'translating': return '翻译中'
    case 'translated': return '已翻译'
    case 'tts_processing': return 'TTS中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'silent': return '静音'
    default: return status
  }
}

// 格式化时长
const formatDuration = (duration: number) => {
  return duration ? duration.toFixed(2) : '0.00'
}

// 播放音频
const playAudio = () => {
  if (props.segment.translated_audio_url) {
    const audio = new Audio(props.segment.translated_audio_url)
    audio.play()
  }
}
</script>

<style scoped>
.segment-index {
  font-weight: 600;
  color: #409eff;
}

.time-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.time-group label {
  font-size: 12px;
  color: #606266;
  width: 30px;
}

.voice-settings {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.duration-info {
  font-size: 12px;
  color: #606266;
}

.duration-info > div {
  margin-bottom: 2px;
}

.row-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
</style>