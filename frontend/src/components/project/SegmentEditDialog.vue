<template>
  <el-dialog
    title="编辑段落"
    :model-value="visible"
    width="800px"
    @close="$emit('close')"
    @update:model-value="$emit('close')"
  >
    <div class="segment-edit-form" v-if="segment">
      <el-form :model="localSegment" label-width="80px">
        <!-- 基本信息 -->
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="序号">
              <el-input-number
                v-model="localSegment.index"
                :min="1"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开始时间">
              <el-input
                v-model="localSegment.start_time"
                placeholder="00:00:00,000"
                size="small"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="结束时间">
              <el-input
                v-model="localSegment.end_time"
                placeholder="00:00:00,000"
                size="small"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 说话人 -->
        <el-form-item label="说话人">
          <el-input
            v-model="localSegment.speaker"
            placeholder="输入说话人名称"
            size="small"
            style="width: 200px"
          />
        </el-form-item>

        <!-- 文本内容 -->
        <el-form-item label="原文">
          <el-input
            v-model="localSegment.original_text"
            type="textarea"
            :rows="4"
            placeholder="输入原文内容"
          />
        </el-form-item>

        <el-form-item label="译文">
          <el-input
            v-model="localSegment.translated_text"
            type="textarea"
            :rows="4"
            placeholder="输入翻译内容"
          />
        </el-form-item>

        <!-- 语音设置 -->
        <el-divider content-position="left">语音设置</el-divider>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="音色">
              <el-select
                v-model="localSegment.voice_id"
                placeholder="选择音色"
                size="small"
                style="width: 100%"
              >
                <el-option label="通用女声" value="female_001" />
                <el-option label="通用男声" value="male_001" />
                <el-option label="温柔女声" value="female_002" />
                <el-option label="磁性男声" value="male_002" />
                <el-option label="甜美女声" value="female_003" />
                <el-option label="成熟男声" value="male_003" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="情感">
              <el-select
                v-model="localSegment.emotion"
                placeholder="选择情感"
                size="small"
                style="width: 100%"
              >
                <el-option label="平静" value="calm" />
                <el-option label="开心" value="happy" />
                <el-option label="悲伤" value="sad" />
                <el-option label="愤怒" value="angry" />
                <el-option label="兴奋" value="excited" />
                <el-option label="温柔" value="gentle" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="语速">
              <el-input-number
                v-model="localSegment.speed"
                :min="0.5"
                :max="2.0"
                :step="0.1"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 状态信息 -->
        <el-divider content-position="left">状态信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="当前状态">
              <el-tag :type="getStatusType(localSegment.status)">
                {{ getStatusText(localSegment.status) }}
              </el-tag>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="原时长">
              <span>{{ formatDuration(localSegment.duration) }}秒</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="TTS时长" v-if="localSegment.t_tts_duration">
              <span>{{ formatDuration(localSegment.t_tts_duration) }}秒</span>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 音频预览 -->
        <el-form-item label="音频预览" v-if="localSegment.translated_audio_url">
          <div class="audio-preview">
            <audio :src="localSegment.translated_audio_url" controls style="width: 100%"></audio>
            <div class="audio-info">
              <span>时长比例: {{ localSegment.ratio?.toFixed(2) || 'N/A' }}</span>
              <el-tag
                :type="getRatioType(localSegment.ratio)"
                size="small"
                style="margin-left: 8px"
              >
                {{ getRatioText(localSegment.ratio) }}
              </el-tag>
            </div>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="$emit('close')">
          取消
        </el-button>
        <el-button type="primary" @click="handleSave">
          保存
        </el-button>
        <el-button
          type="success"
          @click="handleSaveAndTts"
          :disabled="!localSegment.translated_text"
        >
          保存并TTS
        </el-button>
      </div>
    </template>
  </el-dialog>
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
  visible: boolean
  segment: Segment | null
}>()

const emit = defineEmits<{
  close: []
  save: [segment: Segment]
  saveAndTts: [segment: Segment]
}>()

const localSegment = ref<Segment>({
  id: 0,
  index: 0,
  start_time: '',
  end_time: '',
  duration: 0,
  speaker: '',
  original_text: '',
  translated_text: '',
  voice_id: '',
  emotion: '',
  speed: 1.0,
  translated_audio_url: '',
  t_tts_duration: 0,
  ratio: 0,
  status: 'pending'
})

// 监听props变化
watch(() => props.segment, (newSegment) => {
  if (newSegment) {
    localSegment.value = { ...newSegment }
  }
}, { immediate: true })

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

// 比例类型
const getRatioType = (ratio: number) => {
  if (!ratio) return ''
  if (ratio > 1.2) return 'danger'
  if (ratio < 0.8) return 'warning'
  return 'success'
}

// 比例文本
const getRatioText = (ratio: number) => {
  if (!ratio) return 'N/A'
  if (ratio > 1.2) return '过长'
  if (ratio < 0.8) return '过短'
  return '正常'
}

// 保存
const handleSave = () => {
  emit('save', { ...localSegment.value })
}

// 保存并TTS
const handleSaveAndTts = () => {
  emit('saveAndTts', { ...localSegment.value })
}
</script>

<style scoped>
.segment-edit-form {
  padding: 8px 0;
}

.audio-preview {
  width: 100%;
}

.audio-info {
  display: flex;
  align-items: center;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>