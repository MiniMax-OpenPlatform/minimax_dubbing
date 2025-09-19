<template>
  <el-dialog
    title="项目设置"
    :model-value="visible"
    width="600px"
    @close="$emit('close')"
    @update:model-value="$emit('close')"
  >
    <el-form
      ref="settingsForm"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="项目名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入项目名称" />
      </el-form-item>

      <el-form-item label="项目描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入项目描述"
        />
      </el-form-item>

      <el-form-item label="源语言" prop="source_lang">
        <el-select v-model="formData.source_lang" placeholder="请选择源语言" filterable>
          <el-option label="中文" value="zh" />
          <el-option label="粤语" value="yue" />
          <el-option label="英语" value="en" />
          <el-option label="阿拉伯语" value="ar" />
          <el-option label="俄语" value="ru" />
          <el-option label="西班牙语" value="es" />
          <el-option label="法语" value="fr" />
          <el-option label="葡萄牙语" value="pt" />
          <el-option label="德语" value="de" />
          <el-option label="土耳其语" value="tr" />
          <el-option label="荷兰语" value="nl" />
          <el-option label="乌克兰语" value="uk" />
          <el-option label="越南语" value="vi" />
          <el-option label="印尼语" value="id" />
          <el-option label="日语" value="ja" />
          <el-option label="意大利语" value="it" />
          <el-option label="韩语" value="ko" />
          <el-option label="泰语" value="th" />
          <el-option label="波兰语" value="pl" />
          <el-option label="罗马尼亚语" value="ro" />
          <el-option label="希腊语" value="el" />
          <el-option label="捷克语" value="cs" />
          <el-option label="芬兰语" value="fi" />
          <el-option label="印地语" value="hi" />
          <el-option label="保加利亚语" value="bg" />
          <el-option label="丹麦语" value="da" />
          <el-option label="希伯来语" value="he" />
          <el-option label="马来语" value="ms" />
          <el-option label="波斯语" value="fa" />
          <el-option label="斯洛伐克语" value="sk" />
          <el-option label="瑞典语" value="sv" />
          <el-option label="克罗地亚语" value="hr" />
          <el-option label="菲律宾语" value="fil" />
          <el-option label="匈牙利语" value="hu" />
          <el-option label="挪威语" value="no" />
          <el-option label="斯洛文尼亚语" value="sl" />
          <el-option label="加泰罗尼亚语" value="ca" />
          <el-option label="尼诺斯克语" value="nn" />
          <el-option label="泰米尔语" value="ta" />
          <el-option label="阿非利卡语" value="af" />
        </el-select>
      </el-form-item>

      <el-form-item label="目标语言" prop="target_lang">
        <el-select v-model="formData.target_lang" placeholder="请选择目标语言" filterable>
          <el-option label="中文" value="zh" />
          <el-option label="粤语" value="yue" />
          <el-option label="英语" value="en" />
          <el-option label="阿拉伯语" value="ar" />
          <el-option label="俄语" value="ru" />
          <el-option label="西班牙语" value="es" />
          <el-option label="法语" value="fr" />
          <el-option label="葡萄牙语" value="pt" />
          <el-option label="德语" value="de" />
          <el-option label="土耳其语" value="tr" />
          <el-option label="荷兰语" value="nl" />
          <el-option label="乌克兰语" value="uk" />
          <el-option label="越南语" value="vi" />
          <el-option label="印尼语" value="id" />
          <el-option label="日语" value="ja" />
          <el-option label="意大利语" value="it" />
          <el-option label="韩语" value="ko" />
          <el-option label="泰语" value="th" />
          <el-option label="波兰语" value="pl" />
          <el-option label="罗马尼亚语" value="ro" />
          <el-option label="希腊语" value="el" />
          <el-option label="捷克语" value="cs" />
          <el-option label="芬兰语" value="fi" />
          <el-option label="印地语" value="hi" />
          <el-option label="保加利亚语" value="bg" />
          <el-option label="丹麦语" value="da" />
          <el-option label="希伯来语" value="he" />
          <el-option label="马来语" value="ms" />
          <el-option label="波斯语" value="fa" />
          <el-option label="斯洛伐克语" value="sk" />
          <el-option label="瑞典语" value="sv" />
          <el-option label="克罗地亚语" value="hr" />
          <el-option label="菲律宾语" value="fil" />
          <el-option label="匈牙利语" value="hu" />
          <el-option label="挪威语" value="no" />
          <el-option label="斯洛文尼亚语" value="sl" />
          <el-option label="加泰罗尼亚语" value="ca" />
          <el-option label="尼诺斯克语" value="nn" />
          <el-option label="泰米尔语" value="ta" />
          <el-option label="阿非利卡语" value="af" />
        </el-select>
      </el-form-item>

      <el-form-item label="角色音色配置">
        <div class="voice-config-section">
          <div v-for="(mapping, index) in formData.voice_mappings" :key="index" class="voice-mapping-row">
            <el-input
              v-model="mapping.speaker"
              placeholder="角色名称（如: 说话人1, 旁白）"
              style="width: 180px;"
            />
            <span class="arrow">→</span>
            <el-input
              v-model="mapping.voice_id"
              placeholder="音色ID（如: male-qn-qingse）"
              style="width: 200px;"
            />
            <el-button
              type="danger"
              size="small"
              @click="removeSpeakerMapping(index)"
              :disabled="formData.voice_mappings.length <= 1"
            >
              删除
            </el-button>
          </div>
          <el-button
            type="primary"
            size="small"
            @click="addSpeakerMapping"
            style="margin-top: 8px;"
          >
            添加角色音色映射
          </el-button>
        </div>
      </el-form-item>

      <el-form-item label="翻译专有词表">
        <el-input
          v-model="formData.custom_vocabulary"
          type="textarea"
          :rows="4"
          placeholder="请输入专有词汇，每行一个，格式：原词|译词&#10;例如：&#10;AI|人工智能&#10;API|应用程序接口&#10;Machine Learning|机器学习"
        />
        <div class="vocabulary-hint">
          <small>格式说明：每行一个词汇，使用"|"分隔原词和译词。这些词汇在翻译时会被优先使用。</small>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="$emit('close')">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存设置
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

interface SpeakerVoiceMapping {
  speaker: string
  voice_id: string
}

interface ProjectSettings {
  name: string
  description: string
  source_lang: string
  target_lang: string
  voice_mappings: SpeakerVoiceMapping[]
  custom_vocabulary: string
}

const props = defineProps<{
  visible: boolean
  project: any
  saving?: boolean
}>()

const emit = defineEmits<{
  close: []
  save: [settings: ProjectSettings]
}>()

const settingsForm = ref<FormInstance>()

// 表单数据
const formData = reactive<ProjectSettings>({
  name: '',
  description: '',
  source_lang: '',
  target_lang: '',
  voice_mappings: [
    { speaker: '说话人1', voice_id: '' },
    { speaker: '说话人2', voice_id: '' },
    { speaker: '旁白', voice_id: '' }
  ],
  custom_vocabulary: ''
})

// 表单验证规则
const rules: FormRules<ProjectSettings> = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度应在 1 到 100 个字符', trigger: 'blur' }
  ],
  source_lang: [
    { required: true, message: '请选择源语言', trigger: 'change' }
  ],
  target_lang: [
    { required: true, message: '请选择目标语言', trigger: 'change' }
  ]
}

// 监听项目数据变化，更新表单
watch(() => props.project, (newProject) => {
  if (newProject) {
    formData.name = newProject.name || ''
    formData.description = newProject.description || ''
    formData.source_lang = newProject.source_lang || ''
    formData.target_lang = newProject.target_lang || ''

    // 解析角色音色映射
    if (newProject.voice_mappings && Array.isArray(newProject.voice_mappings)) {
      formData.voice_mappings = newProject.voice_mappings
    } else if (newProject.voice_mappings && typeof newProject.voice_mappings === 'string') {
      try {
        formData.voice_mappings = JSON.parse(newProject.voice_mappings)
      } catch {
        formData.voice_mappings = [
          { speaker: '说话人1', voice_id: '' },
          { speaker: '说话人2', voice_id: '' },
          { speaker: '旁白', voice_id: '' }
        ]
      }
    } else {
      formData.voice_mappings = [
        { speaker: '说话人1', voice_id: '' },
        { speaker: '说话人2', voice_id: '' },
        { speaker: '旁白', voice_id: '' }
      ]
    }

    // 解析专有词汇表
    if (Array.isArray(newProject.custom_vocabulary)) {
      // 如果是数组格式，转换为字符串显示
      formData.custom_vocabulary = newProject.custom_vocabulary.join('\n')
    } else if (typeof newProject.custom_vocabulary === 'string') {
      formData.custom_vocabulary = newProject.custom_vocabulary
    } else {
      formData.custom_vocabulary = ''
    }
  }
}, { immediate: true })

// 角色音色映射管理
const addSpeakerMapping = () => {
  formData.voice_mappings.push({
    speaker: '',
    voice_id: ''
  })
}

const removeSpeakerMapping = (index: number) => {
  if (formData.voice_mappings.length > 1) {
    formData.voice_mappings.splice(index, 1)
  }
}

const handleSave = async () => {
  if (!settingsForm.value) return

  try {
    await settingsForm.value.validate()

    // 过滤空的角色映射
    const validMappings = formData.voice_mappings.filter(
      mapping => mapping.speaker.trim() && mapping.voice_id.trim()
    )

    // 处理专有词汇表，转换为数组格式
    const vocabularyArray = formData.custom_vocabulary
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)

    const saveData = {
      ...formData,
      voice_mappings: validMappings,
      custom_vocabulary: vocabularyArray
    }

    // 发送保存事件到父组件
    emit('save', saveData)
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-slider) {
  margin: 12px 0;
}

:deep(.el-checkbox) {
  margin-right: 16px;
  margin-bottom: 8px;
}

.voice-config-section {
  width: 100%;
}

.voice-mapping-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.arrow {
  color: #909399;
  font-weight: bold;
  min-width: 20px;
  text-align: center;
}

.vocabulary-hint {
  margin-top: 8px;
  color: #909399;
  line-height: 1.4;
}

@media (max-width: 768px) {
  :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto !important;
  }

  :deep(.el-form-item__label) {
    width: 100px !important;
  }

  .voice-mapping-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .voice-mapping-row .el-input {
    width: 100% !important;
  }

  .arrow {
    display: none;
  }
}
</style>