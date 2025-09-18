<template>
  <el-dialog
    :title="dialogTitle"
    :model-value="visible"
    width="400px"
    @close="$emit('close')"
    @update:model-value="$emit('close')"
  >
    <div class="batch-settings-form">
      <p class="form-description">
        将为选中的 {{ selectedCount }} 个段落设置{{ settingLabel }}
      </p>

      <!-- 音色设置 -->
      <el-select
        v-if="settingType === 'voice'"
        v-model="currentValue"
        placeholder="选择音色"
        style="width: 100%"
      >
        <el-option label="通用女声" value="female_001" />
        <el-option label="通用男声" value="male_001" />
        <el-option label="温柔女声" value="female_002" />
        <el-option label="磁性男声" value="male_002" />
        <el-option label="甜美女声" value="female_003" />
        <el-option label="成熟男声" value="male_003" />
      </el-select>

      <!-- 情感设置 -->
      <el-select
        v-else-if="settingType === 'emotion'"
        v-model="currentValue"
        placeholder="选择情感"
        style="width: 100%"
      >
        <el-option label="平静" value="calm" />
        <el-option label="开心" value="happy" />
        <el-option label="悲伤" value="sad" />
        <el-option label="愤怒" value="angry" />
        <el-option label="兴奋" value="excited" />
        <el-option label="温柔" value="gentle" />
      </el-select>

      <!-- 语速设置 -->
      <div v-else-if="settingType === 'speed'" class="speed-setting">
        <el-slider
          v-model="currentValue"
          :min="0.5"
          :max="2.0"
          :step="0.1"
          show-input
          :format-tooltip="formatSpeedTooltip"
        />
        <div class="speed-labels">
          <span>慢速 (0.5x)</span>
          <span>正常 (1.0x)</span>
          <span>快速 (2.0x)</span>
        </div>
      </div>

      <!-- 说话人设置 -->
      <el-input
        v-else-if="settingType === 'speaker'"
        v-model="currentValue"
        placeholder="输入说话人名称"
        maxlength="20"
        show-word-limit
      />

      <div class="form-actions">
        <el-button @click="$emit('close')">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="handleConfirm"
          :disabled="!currentValue"
        >
          确定设置
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

type SettingType = 'voice' | 'emotion' | 'speed' | 'speaker'

const props = defineProps<{
  visible: boolean
  settingType: SettingType
  selectedCount: number
}>()

const emit = defineEmits<{
  close: []
  confirm: [value: any]
}>()

const currentValue = ref<any>('')

// 重置值当类型改变时
watch(() => props.settingType, (newType) => {
  switch (newType) {
    case 'speed':
      currentValue.value = 1.0
      break
    default:
      currentValue.value = ''
  }
})

// 对话框标题
const dialogTitle = computed(() => {
  const titles = {
    voice: '批量设置音色',
    emotion: '批量设置情感',
    speed: '批量设置语速',
    speaker: '批量设置说话人'
  }
  return titles[props.settingType]
})

// 设置标签
const settingLabel = computed(() => {
  const labels = {
    voice: '音色',
    emotion: '情感',
    speed: '语速',
    speaker: '说话人'
  }
  return labels[props.settingType]
})

// 格式化语速提示
const formatSpeedTooltip = (value: number) => {
  return `${value}x`
}

// 确认设置
const handleConfirm = () => {
  if (currentValue.value) {
    emit('confirm', currentValue.value)
  }
}
</script>

<style scoped>
.batch-settings-form {
  padding: 8px 0;
}

.form-description {
  margin-bottom: 20px;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.speed-setting {
  margin: 16px 0;
}

.speed-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>