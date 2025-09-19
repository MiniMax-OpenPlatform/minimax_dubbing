<template>
  <div class="inline-edit-table">
    <el-table
      ref="tableRef"
      :data="segments"
      :height="computedTableHeight"
      stripe
      border
      @selection-change="$emit('selection-change', $event)"
      :row-class-name="getRowClassName"
    >
      <!-- 选择列 -->
      <el-table-column type="selection" width="55" fixed="left" />

      <!-- 序号列 -->
      <el-table-column prop="index" label="序号" width="60" fixed="left" />

      <!-- 时间列 - 可编辑时间戳 -->
      <el-table-column label="时间戳" width="220">
        <template #default="{ row }">
          <div class="time-edit-group">
            <div class="time-input-row">
              <label>开始:</label>
              <el-input
                :model-value="formatTimestamp(row.start_time)"
                size="small"
                placeholder="HH:MM:SS,mmm"
                @blur="handleTimestampChange(row, 'start_time', $event.target.value)"
                @keydown.enter="handleTimestampChange(row, 'start_time', $event.target.value)"
                style="width: 95px;"
              />
            </div>
            <div class="time-input-row">
              <label>结束:</label>
              <el-input
                :model-value="formatTimestamp(row.end_time)"
                size="small"
                placeholder="HH:MM:SS,mmm"
                @blur="handleTimestampChange(row, 'end_time', $event.target.value)"
                @keydown.enter="handleTimestampChange(row, 'end_time', $event.target.value)"
                style="width: 95px;"
              />
            </div>
            <div class="duration-display">时长: {{ formatDuration(row.duration) }}s</div>
          </div>
        </template>
      </el-table-column>

      <!-- 说话人列 - 行内编辑 -->
      <el-table-column label="说话人" width="120">
        <template #default="{ row }">
          <el-select
            v-model="row.speaker"
            size="small"
            placeholder="选择说话人"
            style="width: 100%"
            @change="handleSpeakerChange(row, $event)"
          >
            <el-option
              v-for="mapping in getProjectSpeakerOptions()"
              :key="mapping.speaker"
              :label="mapping.speaker"
              :value="mapping.speaker"
            />
          </el-select>
        </template>
      </el-table-column>

      <!-- 原文列 - 行内编辑 -->
      <el-table-column label="原文" min-width="250">
        <template #default="{ row }">
          <el-input
            v-model="row.original_text"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="输入原文内容"
            @blur="handleFieldChange(row, 'original_text', row.original_text)"
            @keydown.ctrl.enter="handleFieldChange(row, 'original_text', row.original_text)"
          />
        </template>
      </el-table-column>

      <!-- 译文列 - 行内编辑 -->
      <el-table-column label="译文" min-width="250">
        <template #default="{ row }">
          <el-input
            v-model="row.translated_text"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="输入译文内容或点击翻译"
            @blur="handleFieldChange(row, 'translated_text', row.translated_text)"
            @keydown.ctrl.enter="handleFieldChange(row, 'translated_text', row.translated_text)"
          >
            <template #suffix>
              <el-button
                v-if="row.original_text && !row.translated_text"
                size="small"
                type="primary"
                @click="translateSingle(row)"
                :loading="row._translating"
              >
                翻译
              </el-button>
            </template>
          </el-input>
        </template>
      </el-table-column>

      <!-- 音色配置列 - 只读（来自项目配置） -->
      <el-table-column label="音色ID" width="140">
        <template #default="{ row }">
          <el-tag size="small" type="info">
            {{ getVoiceDisplayName(row.voice_id, row.speaker) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 情感设置列 - 行内编辑 -->
      <el-table-column label="情感" width="120">
        <template #default="{ row }">
          <el-select
            v-model="row.emotion"
            size="small"
            placeholder="选择情感"
            style="width: 100%"
            @change="handleFieldChange(row, 'emotion', $event)"
          >
            <el-option label="自动" value="auto" />
            <el-option label="高兴" value="happy" />
            <el-option label="悲伤" value="sad" />
            <el-option label="愤怒" value="angry" />
            <el-option label="恐惧" value="fearful" />
            <el-option label="厌恶" value="disgusted" />
            <el-option label="惊讶" value="surprised" />
            <el-option label="平静" value="calm" />
          </el-select>
        </template>
      </el-table-column>

      <!-- 语速设置列 - 行内编辑 -->
      <el-table-column label="语速" width="100">
        <template #default="{ row }">
          <el-input
            :model-value="formatSpeed(row.speed)"
            size="small"
            placeholder="1.00"
            @blur="handleSpeedChange(row, $event.target.value)"
            @keydown.enter="handleSpeedChange(row, $event.target.value)"
            style="width: 100%"
          />
        </template>
      </el-table-column>

      <!-- 时长对比列 -->
      <el-table-column label="时长对比" width="130">
        <template #default="{ row }">
          <div class="duration-info">
            <div>原: {{ formatDuration(row.duration) }}s</div>
            <div v-if="row.t_tts_duration" class="tts-duration">
              TTS: {{ formatDuration(row.t_tts_duration) }}s
            </div>
            <div v-if="row.ratio" :class="getRatioClass(row.ratio)">
              比例: {{ row.ratio.toFixed(2) }}
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <div class="row-actions grid">
            <div class="button-row">
              <el-button
                size="small"
                type="primary"
                @click="generateTTS(row)"
                :disabled="!row.translated_text"
                :loading="row._ttsLoading"
                class="action-btn-small"
              >
                TTS
              </el-button>
              <el-button
                size="small"
                @click="playAudio(row.translated_audio_url)"
                :disabled="!row.translated_audio_url"
                class="action-btn-small"
              >
                播放
              </el-button>
            </div>
            <div class="button-row">
              <el-button
                size="small"
                type="warning"
                @click="shortenTranslation(row)"
                :disabled="!row.translated_text"
                :loading="row._shortenLoading"
                class="action-btn-small"
              >
                缩短
              </el-button>
              <el-button
                size="small"
                type="success"
                @click="lengthenTranslation(row)"
                :disabled="!row.translated_text"
                :loading="row._lengthenLoading"
                class="action-btn-small"
              >
                加长
              </el-button>
            </div>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'

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
  _translating?: boolean
  _ttsLoading?: boolean
  _shortenLoading?: boolean
  _lengthenLoading?: boolean
}

interface Props {
  segments: Segment[]
  tableHeight?: number
  projectId: number
  project?: any
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'selection-change': [segments: Segment[]]
  'field-change': [segment: Segment, field: string, value: any]
  'translate-single': [segment: Segment]
  'generate-tts': [segment: Segment]
  'shorten-translation': [segment: Segment]
  'lengthen-translation': [segment: Segment]
  'segment-click': [segment: Segment]
}>()

const tableRef = ref()
const computedTableHeight = computed(() => props.tableHeight || 600)

// 字段变更处理 - 自动保存
const handleFieldChange = async (segment: Segment, field: string, value: any) => {
  // 立即更新本地数据
  segment[field] = value

  // 显示保存中状态
  const originalStatus = segment.status
  segment.status = 'saving'

  try {
    // 调用API保存
    emit('field-change', segment, field, value)

    // 短暂显示保存成功
    await nextTick()
    setTimeout(() => {
      segment.status = originalStatus
    }, 500)

  } catch (error) {
    ElMessage.error('保存失败')
    segment.status = originalStatus
  }
}

// 语速格式化 - 显示两位小数
const formatSpeed = (speed: number): string => {
  if (speed === null || speed === undefined || isNaN(speed)) {
    return '1.00'
  }
  return speed.toFixed(2)
}

// 语速变更处理 - 验证数值范围
const handleSpeedChange = async (segment: Segment, value: any) => {
  let speed = parseFloat(value)

  // 验证数值范围
  if (isNaN(speed)) {
    speed = 1.00
    ElMessage.warning('语速必须是数字，已重置为1.00')
  } else if (speed < 0.50) {
    speed = 0.50
    ElMessage.warning('语速不能小于0.50')
  } else if (speed > 2.00) {
    speed = 2.00
    ElMessage.warning('语速不能大于2.00')
  }

  // 保留两位小数
  speed = Math.round(speed * 100) / 100
  segment.speed = speed

  // 调用通用保存方法
  await handleFieldChange(segment, 'speed', speed)
}

// 时间戳格式转换 - 转换为SRT标准格式 HH:MM:SS,mmm
const formatTimestamp = (timestamp: string): string => {
  if (!timestamp) return '00:00:00,000'

  // 如果已经是正确格式，直接返回
  if (/^\d{2}:\d{2}:\d{2},\d{3}$/.test(timestamp)) {
    return timestamp
  }

  // 如果是数字（秒），转换为HH:MM:SS,mmm格式
  const seconds = parseFloat(timestamp)
  if (!isNaN(seconds)) {
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    const milliseconds = Math.floor((seconds % 1) * 1000)

    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${milliseconds.toString().padStart(3, '0')}`
  }

  // 其他格式尝试解析
  return timestamp || '00:00:00,000'
}

// 时间戳变更处理
const handleTimestampChange = async (segment: Segment, field: string, value: string) => {
  // 验证SRT时间戳格式 HH:MM:SS,mmm
  const srtPattern = /^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/
  const match = value.match(srtPattern)

  if (!match) {
    ElMessage.warning('时间戳格式不正确，请使用 HH:MM:SS,mmm 格式（如：00:01:23,456）')
    return
  }

  const [, hours, minutes, seconds, milliseconds] = match

  // 验证时间值的合理性
  if (parseInt(minutes) >= 60 || parseInt(seconds) >= 60) {
    ElMessage.warning('时间格式不正确：分钟和秒数不能超过59')
    return
  }

  // 转换为秒数存储（如果后端需要的话）
  const totalSeconds = parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds) + parseInt(milliseconds) / 1000

  // 调用通用保存方法，保存原始SRT格式
  await handleFieldChange(segment, field, value)
}

// 单个翻译
const translateSingle = async (segment: Segment) => {
  if (!segment.original_text.trim()) {
    ElMessage.warning('请先输入原文')
    return
  }

  segment._translating = true
  try {
    emit('translate-single', segment)
  } finally {
    segment._translating = false
  }
}

// 生成TTS
const generateTTS = async (segment: Segment) => {
  if (!segment.translated_text.trim()) {
    ElMessage.warning('请先输入译文')
    return
  }

  segment._ttsLoading = true
  try {
    emit('generate-tts', segment)
  } finally {
    segment._ttsLoading = false
  }
}

// 播放音频
const playAudio = (url: string) => {
  const audio = new Audio(url)
  audio.play().catch(() => {
    ElMessage.error('音频播放失败')
  })
}

// 翻译缩短
const shortenTranslation = async (segment: Segment) => {
  if (!segment.translated_text.trim()) {
    ElMessage.warning('请先输入译文')
    return
  }

  segment._shortenLoading = true
  try {
    emit('shorten-translation', segment)
  } finally {
    segment._shortenLoading = false
  }
}

// 翻译加长
const lengthenTranslation = async (segment: Segment) => {
  if (!segment.translated_text.trim()) {
    ElMessage.warning('请先输入译文')
    return
  }

  segment._lengthenLoading = true
  try {
    emit('lengthen-translation', segment)
  } finally {
    segment._lengthenLoading = false
  }
}

// 获取项目中配置的说话人选项
const getProjectSpeakerOptions = () => {
  if (!props.project?.voice_mappings) {
    // 如果没有项目配置，返回默认选项
    return [
      { speaker: '说话人1', voice_id: '' },
      { speaker: '说话人2', voice_id: '' },
      { speaker: '旁白', voice_id: '' }
    ]
  }

  let mappings = props.project.voice_mappings

  // 如果是字符串，尝试解析为JSON
  if (typeof mappings === 'string') {
    try {
      mappings = JSON.parse(mappings)
    } catch {
      return [
        { speaker: '说话人1', voice_id: '' },
        { speaker: '说话人2', voice_id: '' },
        { speaker: '旁白', voice_id: '' }
      ]
    }
  }

  // 返回项目配置的映射
  return Array.isArray(mappings) ? mappings : []
}

// 处理说话人变更，自动设置对应的voice_id
const handleSpeakerChange = async (segment: Segment, speaker: string) => {
  // 先更新说话人
  segment.speaker = speaker

  // 从项目配置中查找对应的voice_id
  const mappings = getProjectSpeakerOptions()
  const mapping = mappings.find(m => m.speaker === speaker)

  if (mapping && mapping.voice_id) {
    segment.voice_id = mapping.voice_id
  }

  // 保存说话人变更
  await handleFieldChange(segment, 'speaker', speaker)

  // 如果找到了对应的voice_id，也保存voice_id
  if (mapping && mapping.voice_id) {
    await handleFieldChange(segment, 'voice_id', mapping.voice_id)
  }
}

// 获取音色显示名称（只显示voice_id）
const getVoiceDisplayName = (voiceId: string, speaker: string) => {
  if (!voiceId) return '未配置'

  // 直接返回voice_id，不显示speaker前缀
  return voiceId
}

// 复制段落
const duplicateRow = (segment: Segment) => {
  emit('duplicate-row', segment)
}

// 重置段落
const resetRow = async (segment: Segment) => {
  try {
    await ElMessageBox.confirm('确定要重置这个段落的所有设置吗？', '确认重置', {
      type: 'warning'
    })

    // 重置语音设置
    segment.voice_id = ''
    segment.emotion = ''
    segment.speed = 1.0
    segment.translated_audio_url = ''
    segment.t_tts_duration = 0
    segment.ratio = 0

    handleFieldChange(segment, 'voice_settings', {
      voice_id: '',
      emotion: '',
      speed: 1.0
    })

    ElMessage.success('段落设置已重置')
  } catch {
    // 用户取消
  }
}

// 删除段落
const deleteRow = async (segment: Segment) => {
  try {
    await ElMessageBox.confirm('确定要删除这个段落吗？', '确认删除', {
      type: 'warning'
    })

    emit('delete-row', segment)
    ElMessage.success('段落已删除')
  } catch {
    // 用户取消
  }
}

// 工具函数
const formatDuration = (seconds: number): string => {
  return seconds ? seconds.toFixed(1) : '0.0'
}

const getStatusType = (status: string) => {
  const statusMap = {
    'pending': '',
    'translating': 'warning',
    'translated': 'info',
    'tts_processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'silent': 'info',
    'saving': 'warning'
  }
  return statusMap[status] || ''
}

const getStatusText = (status: string) => {
  const statusMap = {
    'pending': '待处理',
    'translating': '翻译中',
    'translated': '已翻译',
    'tts_processing': 'TTS中',
    'completed': '已完成',
    'failed': '失败',
    'silent': '静音',
    'saving': '保存中'
  }
  return statusMap[status] || status
}

const getRatioClass = (ratio: number) => {
  if (ratio > 1.2) return 'ratio-high'
  if (ratio < 0.8) return 'ratio-low'
  return 'ratio-normal'
}

const getRowClassName = ({ row }: { row: Segment }) => {
  const classes = []

  if (row.status === 'failed') {
    classes.push('error-row')
  } else if (row.status === 'completed') {
    classes.push('completed-row')
  } else if (row.status === 'saving') {
    classes.push('saving-row')
  }

  return classes.join(' ')
}
</script>

<style scoped>
.inline-edit-table {
  height: 100%;
}

.time-display {
  font-size: 12px;
  line-height: 1.3;
}

.time-edit-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.time-input-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.time-input-row label {
  width: 30px;
  color: #606266;
  font-size: 11px;
}

.duration-display {
  color: #909399;
  font-size: 11px;
  margin-top: 2px;
}

.duration {
  color: #909399;
  margin-top: 2px;
}

.duration-info {
  font-size: 12px;
  line-height: 1.4;
}

.tts-duration {
  color: #67c23a;
  margin-top: 2px;
}

.ratio-high {
  color: #f56c6c;
  font-weight: bold;
}

.ratio-low {
  color: #e6a23c;
  font-weight: bold;
}

.ratio-normal {
  color: #67c23a;
}

.row-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.row-actions.vertical {
  flex-direction: column;
  align-items: stretch;
  gap: 3px;
}

.row-actions.grid {
  display: flex;
  flex-direction: column;
  gap: 3px !important;
  padding: 2px 10px !important;
}

.button-row {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.action-btn-small {
  width: 40px !important;
  font-size: 11px !important;
  padding: 4px 2px !important;
}

/* 行状态样式 */
:deep(.error-row) {
  background-color: #fef2f2;
}

:deep(.completed-row) {
  background-color: #f0fdf4;
}

:deep(.saving-row) {
  background-color: #fefce8;
}

/* 输入框样式优化 */
:deep(.el-textarea__inner) {
  border: 1px solid transparent;
  transition: border-color 0.3s;
}

:deep(.el-textarea__inner:hover) {
  border-color: #c0c4cc;
}

:deep(.el-textarea__inner:focus) {
  border-color: #409eff;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: center;
}
</style>