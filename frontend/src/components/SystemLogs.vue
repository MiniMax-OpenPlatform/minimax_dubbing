<template>
  <div class="system-logs">
    <div class="logs-header">
      <h2>系统日志</h2>
      <div class="header-actions">
        <el-button @click="refreshLogs" type="primary" size="small" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="downloadLogs" type="success" size="small">
          <el-icon><Download /></el-icon>
          下载
        </el-button>
        <el-button @click="clearLogs" type="danger" size="small" :loading="clearLoading">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <div class="logs-content-wrapper">
      <el-loading v-loading="loading" element-loading-text="加载日志中...">
        <pre
          v-if="rawLogs"
          class="logs-content"
          ref="logsContentRef"
        >{{ rawLogs }}</pre>
        <el-empty
          v-else
          description="暂无日志记录"
          :image-size="100"
        />
      </el-loading>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { Refresh, Download, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../utils/api'

const rawLogs = ref('')
const loading = ref(false)
const clearLoading = ref(false)
const logsContentRef = ref<HTMLElement>()

// 刷新日志
const refreshLogs = async () => {
  loading.value = true
  try {
    const response = await api.get('/logs/raw/')
    rawLogs.value = response.data

    // 自动滚动到底部显示最新日志
    await nextTick()
    if (logsContentRef.value) {
      logsContentRef.value.scrollTop = logsContentRef.value.scrollHeight
    }

    ElMessage.success('日志刷新成功')
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

// 下载日志
const downloadLogs = () => {
  if (!rawLogs.value) {
    ElMessage.warning('暂无日志可下载')
    return
  }

  const blob = new Blob([rawLogs.value], { type: 'text/plain;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `system_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.log`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)

  ElMessage.success('日志下载完成')
}

// 清空日志
const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有系统日志吗？此操作不可撤销。',
      '清空日志确认',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    clearLoading.value = true
    await api.delete('/logs/clear/')
    rawLogs.value = ''
    ElMessage.success('日志清空成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空日志失败:', error)
      ElMessage.error('清空日志失败')
    }
  } finally {
    clearLoading.value = false
  }
}

// 组件挂载时加载日志
onMounted(() => {
  refreshLogs()
})
</script>

<style scoped>
.system-logs {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.logs-header h2 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.logs-content-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.logs-content {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #2c3e50;
  background: #f8f9fa;
  border: none;
  outline: none;
  overflow: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  box-sizing: border-box;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .logs-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  .logs-content {
    font-size: 11px;
    padding: 12px;
  }
}
</style>