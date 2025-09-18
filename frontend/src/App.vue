<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AuthSetup from './components/AuthSetup.vue'
import ProjectList from './components/ProjectList.vue'
import ProjectDetail from './components/ProjectDetail.vue'

const isAuthenticated = ref(false)
const currentView = ref('projects')
const selectedProjectId = ref<number | null>(null)

const handleAuthenticated = () => {
  isAuthenticated.value = true
}

const showProjectDetail = (projectId: number) => {
  selectedProjectId.value = projectId
  currentView.value = 'detail'
}

const backToProjects = () => {
  currentView.value = 'projects'
  selectedProjectId.value = null
}

const logout = () => {
  localStorage.removeItem('group_id')
  localStorage.removeItem('api_key')
  isAuthenticated.value = false
  currentView.value = 'projects'
  selectedProjectId.value = null
}

onMounted(() => {
  // 检查是否已有认证信息
  const groupId = localStorage.getItem('group_id')
  const apiKey = localStorage.getItem('api_key')
  if (groupId && apiKey) {
    isAuthenticated.value = true
  }
})
</script>

<template>
  <!-- 未认证时显示认证设置 -->
  <AuthSetup v-if="!isAuthenticated" @authenticated="handleAuthenticated" />

  <!-- 已认证时显示主应用 -->
  <el-container v-else style="height: 100vh">
    <!-- 头部导航 -->
    <el-header style="background-color: #409eff; color: white; padding: 0 20px;">
      <div style="display: flex; align-items: center; height: 100%;">
        <h1 style="margin: 0;">MiniMax 翻译工具</h1>
        <div style="margin-left: auto;">
          <el-button type="primary" @click="backToProjects" v-if="currentView === 'detail'">
            <el-icon><Back /></el-icon>
            返回项目列表
          </el-button>
          <el-button type="danger" @click="logout" style="margin-left: 10px;">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </div>
    </el-header>

    <!-- 主内容区域 -->
    <el-main style="padding: 20px;">
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
    </el-main>
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
</style>
