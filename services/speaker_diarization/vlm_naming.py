"""
VLM智能命名模块
使用Qwen VLM为说话人命名
"""
import requests
import json
import cv2
import base64
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VLMSpeakerNaming:
    """VLM说话人命名器"""

    def __init__(self, dashscope_api_key: str):
        """
        初始化VLM命名器

        Args:
            dashscope_api_key: 阿里云DashScope API Key
        """
        self.api_key = dashscope_api_key
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    def prepare_representative_images(
        self,
        clusters: Dict[int, List[Dict]],
        output_dir: str
    ) -> Dict[int, List[str]]:
        """
        为每个说话人准备代表图片（带红框标注）

        Args:
            clusters: {speaker_id: [face_data, ...]}
            output_dir: 输出目录

        Returns:
            {speaker_id: [image_path1, image_path2]}
        """
        os.makedirs(output_dir, exist_ok=True)
        speaker_images = {}

        for speaker_id, faces in clusters.items():
            # 按人脸面积排序
            sorted_faces = sorted(faces, key=lambda x: x['face_area_ratio'], reverse=True)

            # 选择2张代表图片
            selected_faces = []
            if len(sorted_faces) > 0:
                selected_faces.append(sorted_faces[0])  # 最大的

            # 第二张选择时间上距离最远的
            if len(sorted_faces) > 1:
                first_segment = sorted_faces[0]['segment_index']
                max_distance = 0
                second_face = sorted_faces[1]

                for face in sorted_faces[1:]:
                    distance = abs(face['segment_index'] - first_segment)
                    if distance > max_distance:
                        max_distance = distance
                        second_face = face

                selected_faces.append(second_face)

            # 生成标注图片
            image_paths = []
            for idx, face in enumerate(selected_faces):
                frame = face['frame'].copy()
                box = face['box']
                x1, y1, x2, y2 = map(int, box)

                # 画红框
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)

                # 保存
                image_path = os.path.join(output_dir, f"speaker_{speaker_id}_frame_{idx}.jpg")
                cv2.imwrite(image_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                image_paths.append(image_path)

            speaker_images[speaker_id] = image_paths

        return speaker_images

    def build_vlm_prompt(
        self,
        speaker_id: int,
        segments_data: List[Dict],
        speaker_statistics: Dict,
        all_srt_segments: List[Dict]
    ) -> str:
        """
        构建VLM Prompt

        Args:
            speaker_id: 说话人ID
            segments_data: 该说话人出现的片段数据
            speaker_statistics: 说话人统计信息
            all_srt_segments: 所有SRT片段

        Returns:
            prompt文本
        """
        # 该说话人出现的片段编号
        appearing_segments = speaker_statistics['segments']

        # 提取出现时的对话（最多15个）
        dialogues = []
        for seg_idx in appearing_segments[:15]:
            seg = next((s for s in all_srt_segments if s['index'] == seg_idx), None)
            if seg:
                dialogues.append(f"[{seg_idx}] {seg['text']}")

        dialogues_text = '\n'.join(dialogues)

        # 完整对话
        all_dialogues = [f"[{s['index']}] {s['text']}" for s in all_srt_segments[:50]]
        all_dialogues_text = '\n'.join(all_dialogues)

        prompt = f"""请分析以下人脸图片和对话内容，为这个人物命名并提供详细档案。

**图片说明**：
- 提供了2张该人物的图片，红框标注的就是目标人物

**该人物的出现统计**：
- 出现片段数：{speaker_statistics['segment_count']}
- 人脸检测数：{speaker_statistics['face_count']}
- 出现的片段编号：{appearing_segments[:10]}{'...' if len(appearing_segments) > 10 else ''}

**该人物出现时的对话内容**（最多15个片段）：
{dialogues_text}

**完整对话上下文**（前50个片段）：
{all_dialogues_text}

**任务要求**：
1. **命名规则**（重要！）：
   - 如果对话中有"我叫X"、"我是X"等自称，那么X就是该人物的名字
   - 如果多人称呼该人物为"X"，那么X可能是名字
   - 注意区分：对话中"X，你好"表示X是对方，不是说话人自己
   - 如果无法确定名字，可以根据角色特征命名（如"女主角"、"老板"等）

2. **输出JSON格式**：
{{
  "speaker_id": {speaker_id},
  "name": "人物姓名或角色名",
  "role": "角色定位（如主角、配角、路人等）",
  "gender": "性别（男/女/未知）",
  "appearance": {{
    "clothing": "服装描述",
    "facial_features": "面部特征",
    "age_estimate": "年龄估计",
    "distinctive_features": "显著特征"
  }},
  "character_analysis": {{
    "personality": "性格特点",
    "importance": "重要程度（高/中/低）",
    "relationship": "与其他人物的关系",
    "dialogue_characteristics": "说话特点"
  }},
  "key_dialogues": ["关键对话1", "关键对话2"]
}}

只输出JSON，不要其他说明。"""

        return prompt

    def call_qwen_vlm(
        self,
        prompt: str,
        image_paths: List[str]
    ) -> Optional[Dict]:
        """
        调用Qwen VLM API

        Args:
            prompt: 提示词
            image_paths: 图片路径列表

        Returns:
            VLM响应的JSON数据
        """
        logger.info(f"调用Qwen VLM API，图片数量: {len(image_paths)}")

        # 读取图片并转换为base64
        images_content = []
        for img_path in image_paths:
            with open(img_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
                images_content.append(f"data:image/jpeg;base64,{img_base64}")

        # 构建消息
        messages_content = []
        for img_content in images_content:
            messages_content.append({
                "type": "image",
                "image": img_content
            })
        messages_content.append({
            "type": "text",
            "text": prompt
        })

        payload = {
            "model": "qwen-vl-max",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": messages_content
                    }
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            trace_id = response.headers.get('X-Request-Id', 'unknown')

            if response.status_code != 200:
                logger.error(f"VLM API错误: {response.status_code}, {response.text}")
                return None

            result = response.json()
            logger.info(f"VLM调用成功，Trace ID: {trace_id}")

            # 解析响应
            output_content = result.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')

            # content可能是list或string
            if isinstance(output_content, list):
                # 如果是list，合并所有text内容
                output_text = ' '.join([item.get('text', '') if isinstance(item, dict) else str(item) for item in output_content])
            else:
                output_text = output_content

            # 提取JSON
            try:
                # 移除markdown代码块
                if '```json' in output_text:
                    output_text = output_text.split('```json')[1].split('```')[0]
                elif '```' in output_text:
                    output_text = output_text.split('```')[1].split('```')[0]

                speaker_info = json.loads(output_text.strip())
                speaker_info['vlm_trace_id'] = trace_id
                return speaker_info

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 原文本: {output_text[:200]}")
                return None

        except Exception as e:
            logger.error(f"VLM调用异常: {e}")
            return None

    def name_all_speakers(
        self,
        clusters: Dict[int, List[Dict]],
        speaker_statistics: Dict[int, Dict],
        all_srt_segments: List[Dict],
        output_dir: str
    ) -> Dict[int, Dict]:
        """
        为所有说话人命名

        Args:
            clusters: 聚类结果
            speaker_statistics: 说话人统计信息
            all_srt_segments: 所有SRT片段
            output_dir: 输出目录

        Returns:
            {speaker_id: speaker_info}
        """
        logger.info("开始VLM智能命名...")

        # 准备代表图片
        speaker_images = self.prepare_representative_images(clusters, output_dir)

        named_speakers = {}

        for speaker_id in sorted(clusters.keys()):
            logger.info(f"正在为说话人 {speaker_id} 命名...")

            # 构建prompt
            prompt = self.build_vlm_prompt(
                speaker_id,
                clusters[speaker_id],
                speaker_statistics[speaker_id],
                all_srt_segments
            )

            # 调用VLM
            image_paths = speaker_images.get(speaker_id, [])
            if not image_paths:
                logger.warning(f"说话人 {speaker_id} 没有代表图片")
                continue

            speaker_info = self.call_qwen_vlm(prompt, image_paths)

            if speaker_info:
                speaker_info['representative_images'] = image_paths
                speaker_info.update(speaker_statistics[speaker_id])
                named_speakers[speaker_id] = speaker_info
                logger.info(f"  ✓ {speaker_info.get('name', '未知')}")
            else:
                # VLM失败，使用默认命名
                default_info = {
                    'speaker_id': speaker_id,
                    'name': f'说话人{speaker_id}',
                    'role': '未知',
                    'gender': '未知',
                    'appearance': {},
                    'character_analysis': {},
                    'representative_images': image_paths,
                    **speaker_statistics[speaker_id]
                }
                named_speakers[speaker_id] = default_info
                logger.warning(f"  ✗ VLM命名失败，使用默认名称")

        return named_speakers
