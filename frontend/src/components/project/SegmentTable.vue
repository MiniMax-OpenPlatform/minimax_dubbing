<template>
  <div class="segment-table-container">
    <!-- 批量操作工具栏 -->
    <BatchOperations
      :selected-segments="selectedSegments"
      :loading-states="{ translate: false, tts: batchTtsLoading }"
      @batch-translate="handleBatchTranslate"
      @batch-tts="$emit('batchTts')"
      @batch-set-voice="handleBatchSetVoice"
      @batch-set-emotion="handleBatchSetEmotion"
      @batch-set-speed="handleBatchSetSpeed"
      @batch-set-speaker="handleBatchSetSpeaker"
      @batch-delete="handleBatchDelete"
      @export-srt="handleExportSrt"
      @export-csv="handleExportCsv"
      @export-audio="handleExportAudio"
      @clear-selection="clearSelection"
    />

    <!-- 段落数据表格 -->
    <el-table
      ref="segmentTable"
      :data="segments"
      style="width: 100%"
      :height="tableHeight"
      stripe
      border
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
      :row-class-name="getRowClassName"
    >
      <!-- 选择列 -->
      <el-table-column type="selection" width="55" />

      <!-- 序号列 -->
      <el-table-column prop="index" label="序号" width="60" />

      <!-- 时间列 -->
      <el-table-column label="时间" width="220">
        <template #default="{ row }">
          <div class="time-display">
            <div class="time-group">
              <label>开始:</label>
              <span>{{ row.start_time }}</span>
            </div>
            <div class="time-group">
              <label>结束:</label>
              <span>{{ row.end_time }}</span>
            </div>
            <div class="time-group">
              <label>时长:</label>
              <span>{{ formatDuration(row.duration) }}s</span>
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 说话人列 -->
      <el-table-column prop="speaker" label="说话人" width="100">
        <template #default="{ row }">
          <el-tag size="small" v-if="row.speaker">{{ row.speaker }}</el-tag>
          <span v-else class="empty-value">-</span>
        </template>
      </el-table-column>

      <!-- 原文列 -->
      <el-table-column label="原文" min-width="200">
        <template #default="{ row }">
          <div class="text-content">
            <p>{{ row.original_text }}</p>
          </div>
        </template>
      </el-table-column>

      <!-- 译文列 -->
      <el-table-column label="译文" min-width="200">
        <template #default="{ row }">
          <div class="text-content">
            <p v-if="row.translated_text">{{ row.translated_text }}</p>
            <span v-else class="empty-value">待翻译</span>
          </div>
        </template>
      </el-table-column>

      <!-- 语音设置列 -->
      <el-table-column label="语音设置" width="150">
        <template #default="{ row }">
          <div class="voice-info">
            <div v-if="row.voice_id">
              <el-tag type="info" size="small">{{ getVoiceName(row.voice_id) }}</el-tag>
            </div>
            <div v-if="row.emotion">
              <el-tag type="warning" size="small">{{ getEmotionName(row.emotion) }}</el-tag>
            </div>
            <div v-if="row.speed && row.speed !== 1.0">
              <el-tag size="small">{{ row.speed }}x</el-tag>
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 状态列 -->
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag
            :type="getStatusType(row.status)"
            size="small"
          >
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 时长信息列 -->
      <el-table-column label="时长对比" width="120">
        <template #default="{ row }">
          <div class="duration-info">
            <div>原: {{ formatDuration(row.duration) }}s</div>
            <div v-if="row.t_tts_duration">
              TTS: {{ formatDuration(row.t_tts_duration) }}s
            </div>
            <div v-if="row.ratio" :class="getRatioClass(row.ratio)">
              比例: {{ row.ratio.toFixed(2) }}
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <el-button
              size="small"
              type="primary"
              @click="handleSingleTts(row)"
              :disabled="!row.translated_text"
            >
              TTS
            </el-button>
            <el-button
              size="small"
              v-if="row.translated_audio_url"
              @click="playAudio(row.translated_audio_url)"
            >
              播放
            </el-button>
            <el-button
              size="small"
              type="text"
              @click="editSegment(row)"
            >
              编辑
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑对话框 -->
    <SegmentEditDialog
      :visible="showEditDialog"
      :segment="editingSegment"
      @close="showEditDialog = false"
      @save="handleSaveSegment"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BatchOperations from './BatchOperations.vue'
import SegmentEditDialog from './SegmentEditDialog.vue'

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
  segments: Segment[]
  tableHeight: number
  batchTtsLoading: boolean
}>()

const emit = defineEmits<{
  updateSegment: [segment: Segment]
  batchTts: []
  rowClick: [segment: Segment]
}>()

// 响应式数据
const selectedSegments = ref<Segment[]>([])
const showEditDialog = ref(false)
const editingSegment = ref<Segment | null>(null)

// 选择变化处理
const handleSelectionChange = (selection: Segment[]) => {
  selectedSegments.value = selection
}

// 行点击处理
const handleRowClick = (row: Segment) => {
  emit('rowClick', row)
}

// 清除选择
const clearSelection = () => {
  selectedSegments.value = []
}

// 行样式
const getRowClassName = ({ row }: { row: Segment }) => {
  return `segment-row segment-row--${row.status}`
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

// 音色名称
const getVoiceName = (voiceId: string) => {
  const voiceMap: Record<string, string> = {
    'female_001': '通用女声',
    'male_001': '通用男声',
    'female_002': '温柔女声',
    'male_002': '磁性男声'
  }
  return voiceMap[voiceId] || voiceId
}

// 情感名称
const getEmotionName = (emotion: string) => {
  const emotionMap: Record<string, string> = {
    'calm': '平静',
    'happy': '开心',
    'sad': '悲伤',
    'angry': '愤怒'
  }
  return emotionMap[emotion] || emotion
}

// 格式化时长
const formatDuration = (duration: number) => {
  return duration ? duration.toFixed(2) : '0.00'
}

// 比例样式
const getRatioClass = (ratio: number) => {
  if (ratio > 1.2) return 'ratio-high'
  if (ratio < 0.8) return 'ratio-low'
  return 'ratio-normal'
}

// 播放音频
const playAudio = (audioUrl: string) => {
  const audio = new Audio(audioUrl)
  audio.play().catch(() => {
    ElMessage.error('音频播放失败')
  })
}

// 编辑段落
const editSegment = (segment: Segment) => {
  editingSegment.value = { ...segment }
  showEditDialog.value = true
}

// 保存段落
const handleSaveSegment = (segment: Segment) => {
  emit('updateSegment', segment)
  showEditDialog.value = false
}

// 单个TTS
const handleSingleTts = (segment: Segment) => {
  // 这里可以添加单个TTS的逻辑
  console.log('Single TTS for segment:', segment.id)
}

// 批量操作处理
const handleBatchTranslate = () => {
  console.log('Batch translate:', selectedSegments.value.length)
}

const handleBatchSetVoice = (voiceId: string) => {
  console.log('Batch set voice:', voiceId, selectedSegments.value.length)
}

const handleBatchSetEmotion = (emotion: string) => {
  console.log('Batch set emotion:', emotion, selectedSegments.value.length)
}

const handleBatchSetSpeed = (speed: number) => {
  console.log('Batch set speed:', speed, selectedSegments.value.length)
}

const handleBatchSetSpeaker = (speaker: string) => {
  console.log('Batch set speaker:', speaker, selectedSegments.value.length)
}

const handleBatchDelete = () => {
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedSegments.value.length} 个段落吗？`,
    '批量删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    console.log('Batch delete confirmed')
  })
}

const handleExportSrt = () => {
  console.log('Export SRT:', selectedSegments.value.length)
}

const handleExportCsv = () => {
  console.log('Export CSV:', selectedSegments.value.length)
}

const handleExportAudio = () => {
  console.log('Export Audio:', selectedSegments.value.length)
}
</script>

<style scoped>
.segment-table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.time-display {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.time-group {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.time-group label {
  color: #606266;
  width: 30px;
}

.text-content {
  max-height: 60px;
  overflow: hidden;
}

.text-content p {
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
}

.empty-value {
  color: #c0c4cc;
  font-style: italic;
}

.voice-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.duration-info {
  font-size: 12px;
}

.duration-info > div {
  margin-bottom: 2px;
}

.ratio-high {
  color: #f56c6c;
}

.ratio-low {
  color: #e6a23c;
}

.ratio-normal {
  color: #67c23a;
}

.row-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* 行状态样式 */
.segment-row--pending {
  background-color: #fdf6ec;
}

.segment-row--translated {
  background-color: #f0f9ff;
}

.segment-row--completed {
  background-color: #f0f9f0;
}

.segment-row--failed {
  background-color: #fef0f0;
}
</style>