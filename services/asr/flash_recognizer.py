#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
阿里云录音文件识别极速版（FlashRecognizer）服务
基于 /data1/devin/test3/aliyun_asr.py 重构为 Django 服务
"""

import json
import os
import requests
import logging
from urllib.parse import urlencode
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AliyunTokenManager:
    """阿里云 NLS AccessToken 管理器"""

    @staticmethod
    def get_access_token(access_key_id: str, access_key_secret: str, region: str = 'cn-shanghai') -> Optional[str]:
        """
        动态获取阿里云 NLS 的 AccessToken

        Args:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            region: 区域，默认 cn-shanghai

        Returns:
            AccessToken 字符串，失败返回 None
        """
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest

            logger.info("正在动态获取 AccessToken...")

            # 创建 AcsClient 实例
            client = AcsClient(access_key_id, access_key_secret, region)

            # 创建 request
            request = CommonRequest()
            request.set_method('POST')
            request.set_domain(f'nls-meta.{region}.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')

            response = client.do_action_with_exception(request)
            jss = json.loads(response)

            if 'Token' in jss and 'Id' in jss['Token']:
                token = jss['Token']['Id']
                expire_time = jss['Token']['ExpireTime']
                logger.info(f"AccessToken 获取成功，过期时间: {expire_time}")
                return token
            else:
                logger.error("Token 响应格式错误")
                return None

        except ImportError:
            logger.error("缺少依赖: aliyun-python-sdk-core，请安装: pip install aliyun-python-sdk-core")
            return None
        except Exception as e:
            logger.error(f"动态获取 Token 失败: {str(e)}")
            return None


class FlashRecognizerService:
    """阿里云 FlashRecognizer 语音识别服务"""

    def __init__(self, app_key: str, access_key_id: str, access_key_secret: str, region: str = 'cn-shanghai'):
        """
        初始化 FlashRecognizer 服务

        Args:
            app_key: 阿里云智能语音应用 Key (APP_KEY)
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            region: 区域，默认 cn-shanghai
        """
        self.app_key = app_key
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region = region
        self.gateway_url = f"https://nls-gateway-{region}.aliyuncs.com/stream/v1/FlashRecognizer"

    def _get_token(self) -> Optional[str]:
        """获取 AccessToken"""
        return AliyunTokenManager.get_access_token(
            self.access_key_id,
            self.access_key_secret,
            self.region
        )

    def recognize(
        self,
        audio_file_path: str,
        audio_format: str = 'mp3',
        sample_rate: int = 16000,
        enable_punctuation: bool = True,
        enable_itn: bool = True
    ) -> Tuple[bool, Dict]:
        """
        使用 FlashRecognizer 识别音频文件

        Args:
            audio_file_path: 音频文件路径
            audio_format: 音频格式 (wav, mp3, opus, aac, amr, pcm)
            sample_rate: 采样率，默认 16000
            enable_punctuation: 启用标点预测
            enable_itn: 启用逆文本正则化

        Returns:
            (success: bool, result: dict)
            success: 是否成功
            result: {
                'sentences': [
                    {
                        'text': '识别文本',
                        'begin_time': 开始时间(毫秒),
                        'end_time': 结束时间(毫秒),
                        'channel_id': 声道ID
                    },
                    ...
                ],
                'duration': 总时长(毫秒),
                'task_id': 任务ID,
                'status': 状态码,
                'message': 消息
            }
        """

        if not os.path.exists(audio_file_path):
            logger.error(f"音频文件不存在: {audio_file_path}")
            return False, {'error': '音频文件不存在'}

        # 获取 AccessToken
        token = self._get_token()
        if not token:
            logger.error("无法获取 AccessToken")
            return False, {'error': '无法获取 AccessToken，请检查 AccessKey 配置和权限'}

        # 读取音频文件
        try:
            with open(audio_file_path, mode='rb') as f:
                audio_content = f.read()
        except Exception as e:
            logger.error(f"读取音频文件失败: {str(e)}")
            return False, {'error': f'读取音频文件失败: {str(e)}'}

        file_size_kb = len(audio_content) / 1024
        logger.info(f"开始识别音频: {audio_file_path} ({file_size_kb:.2f} KB)")

        # 构建请求参数
        params = {
            'appkey': self.app_key,
            'token': token,
            'format': audio_format,
            'sample_rate': sample_rate,
            'enable_punctuation_prediction': 'true' if enable_punctuation else 'false',
            'enable_inverse_text_normalization': 'true' if enable_itn else 'false',
            'enable_intermediate_result': 'false',
            'enable_voice_detection': 'false'
        }

        url = f"{self.gateway_url}?{urlencode(params)}"

        headers = {
            'Content-Type': f'audio/{audio_format}',
            'Content-Length': str(len(audio_content))
        }

        # 检查代理设置
        proxies = {
            'http': os.environ.get('http_proxy', ''),
            'https': os.environ.get('https_proxy', '')
        }

        try:
            logger.info(f"正在上传并识别音频 (格式: {audio_format}, 大小: {len(audio_content)} 字节)")

            response = requests.post(
                url,
                data=audio_content,
                headers=headers,
                proxies=proxies if proxies['http'] or proxies['https'] else None,
                timeout=120  # 2分钟超时
            )

            logger.info(f"API 响应状态: {response.status_code} {response.reason}")

            result = response.json()
            status = result.get('status')

            if status == 20000000:  # 成功
                logger.info("识别成功")
                flash_result = result.get('flash_result', {})
                sentences = flash_result.get('sentences', [])
                duration = flash_result.get('duration', 0)

                logger.info(f"识别到 {len(sentences)} 个句子，总时长: {duration}ms")

                return True, {
                    'sentences': sentences,
                    'duration': duration,
                    'task_id': result.get('task_id', ''),
                    'status': status,
                    'message': result.get('message', 'SUCCESS')
                }
            else:
                error_msg = result.get('message', '未知错误')
                logger.error(f"识别失败: 状态码={status}, 消息={error_msg}")
                return False, {
                    'error': error_msg,
                    'status': status,
                    'message': error_msg,
                    'task_id': result.get('task_id', '')
                }

        except requests.Timeout:
            logger.error("请求超时")
            return False, {'error': 'API 请求超时，请稍后重试'}
        except requests.RequestException as e:
            logger.error(f"网络请求失败: {str(e)}")
            return False, {'error': f'网络请求失败: {str(e)}'}
        except Exception as e:
            logger.error(f"识别过程发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, {'error': f'识别失败: {str(e)}'}

    def recognize_and_create_segments(
        self,
        audio_file_path: str,
        audio_format: str = 'mp3',
        merge_short_segments: bool = True,
        min_duration: float = 0.5,
        max_gap: float = 0.5
    ) -> Tuple[bool, List[Dict], str]:
        """
        识别音频并返回适合导入到 Segment 模型的数据结构

        Args:
            audio_file_path: 音频文件路径
            audio_format: 音频格式
            merge_short_segments: 是否合并短字幕，默认 True
            min_duration: 最小字幕时长（秒），短于此时长的会被合并，默认 0.5 秒
            max_gap: 最大间隔时间（秒），间隔小于此值的字幕会被合并，默认 0.5 秒

        Returns:
            (success: bool, segments: List[Dict], error_msg: str)
            segments 格式:
            [
                {
                    'index': 序号,
                    'start_time': 开始时间(秒, 浮点数),
                    'end_time': 结束时间(秒, 浮点数),
                    'original_text': '原始文本',
                    'translated_text': '',
                    'speaker': ''
                },
                ...
            ]
        """
        success, result = self.recognize(audio_file_path, audio_format)

        if not success:
            error_msg = result.get('error', '识别失败')
            return False, [], error_msg

        sentences = result.get('sentences', [])

        if not sentences:
            return False, [], '识别结果为空'

        # 转换为 Segment 数据结构
        segments = []
        for idx, sentence in enumerate(sentences, start=1):
            text = sentence.get('text', '').strip()
            begin_time_ms = sentence.get('begin_time', 0)
            end_time_ms = sentence.get('end_time', 0)

            if not text:
                continue

            # 将毫秒转换为秒（浮点数）
            start_time_sec = begin_time_ms / 1000.0
            end_time_sec = end_time_ms / 1000.0

            segments.append({
                'index': idx,
                'start_time': start_time_sec,
                'end_time': end_time_sec,
                'original_text': text,
                'translated_text': '',
                'speaker': 'SPEAKER_00'
            })

        # 合并短字幕
        if merge_short_segments and segments:
            segments = self._merge_segments(segments, min_duration, max_gap)

        # 重新编号
        for idx, seg in enumerate(segments, start=1):
            seg['index'] = idx

        logger.info(f"成功创建 {len(segments)} 个字幕段落")
        return True, segments, ''

    @staticmethod
    def _merge_segments(segments: List[Dict], min_duration: float, max_gap: float) -> List[Dict]:
        """
        合并过于离散的短字幕

        策略：
        1. 如果当前字幕时长 < min_duration，且与下一个字幕间隔 < max_gap，则合并
        2. 合并时保留第一个字幕的开始时间，最后一个字幕的结束时间
        3. 文本使用逗号或句号连接

        Args:
            segments: 原始字幕列表
            min_duration: 最小字幕时长（秒）
            max_gap: 最大允许间隔（秒）

        Returns:
            合并后的字幕列表
        """
        if not segments:
            return segments

        merged = []
        current = None

        for seg in segments:
            duration = seg['end_time'] - seg['start_time']

            if current is None:
                # 第一个字幕，直接作为当前
                current = seg.copy()
            else:
                # 计算与当前字幕的间隔
                gap = seg['start_time'] - current['end_time']
                current_duration = current['end_time'] - current['start_time']

                # 判断是否需要合并
                should_merge = (
                    current_duration < min_duration and  # 当前字幕很短
                    gap < max_gap  # 间隔很小
                )

                if should_merge:
                    # 合并到当前字幕
                    current['end_time'] = seg['end_time']
                    # 智能连接文本
                    current_text = current['original_text'].rstrip('。，！？,.!?')
                    new_text = seg['original_text']
                    # 如果当前文本以标点结尾，用空格连接；否则用逗号
                    if current['original_text'][-1:] in '。！？.!?':
                        current['original_text'] = f"{current_text}{current['original_text'][-1:]} {new_text}"
                    else:
                        current['original_text'] = f"{current_text}，{new_text}"
                else:
                    # 不合并，保存当前字幕，开始新的
                    merged.append(current)
                    current = seg.copy()

        # 添加最后一个
        if current is not None:
            merged.append(current)

        original_count = len(segments)
        merged_count = len(merged)
        logger.info(f"字幕合并完成: {original_count} → {merged_count} (减少 {original_count - merged_count} 个)")

        return merged

    @staticmethod
    def _ms_to_timestamp(milliseconds: int) -> str:
        """
        将毫秒转换为 SRT 时间戳格式

        Args:
            milliseconds: 毫秒数

        Returns:
            时间戳字符串，格式: HH:MM:SS,mmm
        """
        seconds = milliseconds / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(milliseconds % 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
