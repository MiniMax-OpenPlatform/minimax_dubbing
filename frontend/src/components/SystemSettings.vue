<template>
  <div class="system-settings">
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="系统信息" name="system">
        <div class="settings-grid">
          <el-card class="settings-card">
            <template #header>
              <span>认证信息</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="Group ID">
                {{ getStorageItem('group_id') || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="API Key">
                {{ getStorageItem('api_key') ? '已设置' : '未设置' }}
              </el-descriptions-item>
            </el-descriptions>
            <el-button @click="logout" type="warning" style="margin-top: 15px; width: 100%;">
              重新设置认证信息
            </el-button>
          </el-card>

          <el-card class="settings-card">
            <template #header>
              <span>应用信息</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="应用名称">MiniMax 翻译工具</el-descriptions-item>
              <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
              <el-descriptions-item label="后端地址">http://10.11.17.19:5172</el-descriptions-item>
              <el-descriptions-item label="前端地址">http://10.11.17.19:5173</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="settings-card">
            <template #header>
              <span>系统状态</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="日志条数">
                {{ logCount }} / 100
              </el-descriptions-item>
              <el-descriptions-item label="当前页面">
                projects
              </el-descriptions-item>
              <el-descriptions-item label="认证状态">
                <el-tag type="success">已认证</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="settings-card">
            <template #header>
              <span>浏览器信息</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="浏览器">
                {{ systemInfo.browser }}
              </el-descriptions-item>
              <el-descriptions-item label="屏幕分辨率">
                {{ systemInfo.screenResolution }}
              </el-descriptions-item>
              <el-descriptions-item label="视口大小">
                {{ systemInfo.viewportSize }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="参数配置" name="parameters">
        <div class="parameters-container">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-card class="parameter-card">
                <template #header>
                  <div class="card-header">
                    <span>翻译参数</span>
                    <el-button type="primary" size="small" @click="saveTranslationSettings">保存</el-button>
                  </div>
                </template>
                <el-form :model="translationSettings" label-width="120px" size="small">
                  <el-form-item label="目标语言">
                    <el-select v-model="translationSettings.target_language" style="width: 100%">
                      <el-option label="英语" value="en" />
                      <el-option label="日语" value="ja" />
                      <el-option label="韩语" value="ko" />
                      <el-option label="法语" value="fr" />
                      <el-option label="德语" value="de" />
                      <el-option label="西班牙语" value="es" />
                      <el-option label="俄语" value="ru" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="翻译风格">
                    <el-select v-model="translationSettings.style" style="width: 100%">
                      <el-option label="准确" value="accurate" />
                      <el-option label="自然" value="natural" />
                      <el-option label="正式" value="formal" />
                      <el-option label="口语化" value="colloquial" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="上下文长度">
                    <el-input-number
                      v-model="translationSettings.context_length"
                      :min="0"
                      :max="10"
                      style="width: 100%"
                    />
                  </el-form-item>
                  <el-form-item label="自定义词汇">
                    <el-input
                      v-model="translationSettings.custom_vocabulary"
                      type="textarea"
                      :rows="3"
                      placeholder="每行一个词汇对，格式：原文|译文"
                    />
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <el-col :span="8">
              <el-card class="parameter-card">
                <template #header>
                  <div class="card-header">
                    <span>TTS参数</span>
                    <el-button type="primary" size="small" @click="saveTTSSettings">保存</el-button>
                  </div>
                </template>
                <el-form :model="ttsSettings" label-width="120px" size="small">
                  <el-form-item label="默认音色">
                    <el-select v-model="ttsSettings.default_voice" style="width: 100%">
                      <el-option label="女声1" value="female_1" />
                      <el-option label="女声2" value="female_2" />
                      <el-option label="男声1" value="male_1" />
                      <el-option label="男声2" value="male_2" />
                      <el-option label="童声" value="child" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="语速">
                    <el-slider
                      v-model="ttsSettings.speed"
                      :min="0.5"
                      :max="2.0"
                      :step="0.1"
                      show-input
                      :show-input-controls="false"
                    />
                  </el-form-item>
                  <el-form-item label="音量">
                    <el-slider
                      v-model="ttsSettings.volume"
                      :min="0"
                      :max="100"
                      show-input
                      :show-input-controls="false"
                    />
                  </el-form-item>
                  <el-form-item label="情感风格">
                    <el-select v-model="ttsSettings.emotion" style="width: 100%">
                      <el-option label="中性" value="neutral" />
                      <el-option label="开心" value="happy" />
                      <el-option label="悲伤" value="sad" />
                      <el-option label="愤怒" value="angry" />
                      <el-option label="惊讶" value="surprised" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="音频格式">
                    <el-select v-model="ttsSettings.format" style="width: 100%">
                      <el-option label="MP3" value="mp3" />
                      <el-option label="WAV" value="wav" />
                      <el-option label="AAC" value="aac" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="比特率">
                    <el-select v-model="ttsSettings.bitrate" style="width: 100%">
                      <el-option label="128kbps" value="128k" />
                      <el-option label="192kbps" value="192k" />
                      <el-option label="256kbps" value="256k" />
                      <el-option label="320kbps" value="320k" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <el-col :span="8">
              <el-card class="parameter-card">
                <template #header>
                  <div class="card-header">
                    <span>时间戳对齐</span>
                    <el-button type="primary" size="small" @click="saveAlignmentSettings">保存</el-button>
                  </div>
                </template>
                <el-form :model="alignmentSettings" label-width="120px" size="small">
                  <el-form-item label="对齐算法">
                    <el-select v-model="alignmentSettings.algorithm" style="width: 100%">
                      <el-option label="5步优化算法" value="five_step" />
                      <el-option label="线性对齐" value="linear" />
                      <el-option label="动态规划" value="dynamic" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="时长容差">
                    <el-input-number
                      v-model="alignmentSettings.duration_tolerance"
                      :min="0.1"
                      :max="2.0"
                      :step="0.1"
                      style="width: 100%"
                    />
                    <div class="form-help">允许的时长偏差范围(秒)</div>
                  </el-form-item>
                  <el-form-item label="最大调整幅度">
                    <el-input-number
                      v-model="alignmentSettings.max_speed_ratio"
                      :min="0.5"
                      :max="3.0"
                      :step="0.1"
                      style="width: 100%"
                    />
                    <div class="form-help">语速调整的最大倍数</div>
                  </el-form-item>
                  <el-form-item label="静音检测">
                    <el-switch
                      v-model="alignmentSettings.silence_detection"
                      active-text="开启"
                      inactive-text="关闭"
                    />
                  </el-form-item>
                  <el-form-item label="静音阈值">
                    <el-input-number
                      v-model="alignmentSettings.silence_threshold"
                      :min="-60"
                      :max="-10"
                      style="width: 100%"
                      :disabled="!alignmentSettings.silence_detection"
                    />
                    <div class="form-help">静音检测的dB阈值</div>
                  </el-form-item>
                  <el-form-item label="优化模式">
                    <el-radio-group v-model="alignmentSettings.optimization_mode">
                      <el-radio label="speed">速度优先</el-radio>
                      <el-radio label="quality">质量优先</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { logger } from '../utils/logger'

const emit = defineEmits<{
  logout: []
}>()

const activeTab = ref('system')

const getStorageItem = (key: string) => {
  return localStorage.getItem(key)
}

const systemInfo = {
  browser: navigator.userAgent.split(' ').slice(-2).join(' '),
  screenResolution: `${screen.width} × ${screen.height}`,
  viewportSize: `${window.innerWidth} × ${window.innerHeight}`
}

const logCount = computed(() => logger.logs.value.length)

const translationSettings = ref({
  target_language: 'en',
  style: 'natural',
  context_length: 3,
  custom_vocabulary: ''
})

const ttsSettings = ref({
  default_voice: 'female_1',
  speed: 1.0,
  volume: 80,
  emotion: 'neutral',
  format: 'mp3',
  bitrate: '128k'
})

const alignmentSettings = ref({
  algorithm: 'five_step',
  duration_tolerance: 0.5,
  max_speed_ratio: 2.0,
  silence_detection: true,
  silence_threshold: -30,
  optimization_mode: 'quality'
})

const loadSettings = () => {
  const savedTranslation = localStorage.getItem('translation_settings')
  if (savedTranslation) {
    translationSettings.value = { ...translationSettings.value, ...JSON.parse(savedTranslation) }
  }

  const savedTTS = localStorage.getItem('tts_settings')
  if (savedTTS) {
    ttsSettings.value = { ...ttsSettings.value, ...JSON.parse(savedTTS) }
  }

  const savedAlignment = localStorage.getItem('alignment_settings')
  if (savedAlignment) {
    alignmentSettings.value = { ...alignmentSettings.value, ...JSON.parse(savedAlignment) }
  }
}

const saveTranslationSettings = () => {
  try {
    localStorage.setItem('translation_settings', JSON.stringify(translationSettings.value))
    ElMessage.success('翻译参数保存成功')
    logger.addLog('success', '翻译参数配置已保存', 'Settings')
  } catch (error) {
    ElMessage.error('保存失败')
    logger.addLog('error', '翻译参数保存失败', 'Settings')
  }
}

const saveTTSSettings = () => {
  try {
    localStorage.setItem('tts_settings', JSON.stringify(ttsSettings.value))
    ElMessage.success('TTS参数保存成功')
    logger.addLog('success', 'TTS参数配置已保存', 'Settings')
  } catch (error) {
    ElMessage.error('保存失败')
    logger.addLog('error', 'TTS参数保存失败', 'Settings')
  }
}

const saveAlignmentSettings = () => {
  try {
    localStorage.setItem('alignment_settings', JSON.stringify(alignmentSettings.value))
    ElMessage.success('时间戳对齐参数保存成功')
    logger.addLog('success', '时间戳对齐参数配置已保存', 'Settings')
  } catch (error) {
    ElMessage.error('保存失败')
    logger.addLog('error', '时间戳对齐参数保存失败', 'Settings')
  }
}

const logout = () => {
  emit('logout')
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.system-settings {
  width: 100%;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  width: 100%;
  max-width: none;
}

.settings-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  transition: box-shadow 0.3s ease;
}

.settings-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.parameters-container {
  width: 100%;
  max-width: none;
}

.parameter-card {
  height: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  transition: box-shadow 0.3s ease;
}

.parameter-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.4;
}

/* 确保表单项之间的间距 */
:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

/* 滑块样式优化 */
:deep(.el-slider) {
  margin: 10px 0;
}

/* 单选组样式 */
:deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Tab内容样式 */
:deep(.el-tabs__content) {
  padding: 20px 0;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .settings-grid {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 15px;
  }

  .parameters-container .el-col {
    margin-bottom: 20px;
  }
}

@media (max-width: 1200px) {
  .settings-grid {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 15px;
  }

  .parameters-container {
    padding: 0 10px;
  }
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .parameters-container .el-row {
    margin: 0;
  }

  .parameters-container .el-col {
    padding: 0 10px;
    margin-bottom: 20px;
  }
}
</style>