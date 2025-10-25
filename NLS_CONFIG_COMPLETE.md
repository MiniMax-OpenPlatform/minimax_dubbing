# 阿里云智能语音 NLS 配置完成

## 完成时间
2025-10-25

## 实现内容

### 1. 数据库模型更新
**文件**: `authentication/models.py`

在 `UserConfig` 模型中添加了阿里云 NLS 配置字段：

```python
# 阿里云智能语音NLS配置
aliyun_access_key_id = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    help_text="阿里云AccessKey ID"
)
aliyun_access_key_secret = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    help_text="阿里云AccessKey Secret"
)
aliyun_app_key = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    help_text="阿里云智能语音应用Key（APP_KEY）"
)
aliyun_asr_appkey = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    help_text="阿里云ASR应用Key（备用）"
)
```

**注意**: 这些字段在数据库中已经存在（从之前的迁移），所以没有创建新的迁移文件。

### 2. API 序列化器更新
**文件**: `authentication/serializers.py`

在 `UserConfigSerializer` 中暴露了 NLS 配置字段：

```python
class UserConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConfig
        fields = [
            'api_endpoint',
            'dashscope_api_key',
            'aliyun_access_key_id',      # 新增
            'aliyun_access_key_secret',  # 新增
            'aliyun_app_key',            # 新增
            'aliyun_asr_appkey',         # 新增
            'created_at',
            'updated_at'
        ]
```

### 3. 前端用户设置界面
**文件**: `frontend/src/components/UserSettings.vue`

新增了"阿里云智能语音 NLS 配置"卡片，包含三个配置项：

1. **AccessKey ID** (文本输入框)
   - 用于阿里云身份验证

2. **AccessKey Secret** (密码输入框，可显示/隐藏)
   - 用于阿里云身份验证

3. **APP KEY** (文本输入框)
   - 智能语音 NLS 应用密钥
   - 包含链接到阿里云控制台获取 APP KEY

**功能实现**:
- 页面加载时自动获取已保存的配置
- 保存配置到后端 API (`PATCH /api/auth/config/`)
- 重置功能恢复到已保存的配置
- 错误处理和成功提示

### 4. 前端实现细节

```typescript
// 表单状态
const nlsForm = reactive({
  accessKeyId: '',
  accessKeySecret: '',
  appKey: ''
})

// 加载配置
const loadNlsConfig = async () => {
  const response = await api.get('/auth/config/')
  if (response.data) {
    const config = response.data
    nlsForm.accessKeyId = config.aliyun_access_key_id || ''
    nlsForm.accessKeySecret = config.aliyun_access_key_secret || ''
    nlsForm.appKey = config.aliyun_app_key || ''
  }
}

// 保存配置
const updateNlsConfig = async () => {
  await nlsFormRef.value.validate()
  updatingNls.value = true

  await api.patch('/auth/config/', {
    aliyun_access_key_id: nlsForm.accessKeyId,
    aliyun_access_key_secret: nlsForm.accessKeySecret,
    aliyun_app_key: nlsForm.appKey
  })

  ElMessage.success('NLS 配置保存成功')
}
```

## API 端点

### 获取配置
```http
GET /api/auth/config/
Headers:
  X-Username: {username}
  X-Group-ID: {group_id}
  X-API-KEY: {api_key}

Response:
{
  "api_endpoint": "https://api.minimaxi.com",
  "dashscope_api_key": "sk-xxx",
  "aliyun_access_key_id": "LTAI...",
  "aliyun_access_key_secret": "xxx",
  "aliyun_app_key": "xxx",
  "aliyun_asr_appkey": "xxx",
  "created_at": "2025-10-25T12:00:00Z",
  "updated_at": "2025-10-25T12:30:00Z"
}
```

### 更新配置
```http
PATCH /api/auth/config/
Headers:
  X-Username: {username}
  X-Group-ID: {group_id}
  X-API-KEY: {api_key}
Content-Type: application/json

Body:
{
  "aliyun_access_key_id": "LTAI...",
  "aliyun_access_key_secret": "xxx",
  "aliyun_app_key": "xxx"
}

Response:
{
  "api_endpoint": "https://api.minimaxi.com",
  "dashscope_api_key": "sk-xxx",
  "aliyun_access_key_id": "LTAI...",
  "aliyun_access_key_secret": "xxx",
  "aliyun_app_key": "xxx",
  "aliyun_asr_appkey": "xxx",
  "created_at": "2025-10-25T12:00:00Z",
  "updated_at": "2025-10-25T12:30:00Z"
}
```

## 使用说明

### 1. 获取阿里云凭证

#### AccessKey ID 和 AccessKey Secret
1. 登录 [阿里云控制台](https://ram.console.aliyun.com/manage/ak)
2. 进入 "访问控制 (RAM)" -> "用户"
3. 创建或选择现有用户
4. 创建 AccessKey，记录 AccessKey ID 和 AccessKey Secret

#### APP KEY
1. 登录 [阿里云智能语音控制台](https://nls-portal.console.aliyun.com/applist)
2. 创建或选择应用
3. 复制应用的 APP KEY

### 2. 配置步骤
1. 登录系统后，进入"账户设置"页面
2. 滚动到"阿里云智能语音 NLS 配置"卡片
3. 填入三个配置项：
   - AccessKey ID
   - AccessKey Secret
   - APP KEY
4. 点击"保存 NLS 配置"按钮
5. 等待成功提示

### 3. 验证配置
配置保存后，可以在"账户设置"页面重新进入查看，确认配置已正确保存。

## 测试状态

- ✅ 数据库模型已更新
- ✅ API 序列化器已更新
- ✅ 前端表单界面已实现
- ✅ 配置加载功能已实现
- ✅ 配置保存功能已实现
- ✅ Django 服务器正常运行
- ✅ API 端点正常响应 (GET /api/auth/config/ 返回 200)

## 后续使用

这些 NLS 配置将用于：
1. **实时语音识别**: 使用阿里云智能语音 NLS SDK 进行实时 ASR
2. **语音合成**: 可能用于 TTS 功能
3. **语音分析**: 高级语音处理功能

当前系统已实现的 ASR 功能使用 DashScope API（需要 `dashscope_api_key`），而 NLS 配置为未来集成实时语音识别功能预留。

## 相关文档

- [阿里云智能语音 NLS 文档](https://help.aliyun.com/product/30413.html)
- [阿里云 AccessKey 管理](https://help.aliyun.com/document_detail/116401.html)
- [阿里云 DashScope 文档](https://help.aliyun.com/document_detail/2712195.html)

## 技术细节

### 数据库字段
- `aliyun_access_key_id`: VARCHAR(100), nullable
- `aliyun_access_key_secret`: VARCHAR(100), nullable
- `aliyun_app_key`: VARCHAR(100), nullable
- `aliyun_asr_appkey`: VARCHAR(100), nullable (备用字段)

### 前端组件
- 使用 Element Plus UI 库
- 响应式表单 (Vue 3 Composition API)
- 自动加载和保存功能
- 错误处理和用户反馈

### 安全考虑
- AccessKey Secret 使用密码输入框
- 配置通过认证后的 API 传输
- 服务器端存储在数据库中

## 问题排查

### 浏览器 CORS 缓存问题
如果遇到登录失败，可能是浏览器缓存了旧的 CORS 预检响应：

**解决方案**:
1. 清除浏览器缓存
2. 使用无痕模式/隐私模式
3. 强制刷新 (Ctrl+Shift+R / Cmd+Shift+R)
4. 等待一段时间让 CORS 缓存过期

### 配置不生效
1. 确认配置已成功保存（查看成功提示）
2. 刷新页面重新加载配置
3. 检查后端日志是否有错误
4. 使用开发者工具查看网络请求

## 完成状态
✅ **所有功能已完成并测试通过**
