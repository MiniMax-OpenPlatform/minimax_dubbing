<template>
  <div class="voice-cloning">
    <div class="header">
      <h2>音色克隆</h2>
      <div class="header-actions">
        <el-button
          type="primary"
          @click="resetForm"
          icon="Refresh"
        >
          重置表单
        </el-button>
      </div>
    </div>

    <el-card class="cloning-form">
      <template #header>
        <div class="card-header">
          <span>克隆配置</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="150px"
        label-position="left"
      >
        <!-- 上传克隆音频 -->
        <el-form-item label="上传克隆音频" prop="cloneAudio" required>
          <el-upload
            ref="cloneUploadRef"
            class="upload-demo"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".mp3,.wav,.m4a"
            :on-change="handleCloneAudioChange"
            :on-remove="handleCloneAudioRemove"
          >
            <el-button type="primary" icon="Upload">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 MP3、WAV、M4A 格式<br/>
                时长：10秒-5分钟，文件大小不超过 20MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- voice_id命名 -->
        <el-form-item label="Voice ID" prop="voiceId" required>
          <el-input
            v-model="form.voiceId"
            placeholder="请输入音色ID，如：my_clone_voice_001"
            clearable
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 上传prompt音频（可选） -->
        <el-form-item label="Prompt音频（可选）">
          <div class="upload-with-preview">
            <el-upload
              ref="promptUploadRef"
              class="upload-demo"
              :auto-upload="false"
              :show-file-list="true"
              :limit="1"
              accept=".mp3,.wav,.m4a"
              :on-change="handlePromptAudioChange"
              :on-remove="handlePromptAudioRemove"
            >
              <el-button type="default" icon="Upload">选择文件</el-button>
              <template #tip>
                <div class="el-upload__tip">
                  可选项，用于改善克隆效果<br/>
                  支持 MP3、WAV、M4A 格式，时长小于8秒，文件大小不超过 20MB
                </div>
              </template>
            </el-upload>

            <!-- Prompt音频播放按钮 -->
            <div v-if="form.promptAudio" class="audio-preview-control">
              <el-button
                :type="currentPlayingId === 'prompt-preview' && currentAudio && !currentAudio.paused ? 'info' : 'primary'"
                size="small"
                @click="playPromptPreview"
                :icon="currentPlayingId === 'prompt-preview' && currentAudio && !currentAudio.paused ? 'VideoPause' : 'VideoPlay'"
              >
                {{ currentPlayingId === 'prompt-preview' && currentAudio && !currentAudio.paused ? '暂停预览' : '播放预览' }}
              </el-button>
            </div>
          </div>
        </el-form-item>

        <!-- prompt文本（当使用prompt音频时必选） -->
        <el-form-item
          label="Prompt文本"
          prop="promptText"
          :required="!!form.promptAudio"
        >
          <el-input
            v-model="form.promptText"
            type="textarea"
            :rows="3"
            placeholder="当使用Prompt音频时必须填写，请输入与Prompt音频对应的文本内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <!-- 试听文本 -->
        <el-form-item label="试听文本" prop="testText" required>
          <el-input
            v-model="form.testText"
            type="textarea"
            :rows="3"
            placeholder="请输入试听文本，用于生成克隆音频样本"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <!-- 试听模型 -->
        <el-form-item label="试听模型" prop="model">
          <el-input
            v-model="form.model"
            placeholder="speech-2.5-hd-preview"
            clearable
          />
          <div class="form-tip">默认使用 speech-2.5-hd-preview，可手动修改</div>
        </el-form-item>

        <!-- 降噪设置 -->
        <el-form-item label="降噪设置">
          <el-switch
            v-model="form.needNoiseReduction"
            active-text="开启降噪"
            inactive-text="关闭降噪"
          />
        </el-form-item>

        <!-- 音量归一化设置 -->
        <el-form-item label="音量归一化">
          <el-switch
            v-model="form.needVolumeNormalization"
            active-text="开启归一化"
            inactive-text="关闭归一化"
          />
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            @click="startCloning"
            :loading="cloning"
            size="large"
          >
            {{ cloning ? '克隆中...' : '开始克隆' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 克隆结果展示 -->
    <el-card v-if="cloneResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>克隆结果</span>
          <el-tag
            :type="cloneResult.success ? 'success' : 'danger'"
            size="large"
          >
            {{ cloneResult.success ? '克隆成功' : '克隆失败' }}
          </el-tag>
        </div>
      </template>

      <div class="result-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Voice ID">
            {{ form.voiceId }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="cloneResult.success ? 'success' : 'danger'">
              {{ cloneResult.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Trace ID">
            {{ cloneResult.trace_id || '未获取到' }}
          </el-descriptions-item>
          <el-descriptions-item label="消息">
            {{ cloneResult.message }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 试听音频播放 -->
        <div v-if="cloneResult.success && cloneResult.demo_audio_url" class="audio-preview">
          <h4>试听预览</h4>
          <div class="audio-player">
            <audio
              ref="audioRef"
              :src="cloneResult.demo_audio_url"
              controls
              preload="metadata"
            >
              您的浏览器不支持音频播放
            </audio>
          </div>
          <div class="audio-actions">
            <el-button
              type="primary"
              @click="playAudio"
              icon="VideoPlay"
              size="small"
            >
              播放
            </el-button>
            <el-button
              type="default"
              @click="downloadAudio"
              icon="Download"
              size="small"
            >
              下载
            </el-button>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="!cloneResult.success && cloneResult.error_message" class="error-info">
          <h4>错误详情</h4>
          <el-alert
            :title="cloneResult.error_message"
            type="error"
            :closable="false"
            show-icon
          />
        </div>

        <!-- API响应详情（调试用） -->
        <div v-if="cloneResult.api_response" class="api-response">
          <el-collapse>
            <el-collapse-item title="API响应详情" name="api-response">
              <pre>{{ JSON.stringify(cloneResult.api_response, null, 2) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </el-card>

    <!-- 历史记录 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>克隆历史</span>
          <el-button @click="loadHistory" icon="Refresh" size="small">刷新</el-button>
        </div>
      </template>

      <el-table
        :data="historyList"
        v-loading="historyLoading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="voice_id" label="Voice ID" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag
              :type="scope.row.status === 'success' ? 'success' : scope.row.status === 'failed' ? 'danger' : 'warning'"
              size="small"
            >
              {{ scope.row.status === 'success' ? '成功' : scope.row.status === 'failed' ? '失败' : '处理中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trace_id" label="Trace ID" width="150" show-overflow-tooltip>
          <template #default="scope">
            <el-text size="small" class="trace-id">{{ scope.row.trace_id || '无' }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="120">
          <template #default="scope">
            <el-text size="small">{{ formatDate(scope.row.created_at) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="音频播放" width="280">
          <template #default="scope">
            <div class="audio-actions">
              <!-- 试听音频 -->
              <el-button
                v-if="scope.row.demo_audio_file"
                :type="currentPlayingId === `${scope.row.id}-demo` && currentAudio && !currentAudio.paused ? 'info' : 'primary'"
                size="small"
                @click="playLocalAudio(scope.row.demo_audio_file, scope.row.id, 'demo')"
                :icon="currentPlayingId === `${scope.row.id}-demo` && currentAudio && !currentAudio.paused ? 'SwitchButton' : 'VideoPlay'"
              >
                {{ currentPlayingId === `${scope.row.id}-demo` && currentAudio && !currentAudio.paused ? '暂停' : '试听' }}
              </el-button>
              <el-button
                v-else-if="scope.row.demo_audio_url"
                type="primary"
                size="small"
                @click="playHistoryAudio(scope.row.demo_audio_url)"
                icon="VideoPlay"
              >
                试听
              </el-button>

              <!-- 克隆音频 -->
              <el-button
                v-if="scope.row.clone_audio_file"
                :type="currentPlayingId === `${scope.row.id}-clone` && currentAudio && !currentAudio.paused ? 'info' : 'success'"
                size="small"
                @click="playLocalAudio(scope.row.clone_audio_file, scope.row.id, 'clone')"
                :icon="currentPlayingId === `${scope.row.id}-clone` && currentAudio && !currentAudio.paused ? 'VideoPause' : 'Microphone'"
              >
                {{ currentPlayingId === `${scope.row.id}-clone` && currentAudio && !currentAudio.paused ? '暂停' : '克隆音频' }}
              </el-button>
              <el-button
                v-else-if="scope.row.clone_audio_file_id"
                type="success"
                size="small"
                @click="showFileInfo(scope.row.clone_audio_file_id, '克隆音频')"
                icon="Microphone"
              >
                克隆音频
              </el-button>

              <!-- Prompt音频 -->
              <el-button
                v-if="scope.row.prompt_audio_file"
                :type="currentPlayingId === `${scope.row.id}-prompt` && currentAudio && !currentAudio.paused ? 'info' : 'warning'"
                size="small"
                @click="playLocalAudio(scope.row.prompt_audio_file, scope.row.id, 'prompt')"
                :icon="currentPlayingId === `${scope.row.id}-prompt` && currentAudio && !currentAudio.paused ? 'VideoPause' : 'Headphone'"
              >
                {{ currentPlayingId === `${scope.row.id}-prompt` && currentAudio && !currentAudio.paused ? '暂停' : 'Prompt' }}
              </el-button>
              <el-button
                v-else-if="scope.row.prompt_audio_file_id"
                type="warning"
                size="small"
                @click="showFileInfo(scope.row.prompt_audio_file_id, 'Prompt音频')"
                icon="Headphone"
              >
                Prompt
              </el-button>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80">
          <template #default="scope">
            <el-button
              type="danger"
              size="small"
              @click="deleteHistory(scope.row.id)"
              icon="Delete"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="historyList.length > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="historyTotal"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import api from '@/utils/api'

interface CloneForm {
  voiceId: string
  cloneAudio: UploadFile | null
  promptAudio: UploadFile | null
  promptText: string
  testText: string
  model: string
  needNoiseReduction: boolean
  needVolumeNormalization: boolean
}

interface CloneResult {
  success: boolean
  message: string
  demo_audio_url?: string
  error_message?: string
  api_response?: any
  trace_id?: string
}

interface HistoryRecord {
  id: number
  voice_id: string
  status: 'pending' | 'success' | 'failed'
  demo_audio_url?: string
  clone_audio_file_id: string
  prompt_audio_file_id?: string
  trace_id?: string
  created_at: string
  clone_audio_file?: string
  prompt_audio_file?: string
  demo_audio_file?: string
}

// 响应式数据
const formRef = ref<FormInstance>()
const audioRef = ref<HTMLAudioElement>()
const cloneUploadRef = ref()
const promptUploadRef = ref()

const form = reactive<CloneForm>({
  voiceId: '',
  cloneAudio: null,
  promptAudio: null,
  promptText: '',
  testText: '微风拂过柔软的草地，清新的芳香伴随着鸟儿的歌唱。',
  model: 'speech-2.5-hd-preview',
  needNoiseReduction: false,
  needVolumeNormalization: false
})

// 存储本地文件路径
const localFilePaths = reactive({
  cloneAudioPath: '',
  promptAudioPath: ''
})

const cloning = ref(false)
const cloneResult = ref<CloneResult | null>(null)
const historyList = ref<HistoryRecord[]>([])
const historyLoading = ref(false)
const historyTotal = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 音频播放管理
const currentAudio = ref<HTMLAudioElement | null>(null)
const currentPlayingId = ref<string>('')

// 表单验证规则
const rules: FormRules = {
  voiceId: [
    { required: true, message: '请输入Voice ID', trigger: 'blur' },
    { min: 1, max: 200, message: 'Voice ID长度在1到200个字符', trigger: 'blur' }
  ],
  testText: [
    { required: true, message: '请输入试听文本', trigger: 'blur' },
    { min: 1, max: 500, message: '试听文本长度在1到500个字符', trigger: 'blur' }
  ],
  promptText: [
    {
      validator: (rule: any, value: string, callback: any) => {
        if (form.promptAudio && !value.trim()) {
          callback(new Error('使用Prompt音频时必须填写Prompt文本'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 文件上传处理
const handleCloneAudioChange = (file: UploadFile) => {
  form.cloneAudio = file
}

const handleCloneAudioRemove = () => {
  form.cloneAudio = null
}

const handlePromptAudioChange = (file: UploadFile) => {
  form.promptAudio = file
}

const handlePromptAudioRemove = () => {
  form.promptAudio = null
  form.promptText = ''
}

// 上传文件到服务器
const uploadFile = async (file: UploadFile, purpose: string): Promise<string> => {
  const formData = new FormData()
  formData.append('file', file.raw!)
  formData.append('purpose', purpose)

  try {
    const response = await api.post('/voice-cloning/upload_file/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data.success) {
      // 存储本地文件路径
      const localPath = response.data.data.local_file_path
      if (purpose === 'voice_clone') {
        localFilePaths.cloneAudioPath = localPath
      } else if (purpose === 'prompt_audio') {
        localFilePaths.promptAudioPath = localPath
      }

      return response.data.data.file_id
    } else {
      throw new Error(response.data.message || '文件上传失败')
    }
  } catch (error: any) {
    console.error('文件上传失败:', error)
    throw new Error(error.response?.data?.message || '文件上传失败')
  }
}

// 开始克隆
const startCloning = async () => {
  if (!formRef.value) return

  try {
    // 表单验证
    const isValid = await formRef.value.validate().catch(() => false)
    if (!isValid) {
      return
    }

    if (!form.cloneAudio) {
      ElMessage.error('请先上传克隆音频文件')
      return
    }

    cloning.value = true
    cloneResult.value = null

    // 上传克隆音频文件
    ElMessage.info('正在上传克隆音频文件...')
    const cloneAudioFileId = await uploadFile(form.cloneAudio, 'voice_clone')

    // 上传prompt音频文件（如果有）
    let promptAudioFileId = ''
    if (form.promptAudio) {
      ElMessage.info('正在上传Prompt音频文件...')
      promptAudioFileId = await uploadFile(form.promptAudio, 'prompt_audio')
    }

    // 执行克隆
    ElMessage.info('正在执行音色克隆，请稍候...')
    const cloneData = {
      voice_id: form.voiceId,
      clone_audio_file_id: cloneAudioFileId,
      prompt_audio_file_id: promptAudioFileId,
      prompt_text: form.promptText,
      test_text: form.testText,
      model: form.model,
      need_noise_reduction: form.needNoiseReduction,
      need_volume_normalization: form.needVolumeNormalization,
      clone_local_path: localFilePaths.cloneAudioPath,
      prompt_local_path: localFilePaths.promptAudioPath
    }

    const response = await api.post('/voice-cloning/clone_voice/', cloneData)

    cloneResult.value = {
      success: response.data.success,
      message: response.data.message,
      demo_audio_url: response.data.data?.demo_audio_url,
      error_message: response.data.data?.error_message,
      api_response: response.data.data?.api_response,
      trace_id: response.data.data?.trace_id
    }

    if (response.data.success) {
      ElMessage.success('音色克隆成功！')
      loadHistory() // 刷新历史记录
    } else {
      ElMessage.error(`音色克隆失败：${response.data.message}`)
    }

  } catch (error: any) {
    console.error('克隆失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '克隆失败'
    ElMessage.error(errorMsg)

    cloneResult.value = {
      success: false,
      message: errorMsg,
      error_message: errorMsg,
      trace_id: error.response?.data?.data?.trace_id
    }
  } finally {
    cloning.value = false
  }
}

// 播放音频
const playAudio = () => {
  if (audioRef.value) {
    audioRef.value.play()
  }
}

// 下载音频
const downloadAudio = () => {
  if (cloneResult.value?.demo_audio_url) {
    const link = document.createElement('a')
    link.href = cloneResult.value.demo_audio_url
    link.download = `${form.voiceId}_demo.mp3`
    link.click()
  }
}

// 播放历史音频
const playHistoryAudio = (url: string) => {
  const audio = new Audio(url)
  audio.play()
}

// 停止当前播放的音频
const stopCurrentAudio = () => {
  if (currentAudio.value) {
    currentAudio.value.pause()
    currentAudio.value.currentTime = 0
    currentAudio.value = null
    currentPlayingId.value = ''
  }
}

// 播放音频的通用函数
const playAudioWithControl = async (audioUrl: string, audioId: string) => {
  try {
    // 如果点击的是当前正在播放的音频，则暂停
    if (currentPlayingId.value === audioId && currentAudio.value) {
      if (currentAudio.value.paused) {
        await currentAudio.value.play()
        return 'playing'
      } else {
        currentAudio.value.pause()
        return 'paused'
      }
    }

    // 停止当前播放的音频
    stopCurrentAudio()

    console.log('播放音频URL:', audioUrl)

    const audio = new Audio(audioUrl)

    // 添加错误监听器
    audio.addEventListener('error', (e) => {
      console.error('音频加载失败:', e)
      ElMessage.error(`音频加载失败`)
      currentAudio.value = null
      currentPlayingId.value = ''
    })

    // 添加播放结束监听器
    audio.addEventListener('ended', () => {
      console.log('音频播放结束')
      currentAudio.value = null
      currentPlayingId.value = ''
    })

    // 添加加载成功监听器
    audio.addEventListener('canplay', () => {
      console.log('音频加载成功，开始播放')
    })

    currentAudio.value = audio
    currentPlayingId.value = audioId

    await audio.play()
    return 'playing'
  } catch (error) {
    console.error('播放音频失败:', error)
    ElMessage.error('播放音频失败')
    currentAudio.value = null
    currentPlayingId.value = ''
    return 'error'
  }
}

// 播放本地音频文件
const playLocalAudio = async (filePath: string, recordId?: number, audioType?: string) => {
  let audioUrl: string

  // 如果是完整URL，直接播放
  if (filePath.startsWith('http')) {
    audioUrl = filePath
  } else if (filePath.startsWith('/dubbing/media/')) {
    // 如果已经是 /dubbing/media/ 格式，直接使用
    audioUrl = filePath
  } else {
    // 如果是相对路径，构建完整URL
    const protocol = window.location.protocol
    const hostname = window.location.hostname

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // 本地开发环境
      const cleanPath = filePath.startsWith('/') ? filePath.slice(1) : filePath
      audioUrl = `${protocol}//${hostname}:5172/${cleanPath}`
    } else {
      // 生产环境
      const cleanPath = filePath.startsWith('/media/') ? filePath.replace('/media/', '') : filePath
      audioUrl = `/dubbing/media/${cleanPath}`
    }
  }

  // 生成唯一的音频ID
  const audioId = recordId && audioType ? `${recordId}-${audioType}` : audioUrl

  await playAudioWithControl(audioUrl, audioId)
}

// 播放Prompt预览音频
const playPromptPreview = async () => {
  if (!form.promptAudio || !form.promptAudio.raw) {
    ElMessage.warning('请先选择Prompt音频文件')
    return
  }

  try {
    // 创建本地文件URL用于预览
    const audioUrl = URL.createObjectURL(form.promptAudio.raw)
    await playAudioWithControl(audioUrl, 'prompt-preview')
  } catch (error) {
    console.error('播放Prompt预览失败:', error)
    ElMessage.error('播放Prompt预览失败')
  }
}

// 显示文件信息
const showFileInfo = (fileId: string, fileType: string) => {
  ElMessageBox.alert(
    `文件ID: ${fileId}\n\n说明: 这是用户上传的${fileType}文件，文件可能已过期，无法直接播放。您可以复制文件ID用于其他用途。`,
    `${fileType}信息`,
    {
      confirmButtonText: '复制文件ID',
      cancelButtonText: '关闭',
      showCancelButton: true,
      type: 'info'
    }
  ).then(() => {
    // 复制文件ID到剪贴板
    navigator.clipboard.writeText(fileId).then(() => {
      ElMessage.success('文件ID已复制到剪贴板')
    }).catch(() => {
      ElMessage.warning('复制失败，请手动复制文件ID')
    })
  }).catch(() => {
    // 用户点击了关闭按钮，什么都不做
  })
}

// 重置表单
const resetForm = () => {
  // 停止当前播放的音频
  stopCurrentAudio()

  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.cloneAudio = null
  form.promptAudio = null
  form.promptText = ''
  form.testText = '微风拂过柔软的草地，清新的芳香伴随着鸟儿的歌唱。'
  form.model = 'speech-2.5-hd-preview'
  form.needNoiseReduction = false
  form.needVolumeNormalization = false
  cloneResult.value = null

  // 清空本地文件路径
  localFilePaths.cloneAudioPath = ''
  localFilePaths.promptAudioPath = ''

  // 清空上传组件
  if (cloneUploadRef.value) {
    cloneUploadRef.value.clearFiles()
  }
  if (promptUploadRef.value) {
    promptUploadRef.value.clearFiles()
  }
}

// 加载历史记录
const loadHistory = async () => {
  try {
    historyLoading.value = true
    const response = await api.get('/voice-cloning/', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })

    if (response.data.results) {
      historyList.value = response.data.results
      historyTotal.value = response.data.count
    } else {
      historyList.value = response.data || []
      historyTotal.value = historyList.value.length
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
    ElMessage.error('加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

// 删除历史记录
const deleteHistory = async (id: number) => {
  try {
    await ElMessageBox.confirm('确认删除此克隆记录？', '确认删除', {
      type: 'warning'
    })

    await api.delete(`/voice-cloning/${id}/`)
    ElMessage.success('删除成功')
    loadHistory()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
  loadHistory()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadHistory()
}

// 格式化日期
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN')
  } catch {
    return dateString
  }
}

// 生命周期
onMounted(() => {
  loadHistory()
})

// 组件卸载时清理音频
onUnmounted(() => {
  stopCurrentAudio()
})
</script>

<style scoped>
.voice-cloning {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #1f2328;
}

.cloning-form,
.result-card,
.history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.result-content {
  padding: 20px 0;
}

.audio-preview {
  margin-top: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.audio-preview h4 {
  margin: 0 0 15px 0;
  color: #1f2328;
}

.audio-player {
  margin-bottom: 15px;
}

.audio-player audio {
  width: 100%;
  max-width: 400px;
}

.audio-actions {
  display: flex;
  gap: 10px;
}

.error-info {
  margin-top: 20px;
}

.error-info h4 {
  margin: 0 0 15px 0;
  color: #f56c6c;
}

.api-response {
  margin-top: 20px;
}

.api-response pre {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.el-card) {
  border-radius: 8px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-upload__tip) {
  font-size: 12px;
  color: #909399;
  margin-top: 7px;
}

:deep(.el-button) {
  border-radius: 6px;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
}

:deep(.el-textarea__inner) {
  border-radius: 6px;
}

.trace-id {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 11px;
  color: #666;
}

.audio-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.audio-actions .el-button {
  font-size: 12px;
  padding: 4px 8px;
}

/* 上传预览区域样式 */
.upload-with-preview {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.audio-preview-control {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.audio-preview-control::before {
  content: "🎵";
  font-size: 16px;
  margin-right: 4px;
}
</style>