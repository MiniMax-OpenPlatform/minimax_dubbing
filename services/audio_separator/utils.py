"""
音频分离工具函数
"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: str, output_audio_path: str) -> str:
    """
    从视频文件提取音频

    Args:
        video_path: 视频文件路径
        output_audio_path: 输出音频文件路径

    Returns:
        str: 提取后的音频文件路径

    Raises:
        RuntimeError: 提取失败时抛出
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)

        # 使用FFmpeg提取音频
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 不处理视频
            '-acodec', 'pcm_s16le',  # 使用WAV格式
            '-ar', '44100',  # 采样率
            '-ac', '2',  # 双声道
            '-y',  # 覆盖已存在文件
            output_audio_path
        ]

        logger.info(f"开始从视频提取音频: {video_path} -> {output_audio_path}")

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=600  # 10分钟超时
        )

        if os.path.exists(output_audio_path):
            file_size = os.path.getsize(output_audio_path)
            logger.info(f"音频提取成功: {output_audio_path} ({file_size} bytes)")
            return output_audio_path
        else:
            raise RuntimeError("音频文件未生成")

    except subprocess.TimeoutExpired:
        logger.error(f"音频提取超时: {video_path}")
        raise RuntimeError("音频提取超时")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg执行失败: {e.stderr.decode()}")
        raise RuntimeError(f"音频提取失败: {e.stderr.decode()}")
    except Exception as e:
        logger.error(f"音频提取异常: {str(e)}")
        raise RuntimeError(f"音频提取失败: {str(e)}")


def get_audio_duration(audio_path: str) -> float:
    """
    获取音频时长（秒）

    Args:
        audio_path: 音频文件路径

    Returns:
        float: 音频时长（秒）
    """
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        duration = float(result.stdout.decode().strip())
        return duration

    except Exception as e:
        logger.warning(f"获取音频时长失败: {str(e)}")
        return 0.0


def estimate_processing_time(audio_duration: float, device: str = 'cpu') -> int:
    """
    估算处理时间（秒）

    Args:
        audio_duration: 音频时长（秒）
        device: 设备类型

    Returns:
        int: 预估处理时间（秒）
    """
    if device == 'cpu':
        # CPU: 约为音频时长的5-10倍
        return int(audio_duration * 7.5)
    else:
        # GPU: 约为音频时长的1-2倍
        return int(audio_duration * 1.5)
