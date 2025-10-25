<template>
  <div class="editor-toolbar">
    <!-- 工作流按钮组 - 按顺序排列 -->
    <div class="workflow-buttons">
      <el-button-group>
        <!-- 1. 上传视频 -->
        <el-upload
          ref="videoUploadRef"
          :show-file-list="false"
          :before-upload="handleUploadVideo"
          accept=".mp4,.avi,.mov,.wmv,.flv,.mkv"
        >
          <el-button :icon="VideoCamera" type="primary">
            上传视频
          </el-button>
        </el-upload>

        <!-- 2. 人声分离 -->
        <el-button
          :icon="Headset"
          @click="$emit('separate-vocals')"
          :loading="batchLoading"
        >
          人声分离
        </el-button>

        <!-- 3. SRT（上传SRT/ASR识别） -->
        <el-dropdown @command="handleSRTCommand">
          <el-button :icon="Document">
            SRT
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="upload-srt">
                <el-icon><Upload /></el-icon>
                上传SRT文件
              </el-dropdown-item>
              <el-dropdown-item command="asr" divided>
                <el-icon><Microphone /></el-icon>
                ASR自动识别
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 隐藏的上传组件 -->
        <el-upload
          ref="srtUploadRef"
          :show-file-list="false"
          :before-upload="handleUploadSRT"
          accept=".srt"
          style="display: none;"
        >
        </el-upload>

        <!-- 4. 分配说话人 -->
        <el-dropdown @command="handleSpeakerCommand">
          <el-button :icon="User">
            分配说话人
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

        <!-- 5. 批量翻译 -->
        <el-button
          type="primary"
          @click="$emit('batch-translate')"
          :loading="batchLoading"
        >
          批量翻译
        </el-button>

        <!-- 6. 批量TTS -->
        <el-button
          type="success"
          @click="$emit('batch-tts')"
          :loading="batchLoading"
        >
          批量TTS
        </el-button>

        <!-- 7. 拼接音频 -->
        <el-button
          type="warning"
          @click="$emit('concatenate-audio')"
          :loading="batchLoading"
        >
          拼接音频
        </el-button>

        <!-- 8. 合成视频 -->
        <el-button
          :icon="Film"
          type="success"
          @click="$emit('synthesize-video')"
          :loading="batchLoading"
        >
          合成视频
        </el-button>
      </el-button-group>
    </div>

    <!-- 右侧工具按钮 -->
    <div class="toolbar-right">
      <el-dropdown trigger="click">
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
import {
  Search,
  ArrowDown,
  Upload,
  User,
  VideoCamera,
  Headset,
  Microphone,
  Film,
  Document
} from '@element-plus/icons-vue'

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
  'synthesize-video': []
  'export': [type: string]
  'upload-video': [file: File]
  'upload-srt': [file: File]
  'separate-vocals': []
  'auto-assign-speaker': []
  'batch-speaker': []
  'asr-recognize': []
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

const handleSRTCommand = (command: string) => {
  switch (command) {
    case 'upload-srt':
      // 触发隐藏的上传组件
      const uploadInput = document.querySelector('input[type="file"][accept=".srt"]') as HTMLInputElement
      if (uploadInput) {
        uploadInput.click()
      }
      break
    case 'asr':
      emit('asr-recognize')
      break
  }
}

const handlePlaceholderClick = (featureName: string) => {
  ElMessage.info(`${featureName}功能即将上线，敬请期待！`)
}

const handleUploadSRT = (file: File) => {
  // 验证文件类型
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))

  if (fileExtension !== '.srt') {
    ElMessage.error('请选择SRT格式的字幕文件')
    return false
  }

  // 验证文件大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('SRT文件大小不能超过10MB')
    return false
  }

  emit('upload-srt', file)
  return false // 阻止自动上传
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

.workflow-buttons {
  display: flex;
  align-items: center;
  flex: 1;
  overflow-x: auto;
}

.workflow-buttons .el-button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
}

.workflow-buttons .el-upload {
  display: inline-block;
  vertical-align: middle;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 1600px) {
  .workflow-buttons .el-button-group {
    flex-wrap: wrap;
  }
}

@media (max-width: 1200px) {
  .editor-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .workflow-buttons,
  .toolbar-right {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .workflow-buttons {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .workflow-buttons .el-button-group {
    flex-wrap: nowrap;
  }
}
</style>