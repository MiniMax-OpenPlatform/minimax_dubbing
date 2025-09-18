<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AuthSetup from './components/AuthSetup.vue'
import ProjectList from './components/ProjectList.vue'
import ProjectDetail from './components/ProjectDetail.vue'
import { Document, Setting, List, Monitor, Delete, SwitchButton } from '@element-plus/icons-vue'
import { logger } from './utils/logger'

const isAuthenticated = ref(false)
const currentView = ref('projects')
const selectedProjectId = ref<number | null>(null)
const sidebarCollapsed = ref(false)

const handleAuthenticated = () => {
  isAuthenticated.value = true
  logger.addLog('success', '用户认证成功', 'Auth')
}

const showProjectDetail = (projectId: number) => {
  selectedProjectId.value = projectId
  currentView.value = 'detail'
  logger.addLog('info', `打开项目详情: ID ${projectId}`, 'Navigation')
}

const backToProjects = () => {
  currentView.value = 'projects'
  selectedProjectId.value = null
  logger.addLog('info', '返回项目列表', 'Navigation')
}

const logout = () => {
  localStorage.removeItem('group_id')
  localStorage.removeItem('api_key')
  isAuthenticated.value = false
  currentView.value = 'projects'
  selectedProjectId.value = null
  logger.addLog('info', '用户退出登录', 'Auth')
  logger.clearLogs()
}

const navigateTo = (view: string) => {
  currentView.value = view
  selectedProjectId.value = null
  const viewNames: Record<string, string> = {
    'projects': '项目管理',
    'logs': '系统日志',
    'settings': '系统设置'
  }
  logger.addLog('info', `导航到: ${viewNames[view] || view}`, 'Navigation')
}

// 为模板提供localStorage访问
const getStorageItem = (key: string) => {
  return localStorage.getItem(key)
}

// 系统信息
const systemInfo = {
  browser: navigator.userAgent.split(' ').slice(-2).join(' '),
  screenResolution: `${screen.width} × ${screen.height}`,
  viewportSize: `${window.innerWidth} × ${window.innerHeight}`
}

onMounted(() => {
  // 检查是否已有认证信息
  const groupId = localStorage.getItem('group_id')
  const apiKey = localStorage.getItem('api_key')
  if (groupId && apiKey) {
    isAuthenticated.value = true
    logger.addLog('info', '应用启动，从本地存储恢复认证信息', 'App')
  } else {
    logger.addLog('info', '应用启动，需要用户认证', 'App')
  }
})
</script>

<template>
  <!-- 未认证时显示认证设置 -->
  <AuthSetup v-if="!isAuthenticated" @authenticated="handleAuthenticated" />

  <!-- 已认证时显示主应用 -->
  <el-container v-else style="height: 100vh">
    <!-- 顶部导航栏 -->
    <el-header style="background-color: #001529; color: white; padding: 0 20px; border-bottom: 1px solid #f0f0f0;">
      <div style="display: flex; align-items: center; height: 100%;">
        <el-icon style="font-size: 24px; margin-right: 12px; color: #1890ff;">
          <Document />
        </el-icon>
        <h1 style="margin: 0; font-size: 20px;">MiniMax 翻译工具</h1>

        <div style="margin-left: auto; display: flex; align-items: center;">
          <el-button
            type="text"
            style="color: white;"
            @click="sidebarCollapsed = !sidebarCollapsed"
          >
            <el-icon><List /></el-icon>
            {{ sidebarCollapsed ? '展开' : '收起' }}菜单
          </el-button>
          <el-button type="danger" @click="logout" style="margin-left: 10px;">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </div>
    </el-header>

    <el-container>
      <!-- 左侧导航栏 -->
      <el-aside :width="sidebarCollapsed ? '60px' : '200px'" style="background-color: #f0f2f5; transition: width 0.2s ease;">
        <el-menu
          :default-active="currentView"
          :collapse="sidebarCollapsed"
          style="height: 100%; border-right: none;"
          @select="navigateTo"
        >
          <el-menu-item index="projects">
            <el-icon><Document /></el-icon>
            <span>项目管理</span>
          </el-menu-item>

          <el-menu-item index="logs">
            <el-icon><Monitor /></el-icon>
            <span>系统日志</span>
          </el-menu-item>

          <el-menu-item index="settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-main class="main-content">
        <div class="content-container">
          <!-- 项目列表页面 -->
          <ProjectList
            v-if="currentView === 'projects'"
            :key="'projects'"
            @show-detail="showProjectDetail"
          />

          <!-- 项目详情页面 -->
          <ProjectDetail
            v-if="currentView === 'detail' && selectedProjectId"
            :key="`detail-${selectedProjectId}`"
            :project-id="selectedProjectId"
            @back="backToProjects"
          />

          <!-- 系统日志页面 -->
          <div v-if="currentView === 'logs'" :key="'logs'" class="page-content logs-page">
            <div class="page-header">
              <h2>系统日志</h2>
              <el-button @click="logger.clearLogs" type="danger">
                <el-icon><Delete /></el-icon>
                清空日志
              </el-button>
            </div>

            <div class="logs-container">
              <div class="logs-table-wrapper">
                <el-table
                  :data="logger.logs.value"
                  class="logs-table"
                  height="calc(100vh - 300px)"
                  stripe
                  :border="true"
                  style="width: 100%;"
                >
                  <el-table-column prop="timestamp" label="时间" width="200" show-overflow-tooltip />
                  <el-table-column prop="level" label="级别" width="120" align="center">
                    <template #default="{ row }">
                      <el-tag
                        :type="row.level === 'error' ? 'danger' : row.level === 'success' ? 'success' : row.level === 'warning' ? 'warning' : 'info'"
                        size="small"
                      >
                        {{ row.level.toUpperCase() }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="module" label="模块" width="150" align="center">
                    <template #default="{ row }">
                      <el-tag v-if="row.module" size="small" type="info">
                        {{ row.module }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="message" label="消息" show-overflow-tooltip />
                </el-table>

                <div v-if="logger.logs.value.length === 0" class="empty-logs">
                  <el-empty description="暂无日志记录" />
                </div>
              </div>
            </div>
          </div>

          <!-- 系统设置页面 -->
          <div v-if="currentView === 'settings'" :key="'settings'" class="page-content">
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
                    {{ logger.logs.value.length }} / 100
                  </el-descriptions-item>
                  <el-descriptions-item label="当前页面">
                    {{ currentView }}
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
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.el-header {
  display: flex;
  align-items: center;
}

/* 主内容区域样式 */
.main-content {
  padding: 0;
  background-color: #f5f5f5;
  overflow: auto;
}

.content-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
  min-height: calc(100vh - 60px);
}

/* 页面内容通用样式 */
.page-content {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

/* 表格卡片样式 */
.table-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
}

/* 日志页面样式 - 简化版本 */
.logs-page {
  width: 100%;
}

.logs-container {
  width: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.logs-table-wrapper {
  width: 100%;
  position: relative;
}

/* 表格样式优化 - 使用Element Plus默认行为但确保宽度 */
.logs-table {
  width: 100%;
}

.logs-table :deep(.el-table) {
  width: 100%;
}

.logs-table :deep(.el-table__header-wrapper),
.logs-table :deep(.el-table__body-wrapper) {
  width: 100%;
}

/* 只禁用可能影响宽度展开的动画 */
.logs-table :deep(.el-table__column-resize-proxy) {
  display: none;
}

.empty-logs {
  padding: 40px;
  text-align: center;
}

/* 设置页面网格布局 */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
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
  .content-container {
    max-width: 100%;
    padding: 15px;
  }

  .settings-grid {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 15px;
  }
}

@media (max-width: 768px) {
  .content-container {
    padding: 10px;
  }

  .settings-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .page-header h2 {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }

  .settings-card {
    margin: 0;
  }
}

/* 确保表格在小屏幕上的响应式 */
@media (max-width: 768px) {
  .table-card :deep(.el-table) {
    font-size: 12px;
  }

  .table-card :deep(.el-table .el-table__cell) {
    padding: 8px 4px;
  }
}


/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .main-content {
    background-color: #1a1a1a;
  }

  .page-header {
    background: #2a2a2a;
    color: #e4e7ed;
  }

  .page-header h2 {
    color: #e4e7ed;
  }
}
</style>
