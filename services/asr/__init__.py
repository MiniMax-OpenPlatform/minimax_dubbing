"""
ASR (Automatic Speech Recognition) 服务模块

使用阿里云 FlashRecognizer 提供语音识别服务
"""

from .flash_recognizer import FlashRecognizerService, AliyunTokenManager

__all__ = [
    'FlashRecognizerService',
    'AliyunTokenManager',
]
