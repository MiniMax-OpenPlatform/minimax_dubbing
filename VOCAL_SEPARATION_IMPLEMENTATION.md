# 人声分离功能实现文档

## ✅ 已完成部分

### 1. 独立音频分离模块 (`services/audio_separator/`)
- ✅ `__init__.py` - 模块初始化
- ✅ `base_separator.py` - 抽象基类
- ✅ `demucs_separator.py` - Demucs实现（CPU优化）
- ✅ `utils.py` - 工具函数（音频提取、时长计算等）

### 2. 数据库模型扩展
- ✅ 添加字段到 `projects/models.py`:
  - `original_audio_path` - 原始音频
  - `vocal_audio_path` - 人声音频
  - `background_audio_path` - 背景音
  - `separation_status` - 分离状态
  - `separation_started_at` - 开始时间
  - `separation_completed_at` - 完成时间
- ✅ 添加属性方法：
  - `audio_url` - 返回人声音频URL
  - `background_audio_url` - 返回背景音URL
- ✅ 数据库迁移已创建并应用

### 3. 后端任务和API
- ✅ Celery配置 (`backend/celery.py`, `backend/__init__.py`)
- ✅ settings.py添加Celery配置
- ✅ 异步任务 (`projects/tasks.py`):
  - `separate_vocals_sync` - 同步分离函数
  - `start_vocal_separation_task` - 启动后台线程
- ✅ API接口 (`projects/views.py`):
  - `separate_vocals` action - POST /api/projects/{id}/separate_vocals/
- ✅ Serializer更新 (`projects/serializers.py`):
  - 添加 `background_audio_url`
  - 添加分离状态字段

## 📋 待完成部分

### 4. 前端集成（需要手动完成）

#### 4.1 启用人声分离按钮
**文件**: `frontend/src/components/editor/EditorToolbar.vue`

修改第18-25行：
```vue
<!-- 修改前 -->
<el-button
  :icon="Headset"
  @click="handlePlaceholderClick('人声分离')"
  disabled
>
  人声分离
</el-button>

<!-- 修改后 -->
<el-button
  :icon="Headset"
  @click="$emit('separate-vocals')"
  :loading="batchLoading"
>
  人声分离
</el-button>
```

并在emits中添加：
```typescript
const emit = defineEmits<{
  // ... 现有的
  'separate-vocals': []  // 新增
}>()
```

#### 4.2 添加处理函数
**文件**: `frontend/src/components/project/ProjectDetailContainer.vue`

在EditorToolbar组件上添加事件绑定（约第36行）：
```vue
<EditorToolbar
  @separate-vocals="handleSeparateVocals"
  ...其他事件
/>
```

添加处理函数（约第880行，在handleUploadVideo后面）：
```typescript
const handleSeparateVocals = async () => {
  if (!project.value?.video_url) {
    ElMessage.warning('请先上传视频文件')
    return
  }

  try {
    await ElMessageBox.confirm(
      '人声分离需要较长时间（约视频时长的5-10倍），处理将在后台进行。是否继续？',
      '确认人声分离',
      {
        confirmButtonText: '开始分离',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const api = (await import('../../utils/api')).default
    const loadingInstance = ElLoading.service({
      lock: true,
      text: '正在启动人声分离任务...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    try {
      const response = await api.post(`/projects/${props.projectId}/separate_vocals/`)

      loadingInstance.close()

      if (response.data.success) {
        ElMessage.success(response.data.message || '人声分离任务已启动')

        // 开始轮询状态
        startPolling Separation()
      } else {
        ElMessage.warning(response.data.message || '无法启动人声分离')
      }
    } catch (error: any) {
      loadingInstance.close()
      console.error('人声分离启动失败', error)
      ElMessage.error(error.response?.data?.message || '启动人声分离失败')
    }
  } catch {
    // 用户取消
  }
}

// 轮询分离状态
const startPollingSeparation = () => {
  const pollInterval = setInterval(async () => {
    try {
      const api = (await import('../../utils/api')).default
      const response = await api.get(`/projects/${props.projectId}/`)

      const status = response.data.separation_status

      if (status === 'completed') {
        clearInterval(pollInterval)
        ElMessage.success('人声分离完成！')
        refreshData() // 刷新项目数据
      } else if (status === 'failed') {
        clearInterval(pollInterval)
        ElMessage.error('人声分离失败')
      }
      // processing状态继续等待
    } catch (error) {
      console.error('轮询状态失败', error)
    }
  }, 5000) // 每5秒轮询一次

  // 30分钟后停止轮询
  setTimeout(() => clearInterval(pollInterval), 30 * 60 * 1000)
}
```

#### 4.3 更新MediaPreview组件
**文件**: `frontend/src/components/project/MediaPreview.vue`

修改mediaOptions计算属性（约第195-217行）：
```typescript
{
  key: 'original_audio',
  label: '原始音频（人声）',  // 更新标签
  url: props.project?.audio_url ? `${BACKEND_BASE_URL}${props.project.audio_url}` : null,
  available: !!props.project?.audio_url,
  priority: 3,
  type: 'audio'
},
{
  key: 'background_audio',
  label: '背景音',
  url: props.project?.background_audio_url ? `${BACKEND_BASE_URL}${props.project.background_audio_url}` : null,  // 更新
  available: !!props.project?.background_audio_url,  // 更新
  priority: 5,
  type: 'audio'
},
```

## 📦 依赖安装

需要安装以下Python包：
```bash
pip install demucs==4.0.1
pip install torch==2.1.0
pip install torchaudio==2.1.0
pip install ffmpeg-python==0.2.0
pip install celery==5.3.4
pip install redis==5.0.1
```

系统依赖（已有）：
```bash
# FFmpeg
ffmpeg -version
```

## 🚀 启动服务

启动Redis（Celery broker）：
```bash
sudo systemctl start redis
# 或
redis-server
```

启动Celery Worker（新终端）：
```bash
celery -A backend worker -l info --concurrency=2
```

启动Django（已有）：
```bash
python manage.py runserver 0.0.0.0:5172
```

启动前端（已有）：
```bash
cd frontend && npm run dev
```

## 🧪 测试流程

1. 上传视频到项目
2. 点击"人声分离"按钮
3. 确认开始分离
4. 等待5-10分钟（取决于视频长度）
5. 完成后在媒体预览区查看：
   - 原始音频（人声）
   - 背景音

## 📝 注意事项

1. **不影响现有功能**：所有代码都是独立模块，不修改现有逻辑
2. **CPU处理较慢**：建议在测试时使用短视频（1-3分钟）
3. **后台任务**：使用线程异步执行，不阻塞主进程
4. **状态轮询**：前端每5秒轮询一次状态
5. **错误处理**：任务失败会更新status为'failed'

## 🔍 故障排查

**如果Demucs不可用**：
```bash
python -m demucs --help
```

**检查Redis连接**：
```bash
redis-cli ping
# 应该返回 PONG
```

**查看Celery任务状态**：
```bash
celery -A backend inspect active
```

**查看后端日志**：
```bash
tail -f /tmp/django_backend.log
```
