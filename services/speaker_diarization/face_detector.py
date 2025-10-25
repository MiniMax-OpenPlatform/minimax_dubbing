"""
人脸检测模块
使用MTCNN进行人脸检测，支持CPU模式，包含多维度质量过滤
"""
import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FaceDetector:
    """人脸检测器（CPU优化版）"""

    def __init__(self, device='cpu'):
        """
        初始化人脸检测器

        Args:
            device: 'cpu' or 'cuda'
        """
        self.device = torch.device(device)
        logger.info(f"初始化人脸检测器，使用设备: {self.device}")

        # 初始化MTCNN（人脸检测）
        self.mtcnn = MTCNN(
            image_size=160,
            margin=0,
            min_face_size=40,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=False,
            device=self.device,
            keep_all=True
        )

        # 初始化FaceNet（特征提取）
        self.facenet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        logger.info("模型加载完成")

    def extract_frames_for_face_detection(
        self,
        video_path: str,
        segments: List[Dict],
        max_frames_per_segment: int = 3
    ) -> List[Dict]:
        """
        从视频中抽取关键帧用于人脸检测

        Args:
            video_path: 视频文件路径
            segments: 字幕片段列表
            max_frames_per_segment: 每个片段抽取的最大帧数（CPU模式建议3帧）

        Returns:
            包含帧数据的字典列表
        """
        logger.info(f"开始抽取视频关键帧: {video_path}")
        logger.info(f"共 {len(segments)} 个片段，每段抽取 {max_frames_per_segment} 帧")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"视频信息: FPS={fps}, 总帧数={total_frames}")

        segment_frames = []

        for i, segment in enumerate(segments):
            start_time = segment['start_time']
            end_time = segment['end_time']
            duration = end_time - start_time

            # 计算要抽取的帧时间点（均匀分布）
            num_frames = max_frames_per_segment
            time_points = []

            if num_frames == 1:
                # 只取中点
                time_points = [(start_time + end_time) / 2]
            else:
                # 等分时间段
                interval = duration / (num_frames + 1)
                time_points = [start_time + interval * (j + 1) for j in range(num_frames)]

            frames = []
            for time_point in time_points:
                frame_number = int(time_point * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()

                if ret:
                    frames.append({
                        'time': time_point,
                        'frame': frame
                    })

            if frames:
                segment_frames.append({
                    'segment_index': segment['index'],
                    'frames': frames
                })

            if (i + 1) % 50 == 0:
                logger.info(f"已处理 {i + 1}/{len(segments)} 个片段")

        cap.release()
        logger.info(f"帧抽取完成，共 {len(segment_frames)} 个片段")
        return segment_frames

    def detect_faces_with_quality_filter(
        self,
        segment_frames: List[Dict],
        confidence_threshold: float = 0.95,
        size_threshold: float = 0.005,
        side_face_ratio: float = 2.5,
        sharpness_threshold: float = 100.0
    ) -> List[Dict]:
        """
        检测人脸并进行多维度质量过滤

        Args:
            segment_frames: 包含帧数据的片段列表
            confidence_threshold: 置信度阈值
            size_threshold: 人脸尺寸阈值（占画幅比例）
            side_face_ratio: 侧脸过滤比率
            sharpness_threshold: 清晰度阈值（Laplacian方差）

        Returns:
            高质量人脸列表
        """
        logger.info("开始人脸检测和质量过滤...")

        all_faces = []
        filter_stats = {
            'total_detected': 0,
            'low_confidence': 0,
            'too_small': 0,
            'side_face': 0,
            'blurry': 0,
            'valid_faces': 0
        }

        for seg_data in segment_frames:
            segment_index = seg_data['segment_index']

            for frame_data in seg_data['frames']:
                frame = frame_data['frame']
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = frame.shape[:2]
                frame_area = h * w

                # MTCNN检测
                boxes, probs, landmarks = self.mtcnn.detect(frame_rgb, landmarks=True)

                if boxes is None:
                    continue

                filter_stats['total_detected'] += len(boxes)

                for box, prob, landmark in zip(boxes, probs, landmarks):
                    # 1. 置信度过滤
                    if prob < confidence_threshold:
                        filter_stats['low_confidence'] += 1
                        continue

                    # 2. 人脸尺寸过滤
                    x1, y1, x2, y2 = box
                    face_area = (x2 - x1) * (y2 - y1)
                    face_area_ratio = face_area / frame_area

                    if face_area_ratio < size_threshold:
                        filter_stats['too_small'] += 1
                        continue

                    # 3. 侧脸过滤（基于landmarks）
                    if landmark is not None:
                        left_eye, right_eye, nose = landmark[0], landmark[1], landmark[2]
                        eye_distance = np.linalg.norm(left_eye - right_eye)
                        nose_to_left = np.linalg.norm(nose - left_eye)
                        nose_to_right = np.linalg.norm(nose - right_eye)

                        ratio = max(nose_to_left, nose_to_right) / (min(nose_to_left, nose_to_right) + 1e-6)

                        if ratio > side_face_ratio:
                            filter_stats['side_face'] += 1
                            continue

                    # 4. 清晰度过滤（Laplacian）
                    x1, y1, x2, y2 = map(int, [max(0, x1), max(0, y1), min(w, x2), min(h, y2)])
                    face_crop = frame[y1:y2, x1:x2]

                    if face_crop.size == 0:
                        continue

                    gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                    laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()

                    if laplacian_var < sharpness_threshold:
                        filter_stats['blurry'] += 1
                        continue

                    # 通过所有过滤条件
                    filter_stats['valid_faces'] += 1

                    all_faces.append({
                        'segment_index': segment_index,
                        'frame': frame_rgb,  # 存储完整画面
                        'box': [x1, y1, x2, y2],
                        'confidence': float(prob),
                        'face_area_ratio': float(face_area_ratio),
                        'sharpness': float(laplacian_var),
                        'landmarks': landmark.tolist() if landmark is not None else None
                    })

        logger.info(f"人脸检测完成！")
        logger.info(f"检测统计:")
        logger.info(f"  总检测: {filter_stats['total_detected']}")
        logger.info(f"  低置信度: {filter_stats['low_confidence']}")
        logger.info(f"  人脸太小: {filter_stats['too_small']}")
        logger.info(f"  侧脸: {filter_stats['side_face']}")
        logger.info(f"  模糊: {filter_stats['blurry']}")
        logger.info(f"  ✓ 高质量人脸: {filter_stats['valid_faces']}")

        return all_faces, filter_stats

    def extract_face_embeddings(self, faces: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """
        提取人脸特征向量

        Args:
            faces: 人脸数据列表

        Returns:
            (embeddings, faces_with_embeddings)
            embeddings: (N, 512) numpy数组
            faces_with_embeddings: 带有embedding的人脸列表
        """
        logger.info(f"开始提取 {len(faces)} 张人脸的特征向量...")

        embeddings_list = []
        valid_faces = []

        for i, face_data in enumerate(faces):
            frame = face_data['frame']
            box = face_data['box']
            x1, y1, x2, y2 = map(int, box)

            # 裁剪人脸
            face_crop = frame[y1:y2, x1:x2]

            if face_crop.size == 0:
                continue

            # 调整大小到160x160
            face_resized = cv2.resize(face_crop, (160, 160))

            # 转换为tensor
            face_tensor = torch.from_numpy(face_resized).permute(2, 0, 1).float()
            face_tensor = (face_tensor - 127.5) / 128.0  # 归一化
            face_tensor = face_tensor.unsqueeze(0).to(self.device)

            # 提取特征
            with torch.no_grad():
                embedding = self.facenet(face_tensor).cpu().numpy()[0]

            embeddings_list.append(embedding)
            valid_faces.append(face_data)

            if (i + 1) % 100 == 0:
                logger.info(f"已处理 {i + 1}/{len(faces)} 张人脸")

        embeddings = np.array(embeddings_list)
        logger.info(f"特征提取完成！形状: {embeddings.shape}")

        return embeddings, valid_faces
