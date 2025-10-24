"""
音频分离基础抽象类

提供统一的接口，便于未来扩展不同的分离算法
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseSeparator(ABC):
    """音频分离器基类"""

    def __init__(self, device: str = 'cpu'):
        """
        初始化分离器

        Args:
            device: 设备类型 'cpu' 或 'cuda'
        """
        self.device = device
        logger.info(f"初始化音频分离器: device={device}")

    @abstractmethod
    def separate(self, audio_path: str, output_dir: str) -> Dict[str, str]:
        """
        分离音频

        Args:
            audio_path: 输入音频文件路径
            output_dir: 输出目录

        Returns:
            Dict[str, str]: 包含分离后的文件路径
            {
                'vocals': '人声文件路径',
                'background': '背景音文件路径',
                'original': '原始音频路径'
            }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查分离器是否可用（依赖是否安装）

        Returns:
            bool: 是否可用
        """
        pass
