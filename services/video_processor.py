"""
视频处理服务
负责视频合成、音视频合并等功能
"""
import os
import logging
import subprocess
import tempfile
from typing import Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)


class VideoProcessor:
    """视频处理器"""

    def __init__(self):
        self.temp_dir = getattr(settings, 'MEDIA_ROOT', tempfile.gettempdir())
        self.ffmpeg_path = 'ffmpeg'  # 假设 ffmpeg 在 PATH 中

    def check_ffmpeg(self) -> bool:
        """
        检查 ffmpeg 是否可用

        Returns:
            是否可用
        """
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"ffmpeg 检查失败: {e}")
            return False

    def replace_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        trace_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        替换视频的音轨

        Args:
            video_path: 原始视频路径
            audio_path: 新音频路径（混合后的翻译音频）
            output_path: 输出视频路径
            trace_id: 追踪ID

        Returns:
            (是否成功, 错误信息)
        """
        try:
            logger.info(f"[{trace_id}] 开始合成视频")
            logger.info(f"[{trace_id}] 视频: {video_path}")
            logger.info(f"[{trace_id}] 音频: {audio_path}")
            logger.info(f"[{trace_id}] 输出: {output_path}")

            # 检查输入文件
            if not os.path.exists(video_path):
                return False, f"视频文件不存在: {video_path}"
            if not os.path.exists(audio_path):
                return False, f"音频文件不存在: {audio_path}"

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 使用 ffmpeg 替换音轨
            # -i: 输入文件
            # -map 0:v: 使用第一个输入的视频流
            # -map 1:a: 使用第二个输入的音频流
            # -c:v copy: 视频流直接复制（不重新编码）
            # -c:a aac: 音频编码为 AAC
            # -shortest: 以较短的流为准
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,      # 输入视频
                '-i', audio_path,      # 输入音频
                '-map', '0:v',         # 使用视频流
                '-map', '1:a',         # 使用音频流
                '-c:v', 'copy',        # 视频直接复制
                '-c:a', 'aac',         # 音频编码为 AAC
                '-b:a', '192k',        # 音频比特率
                '-shortest',           # 以较短的流为准
                '-y',                  # 覆盖输出文件
                output_path
            ]

            logger.info(f"[{trace_id}] ffmpeg 命令: {' '.join(cmd)}")

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                error_msg = result.stderr
                logger.error(f"[{trace_id}] ffmpeg 执行失败: {error_msg}")
                return False, f"视频合成失败: {error_msg}"

            # 检查输出文件
            if not os.path.exists(output_path):
                return False, "输出文件未生成"

            file_size = os.path.getsize(output_path)
            logger.info(f"[{trace_id}] 视频合成成功")
            logger.info(f"[{trace_id}] 输出文件大小: {file_size / 1024 / 1024:.2f} MB")

            return True, ""

        except subprocess.TimeoutExpired:
            logger.error(f"[{trace_id}] ffmpeg 执行超时")
            return False, "视频合成超时"
        except Exception as e:
            logger.error(f"[{trace_id}] 视频合成失败: {e}", exc_info=True)
            return False, f"视频合成失败: {str(e)}"

    def get_video_info(
        self,
        video_path: str,
        trace_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        获取视频信息

        Args:
            video_path: 视频路径
            trace_id: 追踪ID

        Returns:
            视频信息字典，失败返回 None
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            else:
                logger.error(f"[{trace_id}] 获取视频信息失败: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"[{trace_id}] 获取视频信息失败: {e}")
            return None

    def extract_audio_from_video(
        self,
        video_path: str,
        output_audio_path: str,
        trace_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        从视频中提取音频

        Args:
            video_path: 视频路径
            output_audio_path: 输出音频路径
            trace_id: 追踪ID

        Returns:
            (是否成功, 错误信息)
        """
        try:
            logger.info(f"[{trace_id}] 从视频提取音频")

            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-vn',                 # 不处理视频
                '-acodec', 'libmp3lame',  # 使用 MP3 编码
                '-b:a', '192k',        # 音频比特率
                '-y',                  # 覆盖输出文件
                output_audio_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return False, f"音频提取失败: {result.stderr}"

            if not os.path.exists(output_audio_path):
                return False, "输出音频文件未生成"

            logger.info(f"[{trace_id}] 音频提取成功: {output_audio_path}")
            return True, ""

        except Exception as e:
            logger.error(f"[{trace_id}] 音频提取失败: {e}")
            return False, str(e)
