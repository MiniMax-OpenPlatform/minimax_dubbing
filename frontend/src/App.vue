<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoginForm from './components/auth/LoginForm.vue'
import ProjectList from './components/ProjectList.vue'
import ProjectDetailContainer from './components/project/ProjectDetailContainer.vue'
import UserSettings from './components/UserSettings.vue'
import VoiceManagement from './components/voice/VoiceManagement.vue'
import VoiceCloning from './components/voice/VoiceCloning.vue'
import UserGuide from './components/UserGuide.vue'
import About from './components/About.vue'
import { Document, Setting, User, ArrowDown, Microphone, MagicStick, Reading, Link } from '@element-plus/icons-vue'
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
    'voices': '音色管理',
    'voice-cloning': '音色克隆',
    'user-guide': '使用说明',
    'user-settings': '账户设置',
    'about': '关于'
  }
  logger.addLog('info', `导航到: ${viewNames[view] || view}`, 'Navigation')
}

const openAdminPage = () => {
  // 打开Django后台管理页面
  // 使用统一的URL工具函数，自动适配本地开发和生产环境
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  const currentPort = window.location.port

  let adminUrl
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    adminUrl = `${protocol}//${hostname}:5172/admin/`
  } else if (currentPort && currentPort !== '80' && currentPort !== '443') {
    adminUrl = `${protocol}//${hostname}:${currentPort}/dubbing/admin/`
  } else {
    adminUrl = `/dubbing/admin/`
  }

  window.open(adminUrl, '_blank')
  logger.addLog('info', '打开Django后台管理页面', 'Navigation')
}

const openGitHub = () => {
  window.open('https://github.com/MiniMax-OpenPlatform/minimax_dubbing', '_blank')
  logger.addLog('info', '打开GitHub仓库', 'Navigation')
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
      <div style="display: flex; align-items: center; height: 100%; width: 100%;">
        <!-- 左侧标题 -->
        <div style="display: flex; align-items: center; flex-shrink: 0;">
          <h1 style="margin: 0; font-size: 20px;">MiniMax 翻译工具</h1>
        </div>

        <!-- 中间导航菜单 -->
        <div class="nav-menu" style="flex-shrink: 0;">
          <div
            class="nav-item"
            :class="{ active: currentView === 'projects' }"
            @click="navigateTo('projects')"
          >
            <el-icon><Document /></el-icon>
            <span>项目管理</span>
          </div>

          <div
            class="nav-item"
            :class="{ active: currentView === 'voices' }"
            @click="navigateTo('voices')"
          >
            <el-icon><Microphone /></el-icon>
            <span>音色管理</span>
          </div>

          <div
            class="nav-item"
            :class="{ active: currentView === 'voice-cloning' }"
            @click="navigateTo('voice-cloning')"
          >
            <el-icon><MagicStick /></el-icon>
            <span>音色克隆</span>
          </div>

          <div
            class="nav-item"
            :class="{ active: currentView === 'user-guide' }"
            @click="navigateTo('user-guide')"
          >
            <el-icon><Reading /></el-icon>
            <span>使用说明</span>
          </div>

          <div
            class="nav-item github-link"
            @click="openGitHub"
            title="查看 GitHub 仓库"
          >
            <svg class="github-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
            </svg>
            <span>GitHub</span>
          </div>

        </div>

        <!-- 右侧用户区域 -->
        <div class="user-area">
          <!-- 用户信息下拉菜单 -->
          <el-dropdown trigger="hover">
            <div class="user-info-trigger">
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
                  <span>用户设置</span>
                </el-dropdown-item>
                <el-dropdown-item @click="openAdminPage">
                  <el-icon><Setting /></el-icon>
                  <span>后台管理</span>
                </el-dropdown-item>
                <el-dropdown-item divided @click="navigateTo('about')">
                  <el-icon><Document /></el-icon>
                  <span>关于</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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

        <!-- 音色管理页面 -->
        <VoiceManagement v-if="currentView === 'voices'" />

        <!-- 音色克隆页面 -->
        <VoiceCloning v-if="currentView === 'voice-cloning'" />

        <!-- 使用说明页面 -->
        <UserGuide v-if="currentView === 'user-guide'" />

        <!-- 账户设置页面 -->
        <UserSettings v-if="currentView === 'user-settings'" @logout="logout" />

        <!-- 关于页面 -->
        <About v-if="currentView === 'about'" />

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

/* 自定义导航菜单样式 */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 20px;
  justify-content: flex-start;
  margin-left: 40px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
}

.nav-item:hover {
  color: #fff;
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
  background-color: rgba(24, 144, 255, 0.1);
}

.nav-item .el-icon {
  font-size: 16px;
}

.nav-item span {
  font-size: 14px;
  font-weight: 500;
}

/* GitHub 链接样式 */
.github-link {
  position: relative;
}

.github-link .github-icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.github-link:hover .github-icon {
  fill: #fff;
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

/* 用户区域样式 */
.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  padding-left: 20px;
  margin-left: auto;
  flex-shrink: 0;
  flex-grow: 0;
}


/* 用户信息触发器样式 */
.user-info-trigger {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.3s;
}

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
