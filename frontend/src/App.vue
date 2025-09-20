<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoginForm from './components/auth/LoginForm.vue'
import ProjectList from './components/ProjectList.vue'
import ProjectDetailContainer from './components/project/ProjectDetailContainer.vue'
import SystemSettings from './components/SystemSettings.vue'
import UserSettings from './components/UserSettings.vue'
import { Document, Setting, SwitchButton, User, ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'
import { logger } from './utils/logger'

const authStore = useAuthStore()
const currentView = ref('projects')
const selectedProjectId = ref<number | null>(null)

const handleLoginSuccess = () => {
  logger.addLog('success', '用户登录成功', 'Auth')
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
  authStore.logout()
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
    'settings': '系统设置',
    'user-settings': '账户设置'
  }
  logger.addLog('info', `导航到: ${viewNames[view] || view}`, 'Navigation')
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    logger.addLog('info', '应用启动，检查认证状态', 'App')
    const isValid = await authStore.checkAuth()
    if (!isValid) {
      logger.addLog('warning', '认证已过期，需要重新登录', 'Auth')
    } else {
      logger.addLog('success', '认证状态有效', 'Auth')
    }
  } else {
    logger.addLog('info', '应用启动，需要用户登录', 'App')
  }
})
</script>

<template>
  <!-- 未认证时显示登录界面 -->
  <LoginForm v-if="!authStore.isAuthenticated" @login-success="handleLoginSuccess" />

  <!-- 已认证时显示主应用 -->
  <el-container v-else style="height: 100vh">
    <!-- 顶部导航栏 -->
    <el-header style="background-color: #001529; color: white; padding: 0 20px; border-bottom: 1px solid #f0f0f0;">
      <div style="display: flex; align-items: center; justify-content: space-between; height: 100%;">
        <!-- 左侧标题 -->
        <div style="display: flex; align-items: center;">
          <el-icon style="font-size: 24px; margin-right: 12px; color: #1890ff;">
            <Document />
          </el-icon>
          <h1 style="margin: 0; font-size: 20px;">MiniMax 翻译工具</h1>
        </div>

        <!-- 中间导航菜单 -->
        <el-menu
          :default-active="currentView"
          mode="horizontal"
          style="background-color: transparent; border-bottom: none; flex: 1; justify-content: center;"
          @select="navigateTo"
        >
          <el-menu-item index="projects" style="color: white;">
            <el-icon><Document /></el-icon>
            <span>项目管理</span>
          </el-menu-item>


          <el-menu-item index="settings" style="color: white;">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>

        <!-- 右侧操作按钮 -->
        <div style="display: flex; align-items: center; gap: 12px;">
          <!-- 用户信息下拉菜单 -->
          <el-dropdown trigger="hover">
            <div style="display: flex; align-items: center; cursor: pointer; color: white; padding: 8px 12px; border-radius: 6px; transition: background-color 0.3s;"
                 class="user-info-trigger">
              <el-icon style="margin-right: 8px;"><User /></el-icon>
              <span>{{ authStore.username }}</span>
              <el-icon style="margin-left: 8px; transform: rotate(0deg); transition: transform 0.3s;">
                <ArrowDown />
              </el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>
                  <div style="padding: 8px 0;">
                    <div style="font-weight: bold; margin-bottom: 4px;">{{ authStore.username }}</div>
                    <div style="font-size: 12px; color: #909399; margin-bottom: 2px;">Group ID: {{ authStore.group_id }}</div>
                    <div style="font-size: 12px; color: #909399;">API Key: {{ authStore.api_key.slice(0, 8) }}...</div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided @click="navigateTo('user-settings')">
                  <el-icon><Setting /></el-icon>
                  <span>账户设置</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button type="danger" @click="logout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </div>
    </el-header>

    <!-- 主内容区域 -->
    <el-main class="main-content" style="padding: 20px;">
      <div class="content-container">
        <!-- 项目列表页面 -->
        <ProjectList
          v-if="currentView === 'projects'"
          @show-detail="showProjectDetail"
        />

        <!-- 项目详情页面 -->
        <ProjectDetailContainer
          v-if="currentView === 'detail' && selectedProjectId"
          :project-id="selectedProjectId"
          @back="backToProjects"
        />


        <!-- 账户设置页面 -->
        <UserSettings v-if="currentView === 'user-settings'" @logout="logout" />

        <!-- 系统设置页面 -->
        <SystemSettings v-if="currentView === 'settings'" @logout="logout" />
      </div>
    </el-main>
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

/* 顶部导航菜单样式 */
.el-menu--horizontal .el-menu-item {
  color: rgba(255, 255, 255, 0.65) !important;
  border-bottom: 2px solid transparent !important;
}

.el-menu--horizontal .el-menu-item:hover {
  color: #fff !important;
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.el-menu--horizontal .el-menu-item.is-active {
  color: #1890ff !important;
  border-bottom-color: #1890ff !important;
  background-color: rgba(24, 144, 255, 0.1) !important;
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

/* 用户信息触发器hover效果 */
.user-info-trigger:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.user-info-trigger:hover .el-icon:last-child {
  transform: rotate(180deg) !important;
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .main-content {
    background-color: #1a1a1a;
  }
}
</style>
