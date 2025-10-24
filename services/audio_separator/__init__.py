"""
音频分离服务模块

提供人声分离、背景音分离等功能
"""

from .demucs_separator import DemucsSeparator

__all__ = ['DemucsSeparator']
