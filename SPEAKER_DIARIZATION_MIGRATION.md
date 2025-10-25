# 说话人识别系统迁移文档

## 📋 项目概述

本文档记录了从"纯LLM说话人分配"到"人脸聚类+VLM命名+LLM分配"的完整迁移过程。

**迁移时间**: 2025-10-25
**实施范围**: Phase 1 MVP
**技术栈**: Django + Vue 3 + Threading + Qwen VLM/LLM

---

## 🔄 系统变更清单

### 一、数据库变更

#### 1.1 新增Django App: `speakers`

**创建的文件**:
- `speakers/__init__.py`
- `speakers/models.py` - 数据库模型
- `speakers/admin.py` - Django Admin配置
- `speakers/serializers.py` - DRF序列化器
- `speakers/views.py` - API ViewSet
- `speakers/urls.py` - URL路由
- `speakers/migrations/0001_initial.py` - 初始迁移

**数据库模型**:

```python
# speakers/models.py
class SpeakerDiarizationTask(models.Model):
    """说话人识别任务"""
    id = UUIDField(primary_key=True)
    project = ForeignKey(Project)
    status = CharField(choices=STATUS_CHOICES)  # pending, running, completed, failed, cancelled
    progress = IntegerField(default=0)
    progress_message = CharField(max_length=500)
    num_speakers_detected = IntegerField(null=True)
    total_faces = IntegerField(null=True)
    valid_faces = IntegerField(null=True)
    total_segments = IntegerField(null=True)
    clustering_params = JSONField(default=dict)
    filter_statistics = JSONField(default=dict)
    vlm_trace_id = CharField(max_length=200)
    llm_trace_id = CharField(max_length=200)
    error_message = TextField(blank=True)
    is_applied = BooleanField(default=False)
    applied_at = DateTimeField(null=True)
    created_at/updated_at/started_at/completed_at...

class SpeakerProfile(models.Model):
    """说话人档案"""
    task = ForeignKey(SpeakerDiarizationTask)
    speaker_id = IntegerField()
    name = CharField(max_length=100)
    role = CharField(max_length=100)
    gender = CharField(max_length=20)
    face_count = IntegerField(default=0)
    segment_count = IntegerField(default=0)
    segments = JSONField(default=list)  # [1, 5, 8, ...]
    appearance = JSONField(default=dict)
    character_analysis = JSONField(default=dict)
    representative_images = JSONField(default=list)
    avg_confidence = FloatField(default=0.0)
```

#### 1.2 修改现有模型: `projects/models.py`

**变更位置**: lines 101-109

```python
# 新增字段
current_diarization_task = models.ForeignKey(
    'speakers.SpeakerDiarizationTask',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='using_projects',
    help_text="当前使用的说话人识别任务"
)
```

**数据库迁移文件**: `projects/migrations/0012_project_current_diarization_task.py`

---

### 二、后端服务模块

#### 2.1 新增服务目录: `services/speaker_diarization/`

**创建的文件**:

1. **`srt_parser.py`** (722 bytes)
   - 功能: 从Django Segment模型解析SRT数据
   - 关键函数: `parse_srt_from_segments(segments) -> List[Dict]`

2. **`face_detector.py`** (10.1 KB)
   - 功能: MTCNN人脸检测 + FaceNet特征提取
   - 优化: CPU模式,每段3帧(原GPU模式5帧)
   - 关键类: `FaceDetector`
     - `__init__(device='cpu')` - 初始化MTCNN和FaceNet
     - `extract_frames_for_face_detection()` - 抽取关键帧
     - `detect_faces_with_quality_filter()` - 4维度质量过滤
     - `extract_face_embeddings()` - 提取512维特征向量

   **质量过滤参数**:
   - 置信度: ≥0.95
   - 人脸尺寸: ≥0.5% 画幅
   - 侧脸过滤: ratio ≤ 2.5
   - 清晰度: Laplacian ≥ 100

3. **`clusterer.py`** (4.2 KB)
   - 功能: DBSCAN聚类算法
   - 关键类: `FaceClusterer`
     - `__init__(eps=0.28, min_samples=5)`
     - `cluster_faces()` - 执行聚类,返回{speaker_id: [faces]}
     - `get_speaker_statistics()` - 统计每个说话人信息

4. **`vlm_naming.py`** (10.9 KB)
   - 功能: Qwen VLM智能命名
   - API: DashScope Qwen-VL-Max
   - 关键类: `VLMSpeakerNaming`
     - `prepare_representative_images()` - 选择2张代表图片,画红框
     - `build_vlm_prompt()` - 构建VLM提示词(图片+对话)
     - `call_qwen_vlm()` - 调用API,返回{name, role, gender, appearance, character_analysis}
     - `name_all_speakers()` - 为所有说话人命名

5. **`llm_assignment.py`** (10.0 KB)
   - 功能: Qwen LLM说话人分配
   - API: DashScope Qwen-Max (流式)
   - 关键类: `LLMSpeakerAssignment`
     - `build_assignment_prompt()` - 构建分配提示词(含画面约束)
     - `call_qwen_llm()` - 流式调用,返回{topic_summary, assignments}
     - `apply_assignments_to_segments()` - 应用到片段
     - `assign_speakers()` - 执行分配

6. **`pipeline.py`** (9.7 KB)
   - 功能: 主Pipeline编排
   - 关键类: `SpeakerDiarizationPipeline`
     - `__init__(video_path, segments, output_dir, dashscope_api_key, progress_callback)`
     - `process()` - 执行9步流程,返回结果字典

   **9步流程**:
   1. 解析SRT (10%)
   2. 初始化人脸检测模型 (15%)
   3. 抽取视频关键帧 (20%)
   4. 人脸检测+质量过滤 (35%)
   5. 提取face embeddings (50%)
   6. DBSCAN聚类 (60%)
   7. 统计说话人信息 (65%)
   8. VLM智能命名 (75%)
   9. LLM说话人分配 (85-95%)
   10. 整合结果 (100%)

7. **`__init__.py`**
   - 导出: `SpeakerDiarizationPipeline`, `process_speaker_diarization`

---

#### 2.2 后端API接口

**创建的文件**:

1. **`speakers/serializers.py`**
   - `SpeakerProfileSerializer` - 说话人档案
   - `SpeakerDiarizationTaskListSerializer` - 任务列表
   - `SpeakerDiarizationTaskDetailSerializer` - 任务详情
   - `SpeakerDiarizationTaskCreateSerializer` - 创建任务(验证project_id)
   - `ApplySpeakersSerializer` - 应用结果(验证task_id)

2. **`speakers/views.py`**
   - `SpeakerDiarizationTaskViewSet` - DRF ViewSet
     - `POST /api/speakers/tasks/` - 创建并启动任务
     - `GET /api/speakers/tasks/` - 获取任务列表
     - `GET /api/speakers/tasks/{id}/` - 获取任务详情
     - `GET /api/speakers/tasks/{id}/progress/` - 获取进度
     - `POST /api/speakers/tasks/{id}/apply/` - 应用结果
     - `DELETE /api/speakers/tasks/{id}/cancel/` - 取消任务

   **后台线程实现**:
   ```python
   thread = threading.Thread(
       target=self._run_diarization_task,
       args=(task.id, project.id, api_key)
   )
   thread.daemon = True
   thread.start()
   ```

3. **`speakers/urls.py`**
   - 注册Router: `/api/speakers/`

---

### 三、系统配置变更

#### 3.1 `backend/settings.py` (line 51)

```python
INSTALLED_APPS = [
    # ... existing apps
    'speakers',  # ✅ 新增
]
```

#### 3.2 `backend/urls.py` (line 17)

```python
urlpatterns = [
    # ... existing urls
    path('api/speakers/', include('speakers.urls')),  # ✅ 新增
]
```

#### 3.3 `requirements.txt` (lines 15-21)

```txt
# 说话人识别依赖 (Speaker Diarization)
torch==2.2.2
torchvision==0.17.2
facenet-pytorch==2.5.*
opencv-python==4.10.*
scikit-learn==1.5.*
numpy==1.26.*
```

**安装命令**:
```bash
pip install torch==2.2.2 torchvision==0.17.2 facenet-pytorch opencv-python scikit-learn numpy
```

---

### 四、前端界面变更

#### 4.1 修改 `ProjectSettings.vue`

**变更内容**:
- 对话框宽度: `600px` → `900px`
- 添加Tab布局: `<el-tabs>` 包裹内容
- Tab 1: "基础设置" (原有表单内容)
- Tab 2: "说话人档案" (新增,引入`<SpeakerProfiles>`)
- Footer: 只在"基础设置"Tab显示"保存设置"按钮

**代码结构**:
```vue
<el-tabs v-model="activeTab" type="border-card">
  <el-tab-pane label="基础设置" name="basic">
    <!-- 原有表单 -->
  </el-tab-pane>
  <el-tab-pane label="说话人档案" name="speakers">
    <SpeakerProfiles :project="project" />
  </el-tab-pane>
</el-tabs>
```

#### 4.2 新增 `SpeakerProfiles.vue`

**功能模块**:

1. **操作栏**
   - "开始说话人识别"按钮
   - "应用识别结果"按钮(完成后显示)
   - "取消任务"按钮(运行中显示)
   - "刷新"按钮

2. **当前任务卡片**
   - 任务基本信息(ID, 状态, 时间)
   - 实时进度条(pending/running时显示)
   - 错误信息(failed时显示)
   - 统计信息(完成后显示): 说话人数、总人脸数、有效人脸数、总片段数

3. **说话人档案网格**
   - 响应式Grid布局
   - 每个说话人一张卡片:
     - 基本信息: 姓名、角色、性别
     - 代表图片(2张,可预览)
     - 统计: 人脸数、片段数、平均置信度
     - 外观描述: 服装、面部特征、年龄、显著特征
     - 性格分析: 性格特点、重要程度、人物关系、说话特点
     - 出现片段列表(显示前20个)

4. **实时轮询**
   - 任务运行时,每2秒轮询进度
   - 完成/失败时自动停止轮询并刷新详情

**API调用**:
```typescript
// 启动任务
POST /api/speakers/tasks/ { project_id }

// 轮询进度
GET /api/speakers/tasks/{id}/progress/

// 获取详情
GET /api/speakers/tasks/{id}/

// 应用结果
POST /api/speakers/tasks/{id}/apply/

// 取消任务
DELETE /api/speakers/tasks/{id}/cancel/
```

---

## 🗑️ 待删除的旧实现

**注意**: 以下内容将在测试通过后删除:

1. ❌ **旧的LLM分配逻辑** (位置待确认)
   - 纯LLM说话人分配的代码
   - 可能在 `services/business/` 或 `segments/views.py`

2. ❌ **旧的"自动分配说话人"按钮** (前端)
   - 检查 `ProjectList.vue` 或 `SegmentEditor.vue`

**删除前需确认**:
- 确保新功能完全正常工作
- 备份旧代码到独立分支
- 通知团队成员变更

---

## 📊 数据流程图

```
视频文件 + SRT字幕
    ↓
[1] 抽取关键帧 (每段3帧)
    ↓
[2] MTCNN人脸检测
    ↓
[3] 4维度质量过滤
    - 置信度 ≥0.95
    - 尺寸 ≥0.5%
    - 侧脸 ≤2.5
    - 清晰度 ≥100
    ↓
[4] FaceNet提取特征 (512维)
    ↓
[5] DBSCAN聚类
    - eps=0.28
    - min_samples=5
    - metric=cosine
    ↓
[6] 按人脸数排序,分配speaker_id
    ↓
[7] 选择代表图片(2张)
    ↓
[8] Qwen VLM命名
    - 输入: 代表图片 + 出现时的对话
    - 输出: {name, role, gender, appearance, character_analysis}
    ↓
[9] Qwen LLM分配
    - 输入: 所有说话人信息 + 完整对话 + 画面出现信息
    - 输出: {topic_summary, segment_assignments}
    ↓
[10] 保存到数据库
    - SpeakerDiarizationTask (任务信息)
    - SpeakerProfile (说话人档案)
```

---

## ⚙️ 核心算法参数

### 人脸检测 (MTCNN)
```python
MTCNN(
    image_size=160,
    margin=0,
    min_face_size=40,
    thresholds=[0.6, 0.7, 0.7],
    factor=0.709,
    device='cpu'
)
```

### 质量过滤
```python
confidence_threshold = 0.95      # 置信度
size_threshold = 0.005           # 人脸尺寸占比
side_face_ratio = 2.5            # 侧脸过滤
sharpness_threshold = 100.0      # 清晰度(Laplacian)
```

### 聚类参数
```python
DBSCAN(
    eps=0.28,
    min_samples=5,
    metric='cosine'
)
```

### API配置
```python
# VLM
model = "qwen-vl-max"
api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

# LLM
model = "qwen-max"
api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
parameters = {
    "result_format": "message",
    "incremental_output": True  # 流式输出
}
```

---

## 🧪 测试清单

### 后端测试

- [ ] **数据库迁移**
  ```bash
  python manage.py makemigrations speakers
  python manage.py migrate
  ```

- [ ] **依赖安装**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **API测试**
  - [ ] 创建任务: `POST /api/speakers/tasks/`
  - [ ] 获取进度: `GET /api/speakers/tasks/{id}/progress/`
  - [ ] 获取详情: `GET /api/speakers/tasks/{id}/`
  - [ ] 应用结果: `POST /api/speakers/tasks/{id}/apply/`
  - [ ] 取消任务: `DELETE /api/speakers/tasks/{id}/cancel/`

- [ ] **Pipeline测试**
  - [ ] 准备测试视频(有清晰人脸)
  - [ ] 准备测试SRT(至少2个说话人)
  - [ ] 验证9步流程全部执行
  - [ ] 检查进度回调
  - [ ] 验证结果保存到数据库

### 前端测试

- [ ] **Tab布局**
  - [ ] "基础设置"Tab正常显示
  - [ ] "说话人档案"Tab正常切换
  - [ ] 对话框宽度900px
  - [ ] "保存设置"按钮只在基础设置Tab显示

- [ ] **说话人档案功能**
  - [ ] "开始说话人识别"按钮可用(有视频时)
  - [ ] 进度条实时更新
  - [ ] 完成后显示统计信息
  - [ ] 说话人卡片正确显示
  - [ ] 代表图片可预览
  - [ ] "应用结果"按钮正常工作

- [ ] **错误处理**
  - [ ] 无视频文件时禁用开始按钮
  - [ ] API错误时显示提示
  - [ ] 取消任务后状态正确更新

### 集成测试

- [ ] **端到端流程**
  1. 上传视频和SRT
  2. 打开项目设置
  3. 切换到"说话人档案"Tab
  4. 点击"开始说话人识别"
  5. 观察进度更新
  6. 完成后查看说话人档案
  7. 应用识别结果
  8. 验证project.current_diarization_task已更新

---

## 📝 迁移检查表

### 代码完整性

- [x] 数据库模型已创建
- [x] 迁移文件已生成
- [x] 核心服务模块已实现
- [x] API接口已完成
- [x] URL路由已配置
- [x] 前端组件已创建
- [x] Tab布局已完成

### 配置更新

- [x] settings.py 已添加 'speakers'
- [x] urls.py 已添加 speakers路由
- [x] requirements.txt 已更新依赖

### 文档

- [x] 迁移文档已创建
- [x] 代码注释完整
- [x] API文档清晰

### 待办事项

- [ ] 安装新依赖
- [ ] 运行数据库迁移
- [ ] 测试完整流程
- [ ] 删除旧实现
- [ ] 性能优化(如有必要)

---

## 🔧 故障排查

### 常见问题

**1. 依赖安装失败**
```bash
# 如果torch安装慢,使用清华镜像
pip install torch==2.2.2 torchvision==0.17.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**2. CUDA版本问题**
```python
# 确认使用CPU模式
device = torch.device('cpu')
```

**3. 内存不足**
- 减少 `max_frames_per_segment` 从3到2
- 降低视频分辨率
- 分批处理segment

**4. API调用失败**
- 检查DashScope API Key
- 确认账户余额
- 查看trace_id排查错误

**5. 前端组件导入失败**
```bash
# 确保Vue组件路径正确
cd frontend && npm run build
```

---

## 📞 联系方式

**技术支持**:
- 后端问题: 查看Django日志 `logs/app.log`
- 前端问题: 查看浏览器Console
- API问题: 检查Network请求详情

**参考文档**:
- 参考实现: `/data1/devin/test/pyannote_speaker_diarization/`
- MTCNN文档: https://github.com/timesler/facenet-pytorch
- DashScope文档: https://help.aliyun.com/zh/dashscope/

---

## 🎯 下一步计划 (Phase 2)

1. **性能优化**
   - 实现GPU加速(可选)
   - 增加缓存机制
   - 优化图片存储(CDN)

2. **功能增强**
   - 支持手动编辑说话人信息
   - 支持合并/拆分说话人
   - 导出说话人档案为PDF

3. **用户体验**
   - 添加批量操作
   - 历史任务查看
   - 统计报表

---

**文档版本**: 1.0
**最后更新**: 2025-10-25
**创建者**: Claude Code
