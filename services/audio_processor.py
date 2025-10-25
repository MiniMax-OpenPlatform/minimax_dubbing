"""
音频处理服务
负责音频拼接、格式转换、时长计算等功能
"""
import os
import logging
import tempfile
from typing import List, Optional, Tuple
from pydub import AudioSegment
from pydub.silence import split_on_silence
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """音频处理器"""

    def __init__(self):
        self.temp_dir = getattr(settings, 'MEDIA_ROOT', tempfile.gettempdir())

    def download_audio(self, url: str, trace_id: Optional[str] = None) -> Optional[str]:
        """
        下载音频文件到本地临时目录

        Args:
            url: 音频URL
            trace_id: 追踪ID

        Returns:
            本地文件路径，失败返回None
        """
        try:
            logger.info(f"[{trace_id}] 开始下载音频: {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.mp3',
                dir=self.temp_dir
            )
            temp_file.write(response.content)
            temp_file.close()

            logger.info(f"[{trace_id}] 音频下载完成: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            logger.error(f"[{trace_id}] 音频下载失败 {url}: {e}")
            return None

    def get_audio_duration(self, file_path: str, trace_id: Optional[str] = None) -> float:
        """
        获取音频时长（秒）

        Args:
            file_path: 音频文件路径
            trace_id: 追踪ID

        Returns:
            音频时长（秒）
        """
        try:
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0  # 转换为秒
            logger.debug(f"[{trace_id}] 音频时长: {duration}s - {file_path}")
            return duration
        except Exception as e:
            logger.error(f"[{trace_id}] 获取音频时长失败 {file_path}: {e}")
            return 0.0

    def trim_silence(self, file_path: str, trace_id: Optional[str] = None) -> Tuple[str, float]:
        """
        去除音频前后的静音

        Args:
            file_path: 音频文件路径
            trace_id: 追踪ID

        Returns:
            (去除静音后的文件路径, 实际音频时长)
        """
        try:
            logger.debug(f"[{trace_id}] 开始去除静音: {file_path}")

            audio = AudioSegment.from_file(file_path)

            # 检测静音并分割
            chunks = split_on_silence(
                audio,
                min_silence_len=100,  # 最小静音长度100ms
                silence_thresh=audio.dBFS - 16,  # 静音阈值
                keep_silence=50  # 保留50ms静音
            )

            if chunks:
                # 合并所有非静音部分
                trimmed_audio = sum(chunks)
            else:
                # 如果没有检测到静音分割，使用原音频
                trimmed_audio = audio

            # 保存去除静音后的音频
            trimmed_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='_trimmed.mp3',
                dir=self.temp_dir
            )
            trimmed_audio.export(trimmed_file.name, format="mp3")

            actual_duration = len(trimmed_audio) / 1000.0
            logger.info(f"[{trace_id}] 静音去除完成: {actual_duration}s - {trimmed_file.name}")

            return trimmed_file.name, actual_duration

        except Exception as e:
            logger.error(f"[{trace_id}] 去除静音失败 {file_path}: {e}")
            return file_path, self.get_audio_duration(file_path, trace_id)

    def concatenate_audios(self, audio_segments: List[dict], output_path: str, trace_id: Optional[str] = None) -> bool:
        """
        拼接多个音频段落为完整音频

        Args:
            audio_segments: 音频段落列表，格式：
                [
                    {
                        'start_time': 0.0,     # 开始时间（秒）
                        'end_time': 5.0,       # 结束时间（秒）
                        'audio_url': 'http://...',  # 音频URL
                        'local_path': '/tmp/...', # 本地路径（可选）
                    },
                    ...
                ]
            output_path: 输出文件路径
            trace_id: 追踪ID

        Returns:
            拼接是否成功
        """
        try:
            logger.info(f"[{trace_id}] 开始拼接音频，共 {len(audio_segments)} 个段落")

            # 按开始时间排序
            sorted_segments = sorted(audio_segments, key=lambda x: x['start_time'])

            # 创建完整音频轨道
            total_duration = max(seg['end_time'] for seg in sorted_segments)
            full_audio = AudioSegment.silent(duration=int(total_duration * 1000))

            successful_count = 0

            for i, segment in enumerate(sorted_segments):
                try:
                    # 获取音频文件
                    audio_file = segment.get('local_path')
                    if not audio_file and segment.get('audio_url'):
                        audio_file = self.download_audio(segment['audio_url'], trace_id)

                    if not audio_file or not os.path.exists(audio_file):
                        logger.warning(f"[{trace_id}] 段落 {i} 音频文件不存在，跳过")
                        continue

                    # 加载音频段落
                    segment_audio = AudioSegment.from_file(audio_file)

                    # 计算插入位置
                    start_ms = int(segment['start_time'] * 1000)

                    # 确保音频不超过段落时长
                    max_duration_ms = int((segment['end_time'] - segment['start_time']) * 1000)
                    if len(segment_audio) > max_duration_ms:
                        segment_audio = segment_audio[:max_duration_ms]

                    # 插入音频到完整轨道
                    full_audio = full_audio.overlay(segment_audio, position=start_ms)
                    successful_count += 1

                    logger.debug(f"[{trace_id}] 段落 {i} 拼接成功: {segment['start_time']}s-{segment['end_time']}s")

                except Exception as e:
                    logger.error(f"[{trace_id}] 段落 {i} 拼接失败: {e}")
                    continue

            # 导出完整音频
            full_audio.export(output_path, format="mp3", bitrate="128k")

            logger.info(f"[{trace_id}] 音频拼接完成: {successful_count}/{len(sorted_segments)} 段落成功，输出: {output_path}")
            return True

        except Exception as e:
            logger.error(f"[{trace_id}] 音频拼接失败: {e}")
            return False

    def create_silence(self, duration_seconds: float, output_path: str) -> bool:
        """
        创建指定时长的静音音频

        Args:
            duration_seconds: 时长（秒）
            output_path: 输出路径

        Returns:
            创建是否成功
        """
        try:
            silence = AudioSegment.silent(duration=int(duration_seconds * 1000))
            silence.export(output_path, format="mp3")
            return True
        except Exception as e:
            logger.error(f"创建静音音频失败: {e}")
            return False

    def mix_audio_tracks(
        self,
        translated_audio_path: str,
        background_audio_path: str,
        output_path: str,
        translated_volume: float = 1.0,
        background_volume: float = 0.3,
        trace_id: Optional[str] = None
    ) -> bool:
        """
        混合翻译音频和背景音

        Args:
            translated_audio_path: 翻译音频路径（拼接后的完整翻译音频）
            background_audio_path: 背景音路径（人声分离后的背景音）
            output_path: 输出混合音频路径
            translated_volume: 翻译音频音量（0.0-1.0），默认 1.0
            background_volume: 背景音音量（0.0-1.0），默认 0.3
            trace_id: 追踪ID

        Returns:
            混合是否成功
        """
        try:
            logger.info(f"[{trace_id}] 开始混合音频轨道")
            logger.info(f"[{trace_id}] 翻译音频: {translated_audio_path}")
            logger.info(f"[{trace_id}] 背景音: {background_audio_path}")

            # 加载音频文件
            translated_audio = AudioSegment.from_file(translated_audio_path)
            background_audio = AudioSegment.from_file(background_audio_path)

            # 调整音量
            if translated_volume != 1.0:
                translated_audio = translated_audio + (20 * (translated_volume - 1))  # dB 调整
            if background_volume != 1.0:
                background_audio = background_audio + (20 * (background_volume - 1))  # dB 调整

            logger.info(f"[{trace_id}] 音量调整: 翻译={translated_volume}, 背景={background_volume}")

            # 确保两个音频时长一致（使用较长的作为基准）
            translated_duration = len(translated_audio)
            background_duration = len(background_audio)

            if translated_duration > background_duration:
                # 背景音较短，循环或静音填充
                logger.info(f"[{trace_id}] 背景音较短 ({background_duration}ms < {translated_duration}ms)，延长背景音")
                # 添加静音填充
                silence_needed = translated_duration - background_duration
                background_audio = background_audio + AudioSegment.silent(duration=silence_needed)
            elif background_duration > translated_duration:
                # 背景音较长，裁剪
                logger.info(f"[{trace_id}] 背景音较长 ({background_duration}ms > {translated_duration}ms)，裁剪背景音")
                background_audio = background_audio[:translated_duration]

            # 混合音频（overlay）
            mixed_audio = translated_audio.overlay(background_audio)

            # 导出混合音频
            mixed_audio.export(output_path, format="mp3", bitrate="192k")

            logger.info(f"[{trace_id}] 音频混合完成: {output_path}")
            logger.info(f"[{trace_id}] 混合音频时长: {len(mixed_audio)/1000.0:.2f}秒")

            return True

        except Exception as e:
            logger.error(f"[{trace_id}] 音频混合失败: {e}", exc_info=True)
            return False

    def cleanup_temp_files(self, file_paths: List[str], trace_id: Optional[str] = None):
        """
        清理临时文件

        Args:
            file_paths: 文件路径列表
            trace_id: 追踪ID
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"[{trace_id}] 临时文件已清理: {file_path}")
            except Exception as e:
                logger.warning(f"[{trace_id}] 清理临时文件失败 {file_path}: {e}")