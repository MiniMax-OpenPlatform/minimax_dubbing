"""
人脸聚类模块
使用DBSCAN算法进行聚类
"""
import numpy as np
from sklearn.cluster import DBSCAN
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class FaceClusterer:
    """人脸聚类器"""

    def __init__(self, eps: float = 0.28, min_samples: int = 5):
        """
        初始化聚类器

        Args:
            eps: DBSCAN距离阈值（cosine距离）
            min_samples: 最小样本数
        """
        self.eps = eps
        self.min_samples = min_samples
        logger.info(f"初始化DBSCAN聚类器: eps={eps}, min_samples={min_samples}")

    def cluster_faces(
        self,
        embeddings: np.ndarray,
        faces: List[Dict]
    ) -> Tuple[Dict[int, List[Dict]], Dict]:
        """
        对人脸进行聚类

        Args:
            embeddings: (N, 512) 特征向量
            faces: 人脸数据列表

        Returns:
            (clusters, clustering_info)
            clusters: {speaker_id: [face_data, ...]}
            clustering_info: 聚类统计信息
        """
        logger.info(f"开始聚类 {len(embeddings)} 个人脸特征...")

        # DBSCAN聚类（使用所有CPU核心并行计算距离矩阵）
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric='cosine', n_jobs=-1)
        labels = clustering.fit_predict(embeddings)

        # 统计聚类结果
        unique_labels = set(labels)
        num_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        num_noise = list(labels).count(-1)

        logger.info(f"聚类完成！识别出 {num_clusters} 个说话人，噪声点 {num_noise} 个")

        # 组织聚类结果
        clusters_by_label = {}
        for idx, label in enumerate(labels):
            if label == -1:  # 跳过噪声点
                continue

            if label not in clusters_by_label:
                clusters_by_label[label] = []

            clusters_by_label[label].append({
                **faces[idx],
                'embedding': embeddings[idx]
            })

        # 按人脸数量排序，分配speaker_id
        sorted_labels = sorted(
            clusters_by_label.keys(),
            key=lambda x: len(clusters_by_label[x]),
            reverse=True
        )

        label_to_speaker_id = {label: idx + 1 for idx, label in enumerate(sorted_labels)}

        # 转换为speaker_id索引
        final_clusters = {}
        for label, speaker_id in label_to_speaker_id.items():
            final_clusters[speaker_id] = clusters_by_label[label]
            logger.info(f"  说话人 {speaker_id}: {len(clusters_by_label[label])} 张人脸")

        # 聚类信息
        clustering_info = {
            'num_speakers': num_clusters,
            'num_noise': num_noise,
            'total_faces': len(embeddings),
            'eps': self.eps,
            'min_samples': self.min_samples,
            'label_to_speaker_id': label_to_speaker_id
        }

        return final_clusters, clustering_info

    def get_speaker_statistics(self, clusters: Dict[int, List[Dict]]) -> Dict[int, Dict]:
        """
        统计每个说话人的信息

        Args:
            clusters: {speaker_id: [face_data, ...]}

        Returns:
            {speaker_id: {face_count, segments, ...}}
        """
        statistics = {}

        for speaker_id, faces in clusters.items():
            # 统计出现的片段
            segments = sorted(list(set([face['segment_index'] for face in faces])))

            # 计算平均置信度
            avg_confidence = np.mean([face['confidence'] for face in faces])

            # 按人脸面积排序，找到最清晰的人脸
            sorted_faces = sorted(faces, key=lambda x: x['face_area_ratio'], reverse=True)

            statistics[speaker_id] = {
                'speaker_id': speaker_id,
                'face_count': len(faces),
                'segment_count': len(segments),
                'segments': segments,
                'avg_confidence': float(avg_confidence),
                'best_faces': sorted_faces[:2]  # 最好的2张人脸
            }

        return statistics
