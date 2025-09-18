<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

interface Project {
  id: number
  name: string
  source_lang: string
  target_lang: string
  status: string
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
const uploadDialogVisible = ref(false)
const uploadForm = ref({
  srt_file: null as File | null,
  project_name: ''
})

const loadProjects = async () => {
  loading.value = true
  try {
    const response = await api.get('/projects/')
    projects.value = response.data.results || []
  } catch (error) {
    ElMessage.error('加载项目列表失败')
    console.error('Load projects error:', error)
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file: File) => {
  uploadForm.value.srt_file = file
  if (!uploadForm.value.project_name) {
    uploadForm.value.project_name = file.name.replace('.srt', '')
  }
}

const handleUpload = async () => {
  if (!uploadForm.value.srt_file) {
    ElMessage.error('请选择SRT文件')
    return
  }

  const formData = new FormData()
  formData.append('srt_file', uploadForm.value.srt_file)
  if (uploadForm.value.project_name) {
    formData.append('project_name', uploadForm.value.project_name)
  }

  try {
    await api.post('/projects/upload_srt/', formData)
    ElMessage.success('SRT文件上传成功')
    uploadDialogVisible.value = false
    uploadForm.value = { srt_file: null, project_name: '' }
    loadProjects()
  } catch (error) {
    ElMessage.error('上传失败')
    console.error('Upload error:', error)
  }
}

const getStatusTag = (status: string) => {
  const statusMap: Record<string, { type: string, text: string }> = {
    'draft': { type: 'info', text: '草稿' },
    'processing': { type: 'warning', text: '处理中' },
    'completed': { type: 'success', text: '已完成' },
    'failed': { type: 'danger', text: '失败' }
  }
  return statusMap[status] || { type: 'info', text: status }
}

onMounted(() => {
  loadProjects()
})
</script>

<template>
  <div>
    <!-- 操作栏 -->
    <div style="margin-bottom: 20px;">
      <el-button type="primary" @click="uploadDialogVisible = true">
        <el-icon><Upload /></el-icon>
        上传SRT文件
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

      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTag(row.status).type">
            {{ getStatusTag(row.status).text }}
          </el-tag>
        </template>
      </el-table-column>

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

      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" @click="$emit('showDetail', row.id)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传SRT文件" width="500px">
      <el-form>
        <el-form-item label="项目名称">
          <el-input v-model="uploadForm.project_name" placeholder="自动从文件名生成" />
        </el-form-item>
        <el-form-item label="SRT文件">
          <el-upload
            class="upload-demo"
            drag
            accept=".srt"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将SRT文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只支持.srt格式的文件，且不超过1MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleUpload">确认上传</el-button>
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