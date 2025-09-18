<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AuthSetup from './components/AuthSetup.vue'
import ProjectList from './components/ProjectList.vue'
import ProjectDetail from './components/ProjectDetail.vue'
import SystemLogs from './components/SystemLogs.vue'
import SystemSettings from './components/SystemSettings.vue'
import { Document, Setting, List, Monitor, SwitchButton } from '@element-plus/icons-vue'
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

onMounted(() => {
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
            @show-detail="showProjectDetail"
          />

          <!-- 项目详情页面 -->
          <ProjectDetail
            v-if="currentView === 'detail' && selectedProjectId"
            :project-id="selectedProjectId"
            @back="backToProjects"
          />

          <!-- 系统日志页面 -->
          <SystemLogs v-if="currentView === 'logs'" />

          <!-- 系统设置页面 -->
          <SystemSettings v-if="currentView === 'settings'" @logout="logout" />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
/* 全局字体设置 */
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

/* 头部导航栏 */
.el-header {
  display: flex;
  align-items: center;
}

/* 主内容区域 */
.main-content {
  padding: 0;
  background-color: #f5f5f5;
  overflow: auto;
}

/* 内容容器 - 统一宽度管理 */
.content-container {
  margin: 0;
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
  min-height: calc(100vh - 60px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-container {
    padding: 15px;
  }
}

@media (max-width: 768px) {
  .content-container {
    padding: 10px;
  }
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .main-content {
    background-color: #1a1a1a;
  }
}
</style>
