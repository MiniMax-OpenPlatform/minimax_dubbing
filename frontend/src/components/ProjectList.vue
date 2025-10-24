<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Delete } from '@element-plus/icons-vue'
import api from '../utils/api'
import { logger } from '../utils/logger'

interface Project {
  id: number
  name: string
  source_lang: string
  target_lang: string
  created_at: string
  segment_count: number
  completed_segment_count: number
  progress_percentage: number
}

const emit = defineEmits<{
  showDetail: [projectId: number]
}>()

const projects = ref<Project[]>([])
const loading = ref(false)
const createDialogVisible = ref(false)
const createForm = ref({
  name: '',
  description: '',
  source_lang: 'Chinese',
  target_lang: 'English'
})

const loadProjects = async () => {
  loading.value = true
  logger.addLog('info', '开始加载项目列表', 'ProjectList')
  try {
    const response = await api.get('/projects/')
    projects.value = response.data.results || []
    logger.addLog('success', `成功加载 ${projects.value.length} 个项目`, 'ProjectList')
  } catch (error) {
    ElMessage.error('加载项目列表失败')
    logger.addLog('error', '加载项目列表失败', 'ProjectList')
    console.error('Load projects error:', error)
  } finally {
    loading.value = false
  }
}

const handleCreateProject = async () => {
  if (!createForm.value.name) {
    ElMessage.error('请输入项目名称')
    logger.addLog('warning', '未输入项目名称，创建取消', 'ProjectList')
    return
  }

  logger.addLog('info', `开始创建项目: ${createForm.value.name}`, 'ProjectList')

  try {
    const response = await api.post('/projects/', createForm.value)
    ElMessage.success('项目创建成功')
    logger.addLog('success', `项目 "${createForm.value.name}" 创建成功`, 'ProjectList')

    createDialogVisible.value = false
    createForm.value = {
      name: '',
      description: '',
      source_lang: 'Chinese',
      target_lang: 'English'
    }

    loadProjects()

    // 自动跳转到项目详情页
    if (response.data && response.data.id) {
      emit('showDetail', response.data.id)
    }
  } catch (error) {
    ElMessage.error('创建项目失败')
    logger.addLog('error', `项目创建失败: ${error}`, 'ProjectList')
    console.error('Create project error:', error)
  }
}

const handleDeleteProject = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？删除后无法恢复，项目中的所有段落和音频文件将一并删除。`,
      '删除项目确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    logger.addLog('info', `开始删除项目: ${project.name} (ID: ${project.id})`, 'ProjectList')

    await api.delete(`/projects/${project.id}/`)
    ElMessage.success('项目删除成功')
    logger.addLog('success', `项目 "${project.name}" 删除成功`, 'ProjectList')

    // 重新加载项目列表
    loadProjects()
  } catch (error: any) {
    if (error === 'cancel') {
      logger.addLog('info', `取消删除项目: ${project.name}`, 'ProjectList')
      return
    }

    ElMessage.error('删除项目失败')
    logger.addLog('error', `删除项目失败: ${error}`, 'ProjectList')
    console.error('Delete project error:', error)
  }
}


onMounted(() => {
  loadProjects()
})
</script>

<template>
  <div>
    <!-- 操作栏 -->
    <div style="margin-bottom: 20px;">
      <el-button type="primary" @click="createDialogVisible = true">
        <el-icon><Plus /></el-icon>
        新建项目
      </el-button>
      <el-button @click="loadProjects">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 项目列表 -->
    <el-table :data="projects" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="项目名称" min-width="200">
        <template #default="{ row }">
          <el-link type="primary" @click="$emit('showDetail', row.id)">
            {{ row.name }}
          </el-link>
        </template>
      </el-table-column>

      <el-table-column prop="source_lang" label="源语言" width="100" />
      <el-table-column prop="target_lang" label="目标语言" width="100" />


      <el-table-column label="进度" width="150">
        <template #default="{ row }">
          <el-progress
            :percentage="row.progress_percentage"
            :status="row.progress_percentage === 100 ? 'success' : undefined"
          />
          <div style="font-size: 12px; color: #666; margin-top: 4px;">
            {{ row.completed_segment_count }} / {{ row.segment_count }} 段落
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="$emit('showDetail', row.id)">
            查看详情
          </el-button>
          <el-button
            size="small"
            type="danger"
            :icon="Delete"
            @click="handleDeleteProject(row)"
            style="margin-left: 8px;"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建项目对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建项目" width="500px">
      <el-form label-width="100px">
        <el-form-item label="项目名称" required>
          <el-input
            v-model="createForm.name"
            placeholder="请输入项目名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="项目描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            placeholder="请输入项目描述（可选）"
            :rows="3"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="源语言">
          <el-select v-model="createForm.source_lang" placeholder="请选择源语言">
            <el-option label="中文" value="Chinese" />
            <el-option label="英文" value="English" />
            <el-option label="日文" value="Japanese" />
            <el-option label="韩文" value="Korean" />
            <el-option label="法文" value="French" />
            <el-option label="德文" value="German" />
            <el-option label="西班牙文" value="Spanish" />
          </el-select>
        </el-form-item>

        <el-form-item label="目标语言">
          <el-select v-model="createForm.target_lang" placeholder="请选择目标语言">
            <el-option label="英文" value="English" />
            <el-option label="中文" value="Chinese" />
            <el-option label="日文" value="Japanese" />
            <el-option label="韩文" value="Korean" />
            <el-option label="法文" value="French" />
            <el-option label="德文" value="German" />
            <el-option label="西班牙文" value="Spanish" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateProject">创建项目</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.upload-demo {
  width: 100%;
}
</style>