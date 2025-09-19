<template>
  <div class="editable-table">
    <el-table
      ref="tableRef"
      :data="segments"
      :height="tableHeight"
      stripe
      border
      @selection-change="$emit('selection-change', $event)"
      @row-click="handleRowClick"
      :row-class-name="getRowClassName"
    >
      <!-- 选择列 -->
      <el-table-column type="selection" width="55" fixed="left" />

      <!-- 序号列 -->
      <el-table-column prop="index" label="序号" width="70" fixed="left" />

      <!-- 时间列 -->
      <el-table-column label="时间" width="200" fixed="left">
        <template #default="{ row }">
          <TimeDisplay :segment="row" />
        </template>
      </el-table-column>

      <!-- 说话人列 -->
      <el-table-column label="说话人" width="120">
        <template #default="{ row }">
          <EditableCell
            v-if="editingRow === row.id"
            :value="row.speaker"
            type="select"
            :options="speakerOptions"
            @change="handleCellChange(row.id, 'speaker', $event)"
            @save="handleSave(row)"
            @cancel="handleCancel(row)"
          />
          <el-tag v-else size="small" v-if="row.speaker">{{ row.speaker }}</el-tag>
          <span v-else class="empty-value">-</span>
        </template>
      </el-table-column>

      <!-- 原文列 -->
      <el-table-column label="原文" min-width="250">
        <template #default="{ row }">
          <EditableCell
            v-if="editingRow === row.id"
            :value="row.original_text"
            type="textarea"
            :max-length="500"
            @change="handleCellChange(row.id, 'original_text', $event)"
            @save="handleSave(row)"
            @cancel="handleCancel(row)"
          />
          <div v-else class="text-content" @dblclick="startEdit(row.id)">
            <p>{{ row.original_text }}</p>
          </div>
        </template>
      </el-table-column>

      <!-- 译文列 -->
      <el-table-column label="译文" min-width="250">
        <template #default="{ row }">
          <EditableCell
            v-if="editingRow === row.id"
            :value="row.translated_text"
            type="textarea"
            :max-length="500"
            :error="validationErrors[row.id]?.translated_text"
            @change="handleCellChange(row.id, 'translated_text', $event)"
            @save="handleSave(row)"
            @cancel="handleCancel(row)"
          />
          <div v-else class="text-content" @dblclick="startEdit(row.id)">
            <p v-if="row.translated_text">{{ row.translated_text }}</p>
            <span v-else class="empty-value">待翻译</span>
          </div>
        </template>
      </el-table-column>

      <!-- 语音设置列 -->
      <el-table-column label="语音设置" width="180">
        <template #default="{ row }">
          <VoiceSettings
            v-if="editingRow === row.id"
            :voice-id="row.voice_id"
            :emotion="row.emotion"
            :speed="row.speed"
            @voice-change="handleCellChange(row.id, 'voice_id', $event)"
            @emotion-change="handleCellChange(row.id, 'emotion', $event)"
            @speed-change="handleCellChange(row.id, 'speed', $event)"
            @save="handleSave(row)"
            @cancel="handleCancel(row)"
          />
          <VoiceInfo v-else :segment="row" @edit="startEdit(row.id)" />
        </template>
      </el-table-column>

      <!-- 状态列 -->
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>

      <!-- 时长对比列 -->
      <el-table-column label="时长对比" width="130">
        <template #default="{ row }">
          <DurationComparison :segment="row" />
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <template v-if="editingRow === row.id">
              <el-button size="small" type="primary" @click="handleSave(row)">
                保存
              </el-button>
              <el-button size="small" @click="handleCancel(row)">
                取消
              </el-button>
            </template>
            <template v-else>
              <el-button size="small" @click="startEdit(row.id)">
                编辑
              </el-button>
              <el-button
                size="small"
                type="primary"
                @click="$emit('single-tts', row)"
                :disabled="!row.translated_text"
              >
                TTS
              </el-button>
              <el-button
                size="small"
                v-if="row.translated_audio_url"
                @click="$emit('play-audio', row.translated_audio_url)"
              >
                播放
              </el-button>
            </template>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

// 导入子组件
import EditableCell from './EditableCell.vue'
import VoiceSettings from './VoiceSettings.vue'
import VoiceInfo from './VoiceInfo.vue'
import TimeDisplay from './TimeDisplay.vue'
import StatusTag from './StatusTag.vue'
import DurationComparison from './DurationComparison.vue'

interface Props {
  segments: Segment[]
  selectedSegments: Segment[]
  editingRow?: number
  validationErrors: Record<number, Record<string, string>>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'selection-change': [segments: Segment[]]
  'row-edit': [rowId: number]
  'row-save': [segment: Segment]
  'row-cancel': [rowId: number]
  'cell-change': [rowId: number, field: string, value: any]
  'play-audio': [url: string]
  'single-tts': [segment: Segment]
}>()

const tableRef = ref()
const tableHeight = computed(() => 'calc(100vh - 300px)')

// 编辑状态
const editingSegmentData = ref<Record<number, Partial<Segment>>>({})

// 说话人选项
const speakerOptions = [
  { label: '说话人1', value: 'speaker1' },
  { label: '说话人2', value: 'speaker2' },
  { label: '旁白', value: 'narrator' }
]

const getRowClassName = ({ row }: { row: Segment }) => {
  const classes = []

  if (props.editingRow === row.id) {
    classes.push('editing-row')
  }

  if (row.status === 'failed') {
    classes.push('error-row')
  } else if (row.status === 'completed') {
    classes.push('completed-row')
  }

  return classes.join(' ')
}

const handleRowClick = (row: Segment) => {
  // 单击行选中
  tableRef.value.toggleRowSelection(row)
}

const startEdit = (rowId: number) => {
  const segment = props.segments.find(s => s.id === rowId)
  if (segment) {
    // 保存当前编辑状态
    editingSegmentData.value[rowId] = { ...segment }
    emit('row-edit', rowId)
  }
}

const handleCellChange = (rowId: number, field: string, value: any) => {
  if (!editingSegmentData.value[rowId]) {
    editingSegmentData.value[rowId] = {}
  }
  editingSegmentData.value[rowId][field] = value
  emit('cell-change', rowId, field, value)
}

const handleSave = (row: Segment) => {
  const updates = editingSegmentData.value[row.id]
  if (updates) {
    const updatedSegment = { ...row, ...updates }
    emit('row-save', updatedSegment)
    delete editingSegmentData.value[row.id]
  }
}

const handleCancel = (row: Segment) => {
  delete editingSegmentData.value[row.id]
  emit('row-cancel', row.id)
}
</script>

<style scoped>
.editable-table {
  flex: 1;
  overflow: hidden;
}

.text-content {
  padding: 4px;
  min-height: 20px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.text-content:hover {
  background-color: #f5f7fa;
}

.text-content p {
  margin: 0;
  line-height: 1.4;
  word-break: break-word;
}

.empty-value {
  color: #c0c4cc;
  font-style: italic;
}

.row-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* 行状态样式 */
:deep(.editing-row) {
  background-color: #f0f9ff !important;
}

:deep(.error-row) {
  background-color: #fef2f2 !important;
}

:deep(.completed-row) {
  background-color: #f0fdf4 !important;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}
</style>