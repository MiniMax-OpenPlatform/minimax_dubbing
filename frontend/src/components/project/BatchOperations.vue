<template>
  <div class="batch-operations" v-if="selectedCount > 0">
    <div class="selected-info">
      <el-icon><Select /></el-icon>
      <span class="selected-count">已选择 {{ selectedCount }} 项</span>
      <span class="selected-details" v-if="statusCounts">
        (待处理: {{ statusCounts.pending }}, 已翻译: {{ statusCounts.translated }}, 已完成: {{ statusCounts.completed }})
      </span>
    </div>

    <!-- 进度条显示区域 -->
    <BatchProgressBar
      v-if="batchProgress"
      :progress-state="batchProgress.progressState"
      :has-active-progress="batchProgress.hasActiveProgress.value"
      :active-progresses="batchProgress.activeProgresses.value"
      :get-progress-percentage="batchProgress.getProgressPercentage"
      :format-time="batchProgress.formatTime"
      :get-status-text="batchProgress.getStatusText"
      @pause-operation="handlePauseOperation"
      @resume-operation="handleResumeOperation"
      @cancel-operation="handleCancelOperation"
    />

    <div class="batch-actions">
      <!-- 批量翻译 -->
      <el-button
        type="primary"
        size="small"
        :icon="Document"
        @click="$emit('batchTranslate')"
        :disabled="statusCounts.pending === 0"
        :loading="loadingStates.translate"
      >
        批量翻译 ({{ statusCounts.pending }})
      </el-button>

      <!-- 批量TTS -->
      <el-button
        type="success"
        size="small"
        :icon="Microphone"
        @click="$emit('batchTts')"
        :disabled="statusCounts.translated === 0"
        :loading="loadingStates.tts"
      >
        批量TTS ({{ statusCounts.translated }})
      </el-button>

      <!-- 批量设置 -->
      <el-dropdown @command="handleBatchCommand">
        <el-button size="small" :icon="Setting">
          批量设置
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="voice">设置音色</el-dropdown-item>
            <el-dropdown-item command="emotion">设置情感</el-dropdown-item>
            <el-dropdown-item command="speed">设置语速</el-dropdown-item>
            <el-dropdown-item command="speaker">设置说话人</el-dropdown-item>
            <el-dropdown-item divided command="delete">删除选中</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 导出操作 -->
      <el-dropdown @command="handleExportCommand">
        <el-button size="small" :icon="Download">
          导出
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="srt">导出SRT</el-dropdown-item>
            <el-dropdown-item command="csv">导出CSV</el-dropdown-item>
            <el-dropdown-item command="audio">导出音频</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 清除选择 -->
      <el-button
        size="small"
        :icon="Close"
        @click="$emit('clearSelection')"
      >
        清除选择
      </el-button>
    </div>

    <!-- 批量设置对话框 -->
    <BatchSettingsDialog
      :visible="showBatchSettings"
      :setting-type="currentSettingType"
      :selected-count="selectedCount"
      @close="showBatchSettings = false"
      @confirm="handleBatchSettingsConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Select, Document, Microphone, Setting, Download, Close, ArrowDown
} from '@element-plus/icons-vue'
import BatchSettingsDialog from './BatchSettingsDialog.vue'
import BatchProgressBar from '../progress/BatchProgressBar.vue'
import type { UseBatchProgress } from '../../composables/useBatchProgress'

interface Segment {
  id: number
  status: string
  translated_text: string
}

interface StatusCounts {
  pending: number
  translated: number
  completed: number
  failed: number
}

interface LoadingStates {
  translate: boolean
  tts: boolean
}

const props = defineProps<{
  selectedSegments: Segment[]
  loadingStates: LoadingStates
  batchProgress?: UseBatchProgress | null
}>()

const emit = defineEmits<{
  batchTranslate: []
  batchTts: []
  batchSetVoice: [voiceId: string]
  batchSetEmotion: [emotion: string]
  batchSetSpeed: [speed: number]
  batchSetSpeaker: [speaker: string]
  batchDelete: []
  exportSrt: []
  exportCsv: []
  exportAudio: []
  clearSelection: []
  pauseOperation: [type: 'translate' | 'tts']
  resumeOperation: [type: 'translate' | 'tts']
  cancelOperation: [type: 'translate' | 'tts']
}>()

const showBatchSettings = ref(false)
const currentSettingType = ref<'voice' | 'emotion' | 'speed' | 'speaker'>('voice')

// 计算选中数量
const selectedCount = computed(() => props.selectedSegments.length)

// 计算各状态数量
const statusCounts = computed((): StatusCounts => {
  const counts = {
    pending: 0,
    translated: 0,
    completed: 0,
    failed: 0
  }

  props.selectedSegments.forEach(segment => {
    switch (segment.status) {
      case 'pending':
        counts.pending++
        break
      case 'translated':
        if (segment.translated_text) {
          counts.translated++
        }
        break
      case 'completed':
        counts.completed++
        break
      case 'failed':
        counts.failed++
        break
    }
  })

  return counts
})

// 处理批量命令
const handleBatchCommand = (command: string) => {
  switch (command) {
    case 'voice':
      currentSettingType.value = 'voice'
      showBatchSettings.value = true
      break
    case 'emotion':
      currentSettingType.value = 'emotion'
      showBatchSettings.value = true
      break
    case 'speed':
      currentSettingType.value = 'speed'
      showBatchSettings.value = true
      break
    case 'speaker':
      currentSettingType.value = 'speaker'
      showBatchSettings.value = true
      break
    case 'delete':
      emit('batchDelete')
      break
  }
}

// 处理导出命令
const handleExportCommand = (command: string) => {
  switch (command) {
    case 'srt':
      emit('exportSrt')
      break
    case 'csv':
      emit('exportCsv')
      break
    case 'audio':
      emit('exportAudio')
      break
  }
}

// 处理批量设置确认
const handleBatchSettingsConfirm = (value: any) => {
  switch (currentSettingType.value) {
    case 'voice':
      emit('batchSetVoice', value)
      break
    case 'emotion':
      emit('batchSetEmotion', value)
      break
    case 'speed':
      emit('batchSetSpeed', value)
      break
    case 'speaker':
      emit('batchSetSpeaker', value)
      break
  }
  showBatchSettings.value = false
}

// 进度条操作处理
const handlePauseOperation = (type: 'translate' | 'tts') => {
  emit('pauseOperation', type)
}

const handleResumeOperation = (type: 'translate' | 'tts') => {
  emit('resumeOperation', type)
}

const handleCancelOperation = (type: 'translate' | 'tts') => {
  emit('cancelOperation', type)
}
</script>

<style scoped>
.batch-operations {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.selected-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-weight: 500;
}

.selected-count {
  font-size: 16px;
}

.selected-details {
  font-size: 14px;
  color: #606266;
  font-weight: normal;
}

.batch-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .batch-operations {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .selected-info {
    justify-content: center;
  }

  .batch-actions {
    justify-content: center;
  }
}
</style>