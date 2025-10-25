# ASR 语音识别功能实现说明

## 📋 当前实现状态

### ✅ 已完成部分

1. **DashScope ASR 服务模块** (`services/asr/dashscope_asr.py`)
   - 完整的 DashScope ASR 封装
   - 支持URL方式的音频文件识别
   - 自动将识别结果转换为SRT格式
   - 完善的错误处理和日志记录

2. **数据库配置**
   - 用户配置表添加 `dashscope_api_key` 字段
   - 前端用户设置页面支持配置 DashScope API Key

3. **API 端点**
   - `POST /api/projects/{id}/asr_recognize/` - ASR识别端点(已添加)

4. **测试验证**
   - ✅ DashScope ASR API 测试通过
   - ✅ SRT格式生成测试通过
   - ✅ 完整的时间戳解析测试通过

### ⚠️ 限制说明

**DashScope ASR 当前限制:**
- DashScope API 只支持**公网可访问的URL**,不支持本地文件直接识别
- 本地文件需要先上传到OSS等对象存储获取公网URL后才能识别

### 🔧 两种解决方案

#### 方案A: 继续使用 DashScope (推荐用于生产环境)

**优点:**
- 云端识别,不占用服务器资源
- 识别速度快
- 支持多种语言和模型
- 识别准确率高

**需要:**
1. 配置阿里云 OSS
2. 将人声分离后的 vocals.wav 上传到 OSS
3. 使用 OSS 公网 URL 调用 DashScope ASR

**实现步骤:**
```python
# 1. 上传到 OSS
oss_url = upload_to_oss(vocals_path)

# 2. 调用 ASR 识别
from services.asr import DashScopeASRService
asr_service = DashScopeASRService(api_key=user.config.dashscope_api_key)
result = asr_service.transcribe_audio(
    audio_path=oss_url,
    language_hints=['zh', 'en']
)

# 3. 导入 segments
for seg_data in result['segments']:
    Segment.objects.create(
        project=project,
        sequence=seg_data['index'],
        start_time=seg_data['start_time'],
        end_time=seg_data['end_time'],
        original_text=seg_data['text']
    )
```

#### 方案B: 使用 Whisper 本地模型 (参考项目采用)

**优点:**
- 支持本地文件直接识别
- 不需要上传到公网
- 不依赖外部API
- 离线可用

**缺点:**
- 占用服务器CPU/GPU资源
- 识别速度较慢
- 需要下载模型文件(约1-3GB)

**需要:**
```bash
pip install openai-whisper
```

**参考实现:** `/data1/devin/minimax-video-translation/modules/asr_processor.py`

## 📁 文件清单

### 后端文件

1. **ASR服务**
   - `services/asr/dashscope_asr.py` - DashScope ASR 服务类
   - `services/asr/__init__.py` - 模块导出

2. **数据库**
   - `authentication/models.py` - 添加 `dashscope_api_key` 字段
   - `authentication/serializers.py` - 序列化器更新
   - `authentication/migrations/0004_userconfig_dashscope_api_key.py` - 数据库迁移

3. **API视图**
   - `projects/views.py:1524` - `asr_recognize` 端点

4. **依赖**
   - `requirements.txt` - 添加 `dashscope==1.24.*`

### 前端文件

1. **用户设置**
   - `frontend/src/components/UserSettings.vue` - DashScope API Key 配置界面

### 测试文件

1. `test_dashscope_asr.py` - DashScope ASR 基础测试
2. `test_dashscope_asr_detail.py` - ASR 详细输出格式测试
3. `test_asr_service.py` - ASR 服务模块测试

## 🧪 测试结果

### DashScope ASR 输出格式

```json
{
  "transcripts": [
    {
      "sentences": [
        {
          "begin_time": 100,      // 毫秒
          "end_time": 3820,       // 毫秒
          "text": "Hello word, 这里是阿里巴巴语音实验室。",
          "sentence_id": 1,
          "words": [
            {
              "begin_time": 100,
              "end_time": 596,
              "text": "Hello",
              "punctuation": ""
            }
            // ...more words
          ]
        }
      ]
    }
  ]
}
```

### 转换为 SRT 格式

```srt
1
00:00:00,100 --> 00:00:03,819
Hello word, 这里是阿里巴巴语音实验室。
```

## 📝 使用方法

### 1. 配置 DashScope API Key

用户登录后进入"账户设置" -> "阿里云 DashScope ASR 配置"，输入 API Key (格式: `sk-xxx`)

### 2. 人声分离

在项目详情页点击"人声分离"按钮，等待分离完成

### 3. ASR 识别 (待完整实现)

```bash
POST /api/projects/{project_id}/asr_recognize/
Content-Type: application/json

{
  "source_language": "zh"  // 可选
}
```

## 🚀 后续开发计划

1. [ ] 集成阿里云 OSS SDK
2. [ ] 实现 vocals.wav 自动上传到 OSS
3. [ ] 完成 ASR 识别端点的完整实现
4. [ ] 添加前端 UI 调用 ASR 识别
5. [ ] 可选: 添加 Whisper 本地识别支持
6. [ ] 添加 ASR 识别进度展示
7. [ ] 支持分段识别(长音频)

## 💡 建议

**生产环境:**
- 使用 DashScope + OSS 方案
- 配置 OSS 公网访问权限
- 启用 OSS CDN 加速

**开发/测试环境:**
- 可以考虑添加 Whisper 本地识别
- 或手动上传测试文件到临时 OSS

## 📞 API Key 获取

- DashScope API Key: https://dashscope.console.aliyun.com/apiKey
- 阿里云 OSS 控制台: https://oss.console.aliyun.com/

## ⚡ 性能参考

- DashScope ASR (云端): 约 1-3 秒识别 1 分钟音频
- Whisper Base 模型: 约 10-30 秒识别 1 分钟音频(CPU)
- Whisper Large 模型: 更准确,但速度更慢

---

**最后更新:** 2025-10-24
**状态:** ASR 服务模块开发完成,等待 OSS 集成
