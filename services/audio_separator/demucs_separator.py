"""
Demucs音频分离器实现

使用Facebook的Demucs模型进行人声分离
"""
import os
import shutil
import subprocess
import logging
from typing import Dict, Optional
from pathlib import Path
from .base_separator import BaseSeparator

logger = logging.getLogger(__name__)


class DemucsSeparator(BaseSeparator):
    """使用Demucs模型的音频分离器"""

    def __init__(self, device: str = 'cpu', model: str = 'htdemucs'):
        """
        初始化Demucs分离器

        Args:
            device: 设备类型 'cpu' 或 'cuda'
            model: 模型名称，htdemucs为标准高质量模型
        """
        super().__init__(device)
        self.model = model
        self.shifts = 1  # CPU优化：减少shifts（默认10）
        self.segment = None  # 使用默认值
        self.jobs = 4  # 多进程数量

    def is_available(self) -> bool:
        """检查Demucs是否可用"""
        try:
            result = subprocess.run(
                ['python', '-m', 'demucs', '--help'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Demucs不可用: {str(e)}")
            return False

    def separate(self, audio_path: str, output_dir: str) -> Dict[str, str]:
        """
        使用Demucs分离音频

        Args:
            audio_path: 输入音频文件路径
            output_dir: 输出目录

        Returns:
            Dict[str, str]: 分离后的文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            logger.info(f"开始Demucs分离: {audio_path}")
            logger.info(f"模型: {self.model}, 设备: {self.device}")

            # 构建Demucs命令（参考minimax-video-translation的实现）
            command = [
                'python', '-m', 'demucs.separate',
                '-n', self.model,
                '--two-stems', 'vocals',  # 只分离人声和伴奏
                '-d', self.device,
                '-o', output_dir,
                audio_path
            ]

            # 执行分离
            logger.info(f"执行命令: {' '.join(command)}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 实时输出日志
            for line in process.stderr:
                if line.strip():
                    logger.info(f"Demucs: {line.strip()}")

            process.wait()

            if process.returncode != 0:
                error_msg = process.stderr.read() if process.stderr else "未知错误"
                raise RuntimeError(f"Demucs分离失败: {error_msg}")

            # 查找生成的文件
            # Demucs输出结构: output_dir/{model}/{audio_filename}/vocals.wav 和 no_vocals.wav
            audio_filename = Path(audio_path).stem
            model_output_dir = os.path.join(output_dir, self.model, audio_filename)

            vocals_path = os.path.join(model_output_dir, 'vocals.wav')
            background_path = os.path.join(model_output_dir, 'no_vocals.wav')

            # 验证文件是否生成
            if not os.path.exists(vocals_path):
                raise RuntimeError(f"人声文件未生成: {vocals_path}")
            if not os.path.exists(background_path):
                raise RuntimeError(f"背景音文件未生成: {background_path}")

            # 移动文件到目标位置（便于访问）
            final_vocals_path = os.path.join(output_dir, 'vocals.wav')
            final_background_path = os.path.join(output_dir, 'background.wav')

            shutil.copy2(vocals_path, final_vocals_path)
            shutil.copy2(background_path, final_background_path)

            logger.info(f"Demucs分离完成:")
            logger.info(f"  人声: {final_vocals_path} ({os.path.getsize(final_vocals_path)} bytes)")
            logger.info(f"  背景音: {final_background_path} ({os.path.getsize(final_background_path)} bytes)")

            return {
                'vocals': final_vocals_path,
                'background': final_background_path,
                'original': audio_path
            }

        except subprocess.TimeoutExpired:
            logger.error("Demucs分离超时")
            raise RuntimeError("分离超时，请尝试更短的音频")
        except Exception as e:
            logger.error(f"Demucs分离异常: {str(e)}")
            raise RuntimeError(f"分离失败: {str(e)}")
