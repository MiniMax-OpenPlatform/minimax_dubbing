<template>
  <div class="inline-edit-table">
    <el-table
      ref="tableRef"
      :data="segments"
      :height="tableHeight"
      stripe
      border
      @selection-change="$emit('selection-change', $event)"
      :row-class-name="getRowClassName"
    >
      <!-- 选择列 -->
      <el-table-column type="selection" width="55" fixed="left" />

      <!-- 序号列 -->
      <el-table-column prop="index" label="序号" width="60" fixed="left" />

      <!-- 时间列 -->
      <el-table-column label="时间" width="180" fixed="left">
        <template #default="{ row }">
          <div class="time-display">
            <div>{{ row.start_time }} - {{ row.end_time }}</div>
            <div class="duration">时长: {{ formatDuration(row.duration) }}s</div>
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
            @change="handleFieldChange(row, 'speaker', $event)"
          >
            <el-option label="说话人1" value="speaker1" />
            <el-option label="说话人2" value="speaker2" />
            <el-option label="旁白" value="narrator" />
            <el-option label="其他" value="other" />
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

      <!-- 音色设置列 - 行内编辑 -->
      <el-table-column label="音色" width="140">
        <template #default="{ row }">
          <el-select
            v-model="row.voice_id"
            size="small"
            placeholder="选择音色"
            style="width: 100%"
            @change="handleFieldChange(row, 'voice_id', $event)"
          >
            <el-option label="男声-清澈" value="male-qn-qingse" />
            <el-option label="女声-甜美" value="female-shaonv" />
            <el-option label="男声-磁性" value="male-qn-jingying" />
            <el-option label="女声-温柔" value="female-gentle" />
          </el-select>
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
            <el-option label="自然" value="neutral" />
            <el-option label="开心" value="happy" />
            <el-option label="悲伤" value="sad" />
            <el-option label="愤怒" value="angry" />
            <el-option label="惊讶" value="surprised" />
          </el-select>
        </template>
      </el-table-column>

      <!-- 语速设置列 - 行内编辑 -->
      <el-table-column label="语速" width="100">
        <template #default="{ row }">
          <el-input-number
            v-model="row.speed"
            size="small"
            :min="0.5"
            :max="2.0"
            :step="0.1"
            :precision="1"
            style="width: 100%"
            @change="handleFieldChange(row, 'speed', $event)"
          />
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
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <el-button
              size="small"
              type="primary"
              @click="generateTTS(row)"
              :disabled="!row.translated_text"
              :loading="row._ttsLoading"
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

            <el-dropdown trigger="click" size="small">
              <el-button size="small">
                更多
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="duplicateRow(row)">
                    复制段落
                  </el-dropdown-item>
                  <el-dropdown-item @click="resetRow(row)">
                    重置设置
                  </el-dropdown-item>
                  <el-dropdown-item @click="deleteRow(row)" divided>
                    删除段落
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
}

interface Props {
  segments: Segment[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'selection-change': [segments: Segment[]]
  'field-change': [segment: Segment, field: string, value: any]
  'translate-single': [segment: Segment]
  'generate-tts': [segment: Segment]
  'play-audio': [url: string]
  'duplicate-row': [segment: Segment]
  'delete-row': [segment: Segment]
}>()

const tableRef = ref()
const tableHeight = computed(() => 'calc(100vh - 250px)')

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
  emit('play-audio', url)
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