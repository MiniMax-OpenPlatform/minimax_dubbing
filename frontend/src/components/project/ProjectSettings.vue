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
        <el-select v-model="formData.source_lang" placeholder="请选择源语言">
          <el-option label="中文" value="zh" />
          <el-option label="英文" value="en" />
          <el-option label="日文" value="ja" />
          <el-option label="韩文" value="ko" />
        </el-select>
      </el-form-item>

      <el-form-item label="目标语言" prop="target_lang">
        <el-select v-model="formData.target_lang" placeholder="请选择目标语言">
          <el-option label="中文" value="zh" />
          <el-option label="英文" value="en" />
          <el-option label="日文" value="ja" />
          <el-option label="韩文" value="ko" />
        </el-select>
      </el-form-item>

      <el-form-item label="默认音色ID" prop="default_voice_id">
        <el-input
          v-model="formData.default_voice_id"
          placeholder="请输入默认音色ID"
        />
      </el-form-item>

      <el-form-item label="默认情绪" prop="default_emotion">
        <el-select v-model="formData.default_emotion" placeholder="请选择默认情绪">
          <el-option label="中性" value="neutral" />
          <el-option label="开心" value="happy" />
          <el-option label="悲伤" value="sad" />
          <el-option label="愤怒" value="angry" />
        </el-select>
      </el-form-item>

      <el-form-item label="默认语速" prop="default_speed">
        <el-slider
          v-model="formData.default_speed"
          :min="0.5"
          :max="3"
          :step="0.1"
          show-input
          :format-tooltip="formatSpeedTooltip"
        />
      </el-form-item>

      <el-form-item label="批量操作设置">
        <el-checkbox v-model="formData.auto_align">自动对齐时间戳</el-checkbox>
        <el-checkbox v-model="formData.skip_empty_segments">跳过空段落</el-checkbox>
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

interface ProjectSettings {
  name: string
  description: string
  source_lang: string
  target_lang: string
  default_voice_id: string
  default_emotion: string
  default_speed: number
  auto_align: boolean
  skip_empty_segments: boolean
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
  default_voice_id: 'male-qn-qingse',
  default_emotion: 'neutral',
  default_speed: 1.0,
  auto_align: true,
  skip_empty_segments: false
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
  ],
  default_voice_id: [
    { required: true, message: '请输入默认音色ID', trigger: 'blur' }
  ]
}

// 监听项目数据变化，更新表单
watch(() => props.project, (newProject) => {
  if (newProject) {
    formData.name = newProject.name || ''
    formData.description = newProject.description || ''
    formData.source_lang = newProject.source_lang || ''
    formData.target_lang = newProject.target_lang || ''
    formData.default_voice_id = newProject.default_voice_id || 'male-qn-qingse'
    formData.default_emotion = newProject.default_emotion || 'neutral'
    formData.default_speed = newProject.default_speed || 1.0
    formData.auto_align = newProject.auto_align !== false
    formData.skip_empty_segments = newProject.skip_empty_segments === true
  }
}, { immediate: true })

const formatSpeedTooltip = (value: number) => {
  return `${value}x`
}

const handleSave = async () => {
  if (!settingsForm.value) return

  try {
    await settingsForm.value.validate()
    // 发送保存事件到父组件
    emit('save', { ...formData })
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

@media (max-width: 768px) {
  :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto !important;
  }

  :deep(.el-form-item__label) {
    width: 100px !important;
  }
}
</style>