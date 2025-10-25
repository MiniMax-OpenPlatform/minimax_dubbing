# ASR 字幕合并功能

## 功能说明

ASR 识别后的字幕可能过于离散（每个句子很短），现在支持**智能合并短字幕**功能。

## 合并策略

自动合并满足以下条件的相邻字幕：
1. **当前字幕时长** < `min_duration`（默认 2 秒）
2. **与下一个字幕的间隔** < `max_gap`（默认 1 秒）

### 合并效果示例

**合并前**（35个字幕）：
```
1. 00:00:00 → 00:00:01  大家好
2. 00:00:01 → 00:00:02  欢迎来到我的频道
3. 00:00:03 → 00:00:04  今天
4. 00:00:04 → 00:00:06  我们要讲解语音识别
```

**合并后**（15个字幕）：
```
1. 00:00:00 → 00:00:02  大家好，欢迎来到我的频道
2. 00:00:03 → 00:00:06  今天，我们要讲解语音识别
```

## API 参数

### 请求示例

```bash
POST /api/projects/{id}/asr_recognize/
Content-Type: application/json

{
  "merge_short_segments": true,  // 是否启用合并，默认 true
  "min_duration": 2.0,           // 最小字幕时长（秒），默认 2.0
  "max_gap": 1.0                 // 最大间隔时间（秒），默认 1.0
}
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `merge_short_segments` | boolean | `true` | 是否启用字幕合并 |
| `min_duration` | float | `2.0` | 最小字幕时长（秒）。短于此时长的字幕会尝试与下一个合并 |
| `max_gap` | float | `1.0` | 最大间隔时间（秒）。只有间隔小于此值的字幕才会被合并 |

## 使用建议

### 场景 1：对话密集（快速对话）
```json
{
  "merge_short_segments": true,
  "min_duration": 1.5,    // 更短的最小时长
  "max_gap": 0.5          // 更小的间隔
}
```
适用于：访谈、辩论、快节奏对话

### 场景 2：演讲/旁白（正常语速）
```json
{
  "merge_short_segments": true,
  "min_duration": 2.0,    // 默认值（推荐）
  "max_gap": 1.0          // 默认值（推荐）
}
```
适用于：演讲、教学视频、纪录片旁白

### 场景 3：慢速讲解（有停顿）
```json
{
  "merge_short_segments": true,
  "min_duration": 3.0,    // 更长的最小时长
  "max_gap": 1.5          // 更大的间隔
}
```
适用于：教程、讲座、新闻播报

### 场景 4：不合并（保留原始）
```json
{
  "merge_short_segments": false
}
```
适用于：需要精确时间戳的场景

## 合并逻辑

```python
# 伪代码
for each segment:
    duration = segment.end_time - segment.start_time
    gap = next_segment.start_time - segment.end_time

    if duration < min_duration AND gap < max_gap:
        # 合并：保留开始时间，延长到下一个的结束时间
        merged_segment.start_time = segment.start_time
        merged_segment.end_time = next_segment.end_time
        merged_segment.text = segment.text + "，" + next_segment.text
```

## 文本连接规则

- 如果前一个字幕以句号/问号/感叹号结尾 → 用空格连接
  ```
  "你好。" + "欢迎" → "你好。 欢迎"
  ```

- 否则 → 用逗号连接
  ```
  "你好" + "欢迎" → "你好，欢迎"
  ```

## 日志输出

识别过程中会输出合并信息：

```
INFO: 字幕合并完成: 35 → 15 (减少 20 个)
INFO: 成功创建 15 个字幕段落
```

## 前端集成

### 方式 1：使用默认值（最简单）

```typescript
// 直接调用，使用默认合并参数
const response = await api.post(`/projects/${projectId}/asr_recognize/`, {})
```

### 方式 2：自定义参数

```typescript
const response = await api.post(`/projects/${projectId}/asr_recognize/`, {
  merge_short_segments: true,
  min_duration: 2.5,  // 自定义最小时长
  max_gap: 0.8        // 自定义最大间隔
})
```

### 方式 3：添加用户配置界面（建议）

在前端添加配置选项，让用户自己调整：

```vue
<el-form-item label="合并短字幕">
  <el-switch v-model="asrConfig.mergeShortSegments" />
</el-form-item>
<el-form-item label="最小时长（秒）" v-if="asrConfig.mergeShortSegments">
  <el-input-number v-model="asrConfig.minDuration" :min="0.5" :max="5" :step="0.5" />
</el-form-item>
<el-form-item label="最大间隔（秒）" v-if="asrConfig.mergeShortSegments">
  <el-input-number v-model="asrConfig.maxGap" :min="0.1" :max="3" :step="0.1" />
</el-form-item>
```

## 注意事项

1. **合并是不可逆的** - 一旦识别完成并合并，原始的细分字幕会丢失
2. **时间戳准确性** - 合并后的时间戳仍然精确（使用原始的开始和结束时间）
3. **性能影响** - 合并操作在内存中完成，对性能影响极小
4. **建议先测试** - 第一次使用时建议用小文件测试不同参数的效果

## 实现文件

- **后端逻辑**: `services/asr/flash_recognizer.py:313-377`
- **API 端点**: `projects/views.py:1524-1668`
- **合并算法**: `FlashRecognizerService._merge_segments()`

---

**版本**: v1.0
**最后更新**: 2025-10-25
**默认启用**: ✅ 是
