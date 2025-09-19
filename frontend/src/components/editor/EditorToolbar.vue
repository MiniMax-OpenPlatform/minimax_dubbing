<template>
  <div class="editor-toolbar">
    <div class="toolbar-left">
      <div class="selection-info">
        已选择 <strong>{{ selectedCount }}</strong> / {{ totalCount }} 个段落
      </div>

      <el-button-group v-if="selectedCount > 0">
        <el-button
          type="primary"
          @click="$emit('batch-translate')"
          :loading="batchLoading"
        >
          批量翻译 ({{ selectedCount }})
        </el-button>

        <el-button
          type="success"
          @click="$emit('batch-tts')"
          :loading="batchLoading"
        >
          批量TTS ({{ selectedCount }})
        </el-button>
      </el-button-group>
    </div>

    <div class="toolbar-center">
      <!-- 筛选器 -->
      <el-select
        v-model="statusFilter"
        placeholder="按状态筛选"
        style="width: 140px"
        clearable
        @change="handleFilterChange"
      >
        <el-option label="全部" value="" />
        <el-option label="待处理" value="pending" />
        <el-option label="已翻译" value="translated" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>

      <el-input
        v-model="textFilter"
        placeholder="搜索文本内容"
        style="width: 200px; margin-left: 8px"
        clearable
        @input="handleFilterChange"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="toolbar-right">
      <el-button-group>
        <el-button @click="$emit('save-all')" :disabled="!hasUnsavedChanges">
          保存全部
        </el-button>

        <el-button @click="$emit('undo')" :disabled="!canUndo">
          撤销
        </el-button>

        <el-button @click="$emit('redo')" :disabled="!canRedo">
          重做
        </el-button>
      </el-button-group>

      <el-dropdown trigger="click" style="margin-left: 8px">
        <el-button>
          导出
          <el-icon><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleExport('srt')">
              导出SRT字幕
            </el-dropdown-item>
            <el-dropdown-item @click="handleExport('csv')">
              导出CSV表格
            </el-dropdown-item>
            <el-dropdown-item @click="handleExport('audio')" divided>
              导出拼接音频
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-button
        v-if="selectedCount > 0"
        type="danger"
        @click="$emit('clear-selection')"
        style="margin-left: 8px"
      >
        清除选择
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search, ArrowDown } from '@element-plus/icons-vue'

interface Props {
  selectedCount: number
  totalCount: number
  batchLoading?: boolean
  hasUnsavedChanges?: boolean
  canUndo?: boolean
  canRedo?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'batch-translate': []
  'batch-tts': []
  'save-all': []
  'undo': []
  'redo': []
  'export': [type: string]
  'filter-change': [filters: { status: string; text: string }]
  'clear-selection': []
}>()

const statusFilter = ref('')
const textFilter = ref('')

const handleFilterChange = () => {
  emit('filter-change', {
    status: statusFilter.value,
    text: textFilter.value
  })
}

const handleExport = (type: string) => {
  emit('export', type)
}
</script>

<style scoped>
.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  border-radius: 8px 8px 0 0;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.selection-info {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.selection-info strong {
  color: #409eff;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .editor-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .toolbar-center {
    flex-direction: column;
    width: 100%;
  }

  .toolbar-center .el-select,
  .toolbar-center .el-input {
    width: 100% !important;
  }
}
</style>