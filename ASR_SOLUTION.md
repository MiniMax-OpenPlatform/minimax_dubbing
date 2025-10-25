# ASR 识别功能 - 最终解决方案

## 🎯 核心问题

DashScope 提供两种 ASR 接口：

| 接口 | 本地文件 | 时间戳 | 用途 |
|------|---------|--------|------|
| `Recognition.call()` | ✅ 支持 | ❌ 无 | 实时识别,只返回文本 |
| `Transcription.async_call()` | ❌ 仅URL | ✅ 有 | 录音文件识别,返回详细时间戳 |

**我们需要时间戳来生成 SRT**, 因此必须使用 `Transcription.async_call()`，但它要求文件必须是**可公网访问的 URL**。

## ✅ 推荐解决方案：使用 Whisper 本地模型

参考项目 `/data1/devin/minimax-video-translation` 使用的是 **Whisper** 本地模型：

### 优点
- ✅ 支持本地文件直接识别
- ✅ 提供详细的时间戳信息
- ✅ 不需要公网访问
- ✅ 离线可用
- ✅ 免费
- ✅ 支持多语言

### 缺点
- ⚠️ 占用服务器 CPU/GPU 资源
- ⚠️ 识别速度较慢 (CPU: 约 30秒/分钟音频)
- ⚠️ 需要下载模型文件 (base: ~140MB, large: ~3GB)

### 安装

```bash
pip install openai-whisper
```

### 实现代码

```python
import whisper

class WhisperASRService:
    def __init__(self, model_size='base'):
        """
        初始化 Whisper 模型

        Args:
            model_size: 模型大小 ('tiny', 'base', 'small', 'medium', 'large')
                       - tiny: 最快，准确率最低
                       - base: 平衡 (推荐)
                       - large: 最准，最慢
        """
        self.model = whisper.load_model(model_size)

    def transcribe_audio(self, audio_path, language='zh'):
        """
        识别音频文件

        Returns:
            {
                'segments': [
                    {
                        'start': 0.0,
                        'end': 3.5,
                        'text': '你好世界'
                    },
                    ...
                ]
            }
        """
        result = self.model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,  # 启用词级时间戳
            verbose=False
        )

        segments = []
        for seg in result['segments']:
            segments.append({
                'index': len(segments) + 1,
                'start_time': seg['start'],
                'end_time': seg['end'],
                'text': seg['text'].strip(),
                'duration': seg['end'] - seg['start']
            })

        return {
            'success': True,
            'segments': segments,
            'total_duration': result.get('duration', 0)
        }
```

### 转换为 SRT

```python
from services.parsers.srt_parser import SRTParser

# 识别
asr_service = WhisperASRService(model_size='base')
result = asr_service.transcribe_audio('/path/to/vocals.wav', language='zh')

# 转换为 SRT
srt_content = SRTParser.export_to_srt(
    result['segments'],
    output_path='/path/to/output.srt'
)
```

## 📊 性能对比

| 方案 | 1分钟音频识别时间 | 准确率 | 成本 |
|------|------------------|--------|------|
| Whisper tiny (CPU) | ~10s | ⭐⭐⭐ | 免费 |
| Whisper base (CPU) | ~30s | ⭐⭐⭐⭐ | 免费 |
| Whisper large (CPU) | ~120s | ⭐⭐⭐⭐⭐ | 免费 |
| Whisper base (GPU) | ~3s | ⭐⭐⭐⭐ | 免费 |
| DashScope (云端) | ~2s | ⭐⭐⭐⭐⭐ | 付费 |

## 🚀 快速实现步骤

### 1. 安装 Whisper

```bash
pip install openai-whisper
echo "openai-whisper==20231117" >> requirements.txt
```

### 2. 创建 Whisper ASR 服务

创建 `services/asr/whisper_asr.py` (参考上面的代码)

### 3. 更新 API 端点

修改 `projects/views.py` 的 `asr_recognize` 方法：

```python
from services.asr.whisper_asr import WhisperASRService

@action(detail=True, methods=['post'])
def asr_recognize(self, request, pk=None):
    project = self.get_object()

    # 获取人声文件路径
    vocals_path = project.separated_vocals_url.replace('/media/', 'media/')

    # 使用 Whisper 识别
    asr_service = WhisperASRService(model_size='base')
    result = asr_service.transcribe_audio(
        vocals_path,
        language=project.source_language or 'zh'
    )

    # 导入 segments
    with transaction.atomic():
        project.segments.all().delete()  # 清空现有

        for seg_data in result['segments']:
            Segment.objects.create(
                project=project,
                sequence=seg_data['index'],
                start_time=seg_data['start_time'],
                end_time=seg_data['end_time'],
                original_text=seg_data['text']
            )

    project.status = 'ready'
    project.total_segments = len(result['segments'])
    project.save()

    return Response({
        'success': True,
        'segments_count': len(result['segments'])
    })
```

### 4. 前端添加 ASR 按钮

在项目详情页添加"ASR识别"按钮，调用 API：

```javascript
const handleASR = async () => {
  try {
    const response = await api.post(`/projects/${projectId}/asr_recognize/`)
    if (response.data.success) {
      ElMessage.success(`识别成功,导入${response.data.segments_count}个段落`)
      // 刷新项目数据
      await loadProject()
    }
  } catch (error) {
    ElMessage.error('ASR识别失败')
  }
}
```

## 🔄 完整工作流程

1. 用户上传原始视频/音频
2. **人声分离** → 生成 `vocals.wav`
3. **点击 ASR 识别按钮**
4. 后端使用 Whisper 识别 `vocals.wav`
5. 自动创建带时间戳的 Segment 记录
6. 用户编辑/翻译/TTS

## 💡 优化建议

### 加速识别

1. **使用 GPU** (如果服务器有 NVIDIA GPU):
```bash
pip install openai-whisper
# Whisper 会自动使用 CUDA 加速
```

2. **使用更小的模型**:
```python
# tiny 模型最快，适合快速预览
asr_service = WhisperASRService(model_size='tiny')
```

3. **异步处理**:
```python
# 使用 Celery 在后台处理长音频
@shared_task
def async_asr_recognize(project_id):
    # ASR 识别逻辑
    pass
```

### 模型选择建议

- **开发/测试**: `tiny` 或 `base`
- **生产环境 (CPU)**: `base`
- **生产环境 (GPU)**: `small` 或 `medium`
- **高质量需求**: `large` (需要 GPU)

## 📦 依赖

```txt
# requirements.txt
openai-whisper==20231117
```

## 🎬 示例输出

**Whisper 识别结果:**
```json
{
  "segments": [
    {
      "index": 1,
      "start_time": 0.0,
      "end_time": 3.5,
      "text": "大家好，欢迎来到我的频道",
      "duration": 3.5
    },
    {
      "index": 2,
      "start_time": 3.5,
      "end_time": 7.2,
      "text": "今天我们要讲解的是语音识别技术",
      "duration": 3.7
    }
  ]
}
```

**转换为 SRT:**
```srt
1
00:00:00,000 --> 00:00:03,500
大家好，欢迎来到我的频道

2
00:00:03,500 --> 00:00:07,200
今天我们要讲解的是语音识别技术
```

---

**最终建议:** 使用 Whisper 本地模型，简单、免费、可靠！
