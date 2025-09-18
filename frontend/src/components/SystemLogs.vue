<template>
  <div class="system-logs">
    <div class="logs-header">
      <h2>系统日志</h2>
      <el-button @click="clearLogs" type="danger">
        <el-icon><Delete /></el-icon>
        清空日志
      </el-button>
    </div>

    <el-card class="logs-card">
      <el-table
        :data="logs"
        height="calc(100vh - 300px)"
        stripe
        :border="true"
        style="width: 100%;"
        :table-layout="'auto'"
        :fit="true"
      >
        <el-table-column prop="timestamp" label="时间" width="180" show-overflow-tooltip />
        <el-table-column prop="level" label="级别" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.level === 'error' ? 'danger' : row.level === 'success' ? 'success' : row.level === 'warning' ? 'warning' : 'info'"
              size="small"
            >
              {{ row.level.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.module" size="small" type="info">
              {{ row.module }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
      </el-table>

      <el-empty v-if="logs.length === 0" description="暂无日志记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { logger } from '../utils/logger'

const logs = computed(() => logger.logs.value)

const clearLogs = () => {
  logger.clearLogs()
}
</script>

<style scoped>
.system-logs {
  width: 100%;
  min-width: 0;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  box-sizing: border-box;
}

.logs-header h2 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.logs-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 100%;
  box-sizing: border-box;
}

:deep(.el-table) {
  width: 100% !important;
  table-layout: auto;
}

:deep(.el-card__body) {
  padding: 0;
  width: 100%;
}
</style>