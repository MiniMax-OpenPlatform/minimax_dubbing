"""
LLM说话人分配模块
使用Qwen LLM为每个字幕片段分配说话人
"""
import requests
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LLMSpeakerAssignment:
    """LLM说话人分配器"""

    def __init__(self, dashscope_api_key: str):
        """
        初始化LLM分配器

        Args:
            dashscope_api_key: 阿里云DashScope API Key
        """
        self.api_key = dashscope_api_key
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def build_assignment_prompt(
        self,
        named_speakers: Dict[int, Dict],
        all_srt_segments: List[Dict],
        clusters: Dict[int, List[Dict]]
    ) -> str:
        """
        构建LLM分配Prompt

        Args:
            named_speakers: VLM命名的说话人信息
            all_srt_segments: 所有SRT片段
            clusters: 聚类结果（用于获取出现片段）

        Returns:
            prompt文本
        """
        # 构建说话人信息
        speakers_info = []
        for speaker_id, info in sorted(named_speakers.items()):
            speakers_info.append(f"""说话人 {speaker_id}:
  - 姓名: {info.get('name', '未知')}
  - 角色: {info.get('role', '未知')}
  - 性别: {info.get('gender', '未知')}
  - 出现片段: {info.get('segments', [])[:20]}{'...' if len(info.get('segments', [])) > 20 else ''}
  - 人脸数: {info.get('face_count', 0)}""")

        speakers_text = '\n\n'.join(speakers_info)

        # 构建对话列表（包含画面人物信息）
        dialogue_list = []
        for seg in all_srt_segments[:100]:  # 限制100个片段
            # 找出在该片段出现的说话人
            segment_idx = seg['index']
            appeared_speakers = []

            for speaker_id, faces in clusters.items():
                if any(f['segment_index'] == segment_idx for f in faces):
                    speaker_name = named_speakers.get(speaker_id, {}).get('name', f'说话人{speaker_id}')
                    appeared_speakers.append(speaker_name)

            appeared_text = '、'.join(appeared_speakers) if appeared_speakers else '无'

            dialogue_list.append(f"[{segment_idx}] 画面: {appeared_text} | 字幕: {seg['text']}")

        dialogue_text = '\n'.join(dialogue_list)

        prompt = f"""你是一个专业的说话人分配专家。请根据人脸识别结果和对话内容，为每个字幕片段分配说话人。

**已识别的说话人信息**：
{speakers_text}

**对话内容**（画面 = 该片段检测到的人脸）：
{dialogue_text}

**分配规则**：
1. **话题约束**（重要！）：在一个连续话题中，只有画面出现过的人才能说话
   - 如果片段画面只有"张三"，那么该片段的说话人只能是"张三"
   - 如果片段画面有"张三、李四"，需要根据对话逻辑判断

2. **对话逻辑**：
   - 问答对通常是不同人
   - 反问、质疑通常是对话转换
   - 连续陈述通常是同一人

3. **完整性**：必须为所有片段分配说话人（包括画面无人脸的片段）

**输出JSON格式**：
{{
  "topic_summary": {{
    "total_segments": {len(all_srt_segments)},
    "topics": [
      {{
        "topic_id": 1,
        "description": "话题描述",
        "segments": [1, 2, 3],
        "faces_appeared": ["张三", "李四"],
        "key_insight": "在这个话题中只有张三和李四出现，说话人只能从这两位中选"
      }}
    ]
  }},
  "assignments": [
    {{
      "segment_id": 1,
      "analysis": "分析过程",
      "is_face_speaker": true,
      "speaker_name": "张三",
      "speaker_id": 1,
      "confidence": "high"
    }}
  ]
}}

只输出JSON，不要其他说明。"""

        return prompt

    def call_qwen_llm(self, prompt: str) -> Optional[Dict]:
        """
        调用Qwen LLM API（流式）

        Args:
            prompt: 提示词

        Returns:
            LLM响应的JSON数据
        """
        logger.info("调用Qwen LLM API（流式）...")

        payload = {
            "model": "qwen-max",
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的说话人分配专家，根据视觉线索和对话逻辑分配说话人。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "result_format": "message",
                "incremental_output": True
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable"
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )

            trace_id = response.headers.get('X-Request-Id', 'unknown')
            logger.info(f"LLM调用开始，Trace ID: {trace_id}")

            if response.status_code != 200:
                logger.error(f"LLM API错误: {response.status_code}, {response.text}")
                return None

            # 收集流式响应
            full_content = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data:'):
                        json_str = line_text[5:].strip()
                        if json_str:
                            try:
                                data = json.loads(json_str)
                                content = data.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
                                full_content += content
                            except json.JSONDecodeError:
                                continue

            logger.info(f"LLM响应完成，长度: {len(full_content)}")

            # 解析JSON
            try:
                # 移除markdown代码块
                if '```json' in full_content:
                    full_content = full_content.split('```json')[1].split('```')[0]
                elif '```' in full_content:
                    full_content = full_content.split('```')[1].split('```')[0]

                result = json.loads(full_content.strip())
                result['llm_trace_id'] = trace_id
                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 原文本前200字符: {full_content[:200]}")
                return None

        except Exception as e:
            logger.error(f"LLM调用异常: {e}")
            return None

    def apply_assignments_to_segments(
        self,
        assignments: List[Dict],
        named_speakers: Dict[int, Dict]
    ) -> Dict[int, Dict]:
        """
        应用LLM分配结果到片段

        Args:
            assignments: LLM返回的分配列表
            named_speakers: 命名的说话人信息

        Returns:
            {segment_id: assignment_info}
        """
        segment_assignments = {}

        for assignment in assignments:
            segment_id = assignment.get('segment_id')
            speaker_name = assignment.get('speaker_name')
            speaker_id = assignment.get('speaker_id')

            # 如果没有speaker_id，尝试通过名字查找
            if not speaker_id and speaker_name:
                for sid, info in named_speakers.items():
                    if info.get('name') == speaker_name:
                        speaker_id = sid
                        break

            segment_assignments[segment_id] = {
                'speaker_id': speaker_id,
                'speaker_name': speaker_name,
                'speaker_confidence': assignment.get('confidence', 'medium'),
                'llm_analysis': assignment.get('analysis', ''),
                'is_face_speaker': assignment.get('is_face_speaker', False)
            }

        return segment_assignments

    def assign_speakers(
        self,
        named_speakers: Dict[int, Dict],
        all_srt_segments: List[Dict],
        clusters: Dict[int, List[Dict]]
    ) -> Optional[Dict]:
        """
        执行说话人分配

        Args:
            named_speakers: VLM命名的说话人信息
            all_srt_segments: 所有SRT片段
            clusters: 聚类结果

        Returns:
            分配结果字典
        """
        logger.info("开始LLM说话人分配...")

        # 构建prompt
        prompt = self.build_assignment_prompt(named_speakers, all_srt_segments, clusters)

        # 调用LLM
        result = self.call_qwen_llm(prompt)

        if not result:
            logger.error("LLM分配失败")
            return None

        # 解析assignments
        assignments = result.get('assignments', [])
        if not assignments:
            logger.warning("LLM未返回分配结果")
            return None

        # 应用到segments
        segment_assignments = self.apply_assignments_to_segments(assignments, named_speakers)

        logger.info(f"LLM分配完成，共 {len(segment_assignments)} 个片段")

        return {
            'topic_summary': result.get('topic_summary', {}),
            'assignments': segment_assignments,
            'llm_trace_id': result.get('llm_trace_id', 'unknown')
        }
