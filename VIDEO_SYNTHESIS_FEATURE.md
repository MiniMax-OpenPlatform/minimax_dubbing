# 视频合成功能

## 功能说明

将翻译音频与背景音混合，替换原始视频的音轨，生成完整的翻译视频。

## 工作流程

```
原始视频 + (翻译音频 + 背景音) → 最终翻译视频
```

### 详细步骤

1. **音频混合**
   - 翻译音频（拼接后的完整TTS音频）
   - 背景音（人声分离后的背景音）
   - 混合为一个完整音轨

2. **视频合成**
   - 去除原始视频的音轨
   - 添加混合后的音频
   - 生成最终翻译视频

## 前置条件

在使用"合成视频"功能前，需要完成以下步骤：

| 步骤 | 操作 | 说明 |
|-----|------|------|
| 1 | 上传视频 | 上传原始视频文件 |
| 2 | 人声分离 | 分离出人声和背景音 |
| 3 | ASR识别（可选） | 自动识别字幕 |
| 4 | 翻译 | 翻译字幕文本 |
| 5 | 批量TTS | 生成翻译语音 |
| 6 | 拼接音频 | 将所有TTS音频拼接为完整音频 |
| 7 | **合成视频** | ⭐ 当前功能 |

## 使用方法

### 界面操作

**位置**: 项目详情页 → 工具栏 → **合成视频** 按钮（绿色）

**步骤**:
1. 点击"合成视频"按钮
2. 确认对话框，点击"开始合成"
3. 等待合成完成（约1-3分钟）
4. 下载提示，点击"下载"获取视频

### API 调用

```bash
POST /api/projects/{id}/synthesize_video/
Content-Type: application/json

{
  "translated_volume": 1.0,    // 翻译音频音量（0.0-1.0）
  "background_volume": 0.3     // 背景音音量（0.0-1.0）
}
```

**响应**:
```json
{
  "success": true,
  "message": "视频合成成功",
  "mixed_audio_url": "http://.../audio/mixed/project_6_mixed_abc123.mp3",
  "final_video_url": "http://.../videos/final/project_6_final_abc123.mp4"
}
```

## 参数配置

### 音量参数

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `translated_volume` | float | 1.0 | 0.0-1.0 | 翻译音频音量 |
| `background_volume` | float | 0.3 | 0.0-1.0 | 背景音音量 |

### 推荐配置

**场景 1: 清晰对话（推荐）**
```json
{
  "translated_volume": 1.0,
  "background_volume": 0.3
}
```
适用于：访谈、教学视频、讲座

**场景 2: 强调音乐/音效**
```json
{
  "translated_volume": 1.0,
  "background_volume": 0.5
}
```
适用于：音乐视频、游戏视频

**场景 3: 纯翻译（无背景）**
```json
{
  "translated_volume": 1.0,
  "background_volume": 0.0
}
```
适用于：对话视频、无背景音的内容

**场景 4: 平衡混合**
```json
{
  "translated_volume": 0.8,
  "background_volume": 0.5
}
```
适用于：纪录片、综艺节目

## 技术实现

### 后端架构

**文件结构**:
```
services/
├── audio_processor.py          # 音频处理服务
│   └── mix_audio_tracks()      # 音频混合
└── video_processor.py          # 视频处理服务（新增）
    └── replace_audio()         # 替换视频音轨
```

**数据库字段**:
```python
# projects/models.py

class Project(models.Model):
    # ... 现有字段
    mixed_audio_path = FileField()      # 混合音频路径
    final_video_path = FileField()      # 最终视频路径
```

### 音频混合算法

```python
# services/audio_processor.py

def mix_audio_tracks(
    translated_audio_path: str,    # 翻译音频
    background_audio_path: str,    # 背景音
    output_path: str,              # 输出路径
    translated_volume: float = 1.0,
    background_volume: float = 0.3
):
    # 1. 加载音频
    translated = AudioSegment.from_file(translated_audio_path)
    background = AudioSegment.from_file(background_audio_path)

    # 2. 调整音量
    translated = translated + (20 * (translated_volume - 1))  # dB
    background = background + (20 * (background_volume - 1))  # dB

    # 3. 对齐时长
    if len(translated) > len(background):
        background += AudioSegment.silent(len(translated) - len(background))
    else:
        background = background[:len(translated)]

    # 4. 混合
    mixed = translated.overlay(background)

    # 5. 导出
    mixed.export(output_path, format="mp3", bitrate="192k")
```

### 视频合成（ffmpeg）

```bash
ffmpeg \
  -i original_video.mp4 \      # 原始视频
  -i mixed_audio.mp3 \         # 混合音频
  -map 0:v \                   # 使用视频流
  -map 1:a \                   # 使用音频流
  -c:v copy \                  # 视频直接复制（不重新编码）
  -c:a aac \                   # 音频编码为 AAC
  -b:a 192k \                  # 音频比特率
  -shortest \                  # 以较短的流为准
  final_video.mp4
```

**优点**:
- 视频不重新编码，速度快
- 保持原视频质量
- 音频高质量AAC编码

## 文件输出

### 生成文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 混合音频 | `media/audio/mixed/project_{id}_mixed_{trace_id}.mp3` | 翻译音频+背景音 |
| 最终视频 | `media/videos/final/project_{id}_final_{trace_id}.mp4` | 完整翻译视频 |

### 文件命名规则

```
project_{项目ID}_{类型}_{追踪ID}.{扩展名}
```

示例:
- `project_6_mixed_abc123.mp3`
- `project_6_final_abc123.mp4`

## 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 音频混合时间 | 5-15秒 | 取决于音频时长 |
| 视频合成时间 | 30-180秒 | 取决于视频时长和大小 |
| 总处理时间 | 1-3分钟 | 包含文件I/O |
| 输出视频质量 | 原视频质量 | 视频流直接复制 |
| 输出音频质量 | 192kbps AAC | 高质量音频 |

### 示例时间（5分钟视频）

```
音频混合: 10秒
视频合成: 60秒
文件保存: 5秒
--------
总计: 75秒
```

## 依赖项

### Python 库

```
pydub==0.25.*          # 音频处理
ffmpeg-python          # ffmpeg Python绑定（可选）
```

### 系统依赖

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# 验证安装
ffmpeg -version
```

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方法 |
|------|------|---------|
| "请先完成批量TTS和拼接音频" | 缺少翻译音频 | 先完成批量TTS和拼接音频 |
| "请先完成人声分离" | 缺少背景音 | 先进行人声分离 |
| "请先上传视频文件" | 缺少原始视频 | 上传视频文件 |
| "ffmpeg 未安装或不可用" | ffmpeg 未安装 | 安装 ffmpeg |
| "音频混合失败" | 音频文件损坏 | 检查音频文件 |
| "视频合成超时" | 视频过大 | 增加超时时间或压缩视频 |

### 日志查看

```bash
# 查看合成日志
tail -f logs/django.log | grep "视频合成"

# 示例输出
INFO: [abc123] 开始视频合成: test222 (ID: 6)
INFO: [abc123] 音量参数: 翻译=1.0, 背景=0.3
INFO: [abc123] 步骤 1/2: 混合音频轨道
INFO: [abc123] 音频混合完成
INFO: [abc123] 步骤 2/2: 合成最终视频
INFO: [abc123] 视频合成成功
```

## 前端界面

### 按钮状态

```vue
<el-button
  :icon="Film"
  type="success"
  @click="handleSynthesizeVideo"
  :loading="batchLoading"
>
  合成视频
</el-button>
```

### 确认对话框

```
标题: 合成视频
内容: 将翻译音频与背景音混合，并替换原始视频的音轨，
      生成最终翻译视频。此过程可能需要几分钟，是否继续？
按钮: [开始合成] [取消]
```

### 下载提示

```
标题: 下载视频
内容: 视频合成成功！是否现在下载？
按钮: [下载] [稍后]
```

## 完整工作流示例

### 1. 创建项目
```
上传视频: demo.mp4 (5分钟)
```

### 2. 人声分离
```
分离人声: vocals.wav
分离背景: background.wav
```

### 3. 字幕处理
```
ASR识别: 35个字幕段落
翻译: 中文 → 英文
```

### 4. 语音生成
```
批量TTS: 35个音频段落
拼接音频: translated_full.mp3
```

### 5. 视频合成 ⭐
```
混合音频: translated_full.mp3 + background.wav
        → mixed.mp3

替换音轨: demo.mp4 (原视频) + mixed.mp3
        → final.mp4 (翻译视频)
```

### 6. 下载
```
下载: final.mp4
```

## 最佳实践

1. **检查音量平衡**
   - 先用默认参数测试
   - 根据效果调整音量比例

2. **视频质量**
   - 原视频保持高质量
   - 避免多次转码

3. **文件管理**
   - 定期清理临时文件
   - 备份重要视频

4. **性能优化**
   - 视频不宜过大（建议<1GB）
   - 服务器保证足够磁盘空间

5. **错误恢复**
   - 合成失败可重试
   - 检查日志定位问题

## API 端点列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects/{id}/synthesize_video/` | POST | 合成视频 |
| `/api/projects/{id}/concatenate_audio/` | POST | 拼接音频 |
| `/api/projects/{id}/separate_vocals/` | POST | 人声分离 |

---

**版本**: v1.0
**最后更新**: 2025-10-25
**状态**: ✅ 可用
**依赖**: ffmpeg, pydub
