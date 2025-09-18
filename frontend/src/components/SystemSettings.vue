<template>
  <div class="system-settings">
    <h2>系统设置</h2>

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
          <el-descriptions-item label="前端地址">http://10.11.17.19:5174</el-descriptions-item>
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
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { logger } from '../utils/logger'

const emit = defineEmits<{
  logout: []
}>()

const getStorageItem = (key: string) => {
  return localStorage.getItem(key)
}

const systemInfo = {
  browser: navigator.userAgent.split(' ').slice(-2).join(' '),
  screenResolution: `${screen.width} × ${screen.height}`,
  viewportSize: `${window.innerWidth} × ${window.innerHeight}`
}

const logCount = computed(() => logger.logs.value.length)

const logout = () => {
  emit('logout')
}
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

/* 响应式设计 */
@media (max-width: 1200px) {
  .settings-grid {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 15px;
  }
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
}
</style>