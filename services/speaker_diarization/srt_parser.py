"""
SRT解析模块
简化版，从segments模型读取数据
"""
from typing import List, Dict


def parse_srt_from_segments(segments) -> List[Dict]:
    """
    从Django Segment模型解析SRT数据

    Args:
        segments: Django QuerySet of Segment objects

    Returns:
        包含时间戳和文本的字典列表
    """
    segments_data = []

    for seg in segments:
        segments_data.append({
            'index': seg.index,
            'start_time': seg.start_time,
            'end_time': seg.end_time,
            'duration': seg.end_time - seg.start_time,
            'text': seg.original_text,
            'segment_id': seg.id
        })

    return segments_data
