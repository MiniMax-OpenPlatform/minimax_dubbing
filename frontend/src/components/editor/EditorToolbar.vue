<template>
  <div class="editor-toolbar">
    <div class="toolbar-left">
      <el-button-group>
        <el-button
          type="primary"
          @click="$emit('batch-translate')"
          :loading="batchLoading"
        >
          批量翻译
        </el-button>

        <el-button
          type="success"
          @click="$emit('batch-tts')"
          :loading="batchLoading"
        >
          批量TTS
        </el-button>

        <el-button
          type="warning"
          @click="$emit('concatenate-audio')"
          :loading="batchLoading"
        >
          拼接音频
        </el-button>
      </el-button-group>
    </div>

    <div class="toolbar-center">
      <!-- 空白区域 -->
    </div>

    <div class="toolbar-right">


      <!-- 上传视频 -->
      <el-upload
        ref="videoUploadRef"
        :show-file-list="false"
        :before-upload="handleUploadVideo"
        accept=".mp4,.avi,.mov,.wmv,.flv,.mkv"
        style="margin-left: 8px"
      >
        <el-button :icon="VideoCamera" type="primary">
          上传视频
        </el-button>
      </el-upload>

      <!-- 说话人管理 -->
      <el-dropdown @command="handleSpeakerCommand" style="margin-left: 8px">
        <el-button :icon="User">
          说话人管理
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="auto-assign">
              自动分配说话人
            </el-dropdown-item>
            <el-dropdown-item command="batch-speaker" divided>
              批量修改说话人
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

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

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, ArrowDown, Upload, User, VideoCamera } from '@element-plus/icons-vue'

interface Props {
  selectedCount: number
  totalCount: number
  batchLoading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'batch-translate': []
  'batch-tts': []
  'concatenate-audio': []
  'export': [type: string]
  'upload-video': [file: File]
  'auto-assign-speaker': []
  'batch-speaker': []
}>()


const handleExport = (type: string) => {
  emit('export', type)
}


const handleUploadVideo = (file: File) => {
  // 验证文件类型
  const allowedTypes = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))

  if (!allowedTypes.includes(fileExtension)) {
    ElMessage.error('请选择支持的视频格式 (MP4, AVI, MOV, WMV, FLV, MKV)')
    return false
  }

  // 验证文件大小 (500MB)
  if (file.size > 500 * 1024 * 1024) {
    ElMessage.error('视频文件大小不能超过500MB')
    return false
  }

  emit('upload-video', file)
  return false // 阻止自动上传
}

const handleSpeakerCommand = (command: string) => {
  switch (command) {
    case 'auto-assign':
      emit('auto-assign-speaker')
      break
    case 'batch-speaker':
      emit('batch-speaker')
      break
  }
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