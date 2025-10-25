"""
说话人识别主Pipeline
整合人脸检测、聚类、VLM命名、LLM分配的完整流程
"""
import os
import logging
from typing import Dict, Callable, Optional
from .srt_parser import parse_srt_from_segments
from .face_detector import FaceDetector
from .clusterer import FaceClusterer
from .vlm_naming import VLMSpeakerNaming
from .llm_assignment import LLMSpeakerAssignment

logger = logging.getLogger(__name__)


class SpeakerDiarizationPipeline:
    """说话人识别Pipeline"""

    def __init__(
        self,
        video_path: str,
        segments,
        output_dir: str,
        dashscope_api_key: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ):
        """
        初始化Pipeline

        Args:
            video_path: 视频文件路径
            segments: Django Segment QuerySet
            output_dir: 输出目录
            dashscope_api_key: 阿里云DashScope API Key
            progress_callback: 进度回调函数 callback(progress, message)
        """
        self.video_path = video_path
        self.segments = segments
        self.output_dir = output_dir
        self.dashscope_api_key = dashscope_api_key
        self.progress_callback = progress_callback or (lambda p, m: None)

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 初始化组件
        self.face_detector = None
        self.clusterer = None
        self.vlm_naming = None
        self.llm_assignment = None

    def update_progress(self, progress: int, message: str):
        """更新进度"""
        logger.info(f"[{progress}%] {message}")
        self.progress_callback(progress, message)

    def process(self) -> Dict:
        """
        执行完整的说话人识别流程

        Returns:
            识别结果字典
        """
        logger.info("=" * 60)
        logger.info("开始说话人识别Pipeline")
        logger.info("=" * 60)

        result = {
            'success': False,
            'error': None,
            'num_speakers': 0,
            'speakers': {},
            'clustering_params': {},
            'filter_statistics': {},
            'vlm_trace_id': None,
            'llm_trace_id': None
        }

        try:
            # Step 1: 解析SRT (10%)
            self.update_progress(10, "解析字幕文件...")
            srt_segments = parse_srt_from_segments(self.segments)
            logger.info(f"解析到 {len(srt_segments)} 个字幕片段")
            result['total_segments'] = len(srt_segments)

            if len(srt_segments) == 0:
                raise ValueError("没有可用的字幕片段")

            # Step 2: 初始化人脸检测器 (15%)
            self.update_progress(15, "初始化人脸检测模型...")
            self.face_detector = FaceDetector(device='cpu')

            # Step 3: 抽取关键帧 (20%)
            self.update_progress(20, "抽取视频关键帧...")
            segment_frames = self.face_detector.extract_frames_for_face_detection(
                self.video_path,
                srt_segments,
                max_frames_per_segment=3  # CPU模式使用3帧
            )
            logger.info(f"抽取了 {len(segment_frames)} 个片段的帧")

            # Step 4: 人脸检测+质量过滤 (35%)
            self.update_progress(35, "检测人脸并过滤...")
            faces, filter_stats = self.face_detector.detect_faces_with_quality_filter(
                segment_frames,
                confidence_threshold=0.95,
                size_threshold=0.005,
                side_face_ratio=2.5,
                sharpness_threshold=100.0
            )
            logger.info(f"检测到 {len(faces)} 张高质量人脸")
            result['total_faces'] = filter_stats['total_detected']
            result['valid_faces'] = filter_stats['valid_faces']
            result['filter_statistics'] = filter_stats

            if len(faces) == 0:
                raise ValueError("未检测到高质量人脸，请检查视频质量或调整过滤参数")

            # Step 5: 提取特征向量 (50%)
            self.update_progress(50, f"提取 {len(faces)} 张人脸的特征向量...")
            embeddings, valid_faces = self.face_detector.extract_face_embeddings(faces)
            logger.info(f"特征提取完成，形状: {embeddings.shape}")

            # Step 6: DBSCAN聚类 (60%)
            self.update_progress(60, "DBSCAN聚类识别说话人...")
            self.clusterer = FaceClusterer(eps=0.28, min_samples=5)
            clusters, clustering_info = self.clusterer.cluster_faces(embeddings, valid_faces)

            num_speakers = clustering_info['num_speakers']
            logger.info(f"识别出 {num_speakers} 个说话人")
            result['num_speakers'] = num_speakers
            result['clustering_params'] = {
                'eps': clustering_info['eps'],
                'min_samples': clustering_info['min_samples'],
                'metric': 'cosine'
            }

            if num_speakers == 0:
                raise ValueError("聚类未识别出说话人，请调整聚类参数")

            # Step 7: 统计说话人信息 (65%)
            self.update_progress(65, "统计说话人信息...")
            speaker_statistics = self.clusterer.get_speaker_statistics(clusters)

            # Step 8: VLM智能命名 (75%)
            self.update_progress(75, "VLM智能命名说话人...")
            self.vlm_naming = VLMSpeakerNaming(self.dashscope_api_key)

            faces_dir = os.path.join(self.output_dir, 'faces')
            named_speakers = self.vlm_naming.name_all_speakers(
                clusters,
                speaker_statistics,
                srt_segments,
                faces_dir
            )

            # 提取VLM trace_id
            vlm_trace_ids = [s.get('vlm_trace_id') for s in named_speakers.values() if s.get('vlm_trace_id')]
            result['vlm_trace_id'] = vlm_trace_ids[0] if vlm_trace_ids else None

            # Step 9: LLM说话人分配 (85%)
            self.update_progress(85, "LLM分配说话人到字幕...")
            self.llm_assignment = LLMSpeakerAssignment(self.dashscope_api_key)

            assignment_result = self.llm_assignment.assign_speakers(
                named_speakers,
                srt_segments,
                clusters
            )

            if assignment_result:
                result['llm_trace_id'] = assignment_result.get('llm_trace_id')
                result['topic_summary'] = assignment_result.get('topic_summary', {})
                result['segment_assignments'] = assignment_result.get('assignments', {})
            else:
                logger.warning("LLM分配失败，将仅使用VLM命名结果")

            # Step 10: 整合结果 (95%)
            self.update_progress(95, "整合识别结果...")

            # 转换为最终格式
            speakers_result = {}
            for speaker_id, info in named_speakers.items():
                # 相对路径转换（去掉output_dir前缀）
                representative_images = info.get('representative_images', [])
                relative_images = [
                    os.path.relpath(img, self.output_dir) for img in representative_images
                ]

                speakers_result[speaker_id] = {
                    'speaker_id': speaker_id,
                    'name': info.get('name', f'说话人{speaker_id}'),
                    'role': info.get('role', ''),
                    'gender': info.get('gender', ''),
                    'face_count': info.get('face_count', 0),
                    'segment_count': info.get('segment_count', 0),
                    'segments': info.get('segments', []),
                    'appearance': info.get('appearance', {}),
                    'character_analysis': info.get('character_analysis', {}),
                    'representative_images': relative_images,
                    'avg_confidence': info.get('avg_confidence', 0.0)
                }

            result['speakers'] = speakers_result
            result['success'] = True

            # Step 11: 完成 (100%)
            self.update_progress(100, f"识别完成！检测到 {num_speakers} 个说话人")

            logger.info("=" * 60)
            logger.info("说话人识别Pipeline完成")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Pipeline执行失败: {e}", exc_info=True)
            result['error'] = str(e)
            self.update_progress(0, f"识别失败: {str(e)}")
            return result


def process_speaker_diarization(
    video_path: str,
    segments,
    output_dir: str,
    dashscope_api_key: str,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Dict:
    """
    便捷函数：执行说话人识别

    Args:
        video_path: 视频文件路径
        segments: Django Segment QuerySet
        output_dir: 输出目录
        dashscope_api_key: 阿里云DashScope API Key
        progress_callback: 进度回调函数

    Returns:
        识别结果字典
    """
    pipeline = SpeakerDiarizationPipeline(
        video_path=video_path,
        segments=segments,
        output_dir=output_dir,
        dashscope_api_key=dashscope_api_key,
        progress_callback=progress_callback
    )

    return pipeline.process()
