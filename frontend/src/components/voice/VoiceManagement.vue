<template>
  <div class="voice-management">
    <div class="header">
      <h2>音色管理</h2>
      <div class="header-actions">
        <el-button
          type="primary"
          @click="queryAndUpdateVoices"
          :loading="loading"
          icon="Refresh"
        >
          查询更新
        </el-button>
      </div>
    </div>

    <div class="stats" v-if="stats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_count || 0 }}</div>
              <div class="stat-label">总音色数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.system_voice_count || 0 }}</div>
              <div class="stat-label">系统音色</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.voice_cloning_count || 0 }}</div>
              <div class="stat-label">音色克隆</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ stats.voice_generation_count || 0 }}</div>
              <div class="stat-label">音色生成</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="filters">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchText"
            placeholder="搜索音色ID、名称或备注"
            clearable
            prefix-icon="Search"
          />
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterType" placeholder="音色类型" clearable>
            <el-option label="系统音色" value="system_voice" />
            <el-option label="音色克隆" value="voice_cloning" />
            <el-option label="音色生成" value="voice_generation" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <el-table
      :data="paginatedVoices"
      v-loading="tableLoading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="voice_id" label="音色ID" min-width="200">
        <template #default="scope">
          <el-text class="voice-id">{{ scope.row.voice_id }}</el-text>
        </template>
      </el-table-column>

      <el-table-column prop="voice_name" label="音色名称" width="150">
        <template #default="scope">
          <el-text>{{ scope.row.voice_name || '无名称' }}</el-text>
        </template>
      </el-table-column>

      <el-table-column prop="voice_type_display" label="类型" width="120">
        <template #default="scope">
          <el-tag
            :type="getTypeTagType(scope.row.voice_type)"
            size="small"
          >
            {{ scope.row.voice_type_display }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="description_text" label="描述" min-width="200">
        <template #default="scope">
          <el-text class="description">
            {{ scope.row.description_text || '无描述' }}
          </el-text>
        </template>
      </el-table-column>

      <el-table-column prop="user_note" label="用户备注" min-width="200">
        <template #default="scope">
          <el-input
            v-model="scope.row.user_note"
            type="textarea"
            :rows="2"
            placeholder="添加备注..."
            @blur="updateNote(scope.row)"
            size="small"
          />
        </template>
      </el-table-column>

      <el-table-column prop="created_time" label="创建时间" width="120">
        <template #default="scope">
          <el-text size="small">{{ scope.row.created_time || '未知' }}</el-text>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination" v-if="allVoices.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="filteredVoices.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

interface Voice {
  id: number
  voice_id: string
  voice_name?: string
  voice_type: 'system_voice' | 'voice_cloning' | 'voice_generation'
  voice_type_display: string
  description: string[]
  description_text: string
  user_note: string
  created_time: string
  updated_at: string
  created_at: string
}

interface Stats {
  total_count: number
  system_voice_count: number
  voice_cloning_count: number
  voice_generation_count: number
}

// 响应式数据
const allVoices = ref<Voice[]>([]) // 存储所有音色用于统计和显示
const loading = ref(false)
const tableLoading = ref(false)
const searchText = ref('')
const filterType = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const stats = ref<Stats | null>(null)

// 计算属性
const filteredVoices = computed(() => {
  let filtered = allVoices.value

  // 文本搜索
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(voice =>
      voice.voice_id.toLowerCase().includes(search) ||
      (voice.voice_name && voice.voice_name.toLowerCase().includes(search)) ||
      (voice.user_note && voice.user_note.toLowerCase().includes(search))
    )
  }

  // 类型筛选
  if (filterType.value) {
    filtered = filtered.filter(voice => voice.voice_type === filterType.value)
  }

  return filtered
})

// 分页显示的音色
const paginatedVoices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredVoices.value.slice(start, end)
})

// 方法
const getTypeTagType = (type: string) => {
  switch (type) {
    case 'system_voice':
      return 'primary'
    case 'voice_cloning':
      return 'success'
    case 'voice_generation':
      return 'warning'
    default:
      return 'info'
  }
}

const loadVoices = async () => {
  try {
    tableLoading.value = true
    // 使用no_pagination参数获取所有音色
    const response = await api.get('/voices/?no_pagination=true')
    if (response.data) {
      // 无分页时直接返回数组，有分页时返回results
      allVoices.value = Array.isArray(response.data) ? response.data : (response.data.results || response.data)
      updateStats()
    }
  } catch (error) {
    console.error('加载音色列表失败:', error)
    ElMessage.error('加载音色列表失败')
  } finally {
    tableLoading.value = false
  }
}

const queryAndUpdateVoices = async () => {
  try {
    loading.value = true
    const response = await api.post('/voices/query_and_update/')

    if (response.data.success) {
      ElMessage.success(response.data.message)
      stats.value = response.data.data
      await loadVoices()
    } else {
      ElMessage.error(response.data.message || '查询失败')
    }
  } catch (error: any) {
    console.error('查询音色失败:', error)
    const errorMsg = error.response?.data?.message || '查询音色失败'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

const updateNote = async (voice: Voice) => {
  try {
    const response = await api.patch(`/voices/${voice.id}/update_note/`, {
      user_note: voice.user_note
    })

    if (response.data.success) {
      // 静默更新，不显示成功消息
    } else {
      ElMessage.error('更新备注失败')
    }
  } catch (error) {
    console.error('更新备注失败:', error)
    ElMessage.error('更新备注失败')
  }
}

const updateStats = () => {
  const systemCount = allVoices.value.filter(v => v.voice_type === 'system_voice').length
  const cloningCount = allVoices.value.filter(v => v.voice_type === 'voice_cloning').length
  const generationCount = allVoices.value.filter(v => v.voice_type === 'voice_generation').length

  stats.value = {
    total_count: allVoices.value.length,
    system_voice_count: systemCount,
    voice_cloning_count: cloningCount,
    voice_generation_count: generationCount
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 生命周期
onMounted(() => {
  loadVoices()
})
</script>

<style scoped>
.voice-management {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #1f2328;
}

.stats {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #1f2328;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #656d76;
}

.filters {
  margin-bottom: 20px;
}

.voice-id {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #0969da;
}

.description {
  font-size: 13px;
  color: #656d76;
  line-height: 1.4;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-card) {
  border-radius: 8px;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
}

:deep(.el-button) {
  border-radius: 6px;
}
</style>