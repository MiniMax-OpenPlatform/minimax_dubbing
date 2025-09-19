"""
MiniMax API客户端
基于提供的API示例实现
"""
import requests
import json
import time
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from backend.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)


# 使用统一异常处理
# MiniMaxAPIError 已被 ExternalAPIError 替代


class MiniMaxClient:
    """MiniMax API客户端"""

    def __init__(self, api_key: str = None, group_id: str = None):
        self.api_key = api_key or settings.MINIMAX_API_KEY
        self.group_id = group_id or settings.MINIMAX_GROUP_ID
        self.llm_base_url = settings.MINIMAX_API_BASE_URL
        self.tts_base_url = settings.MINIMAX_TTS_BASE_URL

        # 请求限流配置
        self.last_llm_request = 0
        self.last_tts_request = 0
        self.llm_interval = 1.0  # LLM请求间隔1秒
        self.tts_interval = 3.0  # TTS请求间隔3秒

    def _rate_limit(self, request_type: str):
        """请求限流控制"""
        current_time = time.time()

        if request_type == 'llm':
            time_since_last = current_time - self.last_llm_request
            if time_since_last < self.llm_interval:
                sleep_time = self.llm_interval - time_since_last
                logger.info(f"LLM请求限流，等待 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
            self.last_llm_request = time.time()

        elif request_type == 'tts':
            time_since_last = current_time - self.last_tts_request
            if time_since_last < self.tts_interval:
                sleep_time = self.tts_interval - time_since_last
                logger.info(f"TTS请求限流，等待 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
            self.last_tts_request = time.time()

    def _make_request(self, method: str, url: str, headers: Dict, data: Any = None,
                     request_type: str = 'llm', max_retries: int = 2) -> Dict:
        """统一的请求方法，支持重试"""
        try:
            logger.info(f"[_make_request] 开始请求 - {method} {url}")
            self._rate_limit(request_type)

            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"[_make_request] 尝试 {attempt + 1}/{max_retries + 1}")

                    if method.upper() == 'POST':
                        if isinstance(data, dict):
                            response = requests.post(url, headers=headers, json=data, timeout=30)
                        else:
                            response = requests.post(url, headers=headers, data=data, timeout=30)
                    else:
                        response = requests.get(url, headers=headers, timeout=30)

                    # 记录trace_id
                    trace_id = response.headers.get('Trace-ID', 'N/A')
                    logger.info(f"[_make_request] API请求 - {request_type.upper()} - Trace-ID: {trace_id} - 状态码: {response.status_code}")

                    if response.status_code == 200:
                        logger.info(f"[_make_request] 开始解析JSON响应")
                        result = response.json()
                        logger.info(f"[_make_request] JSON解析成功，类型: {type(result)}")

                        # 确保result是字典类型才添加trace_id
                        if isinstance(result, dict):
                            result['trace_id'] = trace_id
                            logger.info(f"[_make_request] 请求成功，返回字典")
                            return result
                        else:
                            logger.error(f"[_make_request] API返回格式错误，不是字典类型: {type(result)} - {result}")
                            return {'error': f'API返回格式错误: {result}', 'trace_id': trace_id}
                    else:
                        error_msg = f"API请求失败: {response.status_code} - {response.text}"
                        logger.error(f"[_make_request] {error_msg}")
                        if attempt == max_retries:
                            raise ExternalAPIError(error_msg, service="minimax")

                except requests.exceptions.RequestException as e:
                    error_msg = f"请求异常: {str(e)}"
                    logger.error(f"[_make_request] {error_msg}")
                    if attempt == max_retries:
                        raise ExternalAPIError(error_msg, service="minimax")
                except Exception as e:
                    error_msg = f"未知异常: {str(e)}"
                    logger.error(f"[_make_request] {error_msg}")
                    if attempt == max_retries:
                        raise ExternalAPIError(error_msg, service="minimax")

                # 重试前等待
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"[_make_request] 第{attempt + 1}次重试失败，等待{wait_time}秒后重试")
                    time.sleep(wait_time)

            # 如果所有重试都失败了
            logger.error(f"[_make_request] 所有重试都失败了")
            raise ExternalAPIError("所有重试都失败了", service="minimax")

        except Exception as e:
            logger.error(f"[_make_request] 最外层异常: {str(e)} - 类型: {type(e)}")
            raise

    def translate(self, text: str, target_language: str,
                  custom_vocabulary: list = None) -> Dict[str, Any]:
        """
        LLM翻译

        Args:
            text: 需要翻译的文本
            target_language: 目标语言
            custom_vocabulary: 专有词汇表 [{"序号": 1, "词汇": "小明", "译文": "Xiaoming"}]

        Returns:
            包含翻译结果和trace_id的字典
        """
        logger.info(f"开始翻译: {text[:50]}... -> {target_language}")

        # 生成请求trace_id用于调试
        import uuid
        request_trace_id = str(uuid.uuid4())[:8]
        logger.info(f"[{request_trace_id}] 翻译请求开始 - 文本: {text} - 目标语言: {target_language}")
        logger.info(f"[{request_trace_id}] 专有词汇表: {custom_vocabulary}")

        try:
            # 构建专有词汇表字符串 - 按照prompt_translation模板格式
            vocab_str = ""
            if custom_vocabulary:
                vocab_parts = []
                for item in custom_vocabulary:
                    # 确保item是字典类型
                    if isinstance(item, dict):
                        # 按照模板格式：序号1，词汇1，词汇1译文1；序号2，词汇2，词汇译文2；
                        序号 = item.get('序号', len(vocab_parts) + 1)
                        词汇 = item.get('词汇', '')
                        译文 = item.get('译文', '')
                        if 词汇 and 译文:  # 只有词汇和译文都存在才添加
                            vocab_parts.append(f"{序号}，{词汇}，{译文}")
                    else:
                        logger.warning(f"[{request_trace_id}] 专有词汇项不是字典类型: {type(item)} - {item}")
                vocab_str = "；".join(vocab_parts) + "；" if vocab_parts else ""

            # 构建提示词 - 严格按照prompt_translation模板
            system_prompt = "你是一个专业的翻译助手，擅长翻译视频字幕。请保持翻译的自然流畅，适合口语表达。"

            user_prompt = f"请将以下文本翻译成{target_language}，要求：\n"
            user_prompt += "1. 保持自然流畅的表达方式\n"
            if vocab_str:
                user_prompt += f"2. 如果包含以下专有词汇，请按照词表翻译，词表:{vocab_str}\n"
            user_prompt += f"需要翻译的文本：\"{text}\"\n"
            user_prompt += "请直接给出翻译结果，不需要解释，你的翻译结果是："

            logger.info(f"[{request_trace_id}] 专有词汇表字符串: {vocab_str}")
            logger.info(f"[{request_trace_id}] 用户提示词: {user_prompt}")

            url = f"{self.llm_base_url}/v1/text/chatcompletion_v2"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "MiniMax-Text-01",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "name": "用户", "content": user_prompt}
                ]
            }

            logger.info(f"发送翻译请求到: {url}")
            logger.info(f"请求payload: {payload}")

            result = self._make_request('POST', url, headers, payload, 'llm')
            logger.info(f"API响应: {result}")

            if 'choices' in result and len(result['choices']) > 0:
                translation = result['choices'][0]['message']['content'].strip()
                logger.info(f"翻译成功: {translation}")
                return {
                    'translation': translation,
                    'trace_id': result.get('trace_id'),
                    'success': True
                }
            else:
                logger.error(f"翻译响应格式错误: {result}")
                return {
                    'error': f'翻译响应格式错误: {result}',
                    'success': False
                }

        except Exception as e:
            logger.error(f"[{request_trace_id}] 翻译异常: {str(e)} - 异常类型: {type(e)}")
            import traceback
            logger.error(f"[{request_trace_id}] 异常堆栈: {traceback.format_exc()}")
            return {
                'error': f'翻译失败: {str(e)}',
                'success': False,
                'trace_id': request_trace_id
            }

    def optimize_translation(self, original_text: str, current_translation: str,
                           target_language: str, target_char_count: int,
                           custom_vocabulary: list = None) -> Dict[str, Any]:
        """
        翻译优化（用于时间戳对齐）

        Args:
            original_text: 原文
            current_translation: 当前翻译
            target_language: 目标语言
            target_char_count: 目标字符数
            custom_vocabulary: 专有词汇表

        Returns:
            包含优化后翻译和trace_id的字典
        """
        logger.info(f"开始翻译优化: {current_translation} -> 目标字符数: {target_char_count}")

        current_char_count = len(current_translation)

        # 构建专有词汇表字符串
        vocab_str = ""
        if custom_vocabulary:
            vocab_parts = []
            for item in custom_vocabulary:
                vocab_parts.append(f"序号{item.get('序号', '')}，{item.get('词汇', '')}，{item.get('译文', '')}")
            vocab_str = "；".join(vocab_parts) + "；"

        system_prompt = "你是一个翻译优化专家，你必须严格按照指定的字符数要求进行文本缩短，不能超出范围。"

        user_prompt = f"你的任务是翻译优化，原文\"{original_text}\"当前\"{target_language}\"翻译\"{current_translation}\"，要求：\n"
        user_prompt += "1. 保持口语化表达\n"
        if vocab_str:
            user_prompt += f"2. 如果包含以下专有词汇，请按照词表翻译，词表{vocab_str}\n"
        user_prompt += f"3. 当前字符数是{current_char_count}个字，需要精简成少于{target_char_count}个字，\n"
        user_prompt += f"请直接输出新的\"{target_language}\"翻译如下："

        url = f"{self.llm_base_url}/v1/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "MiniMax-Text-01",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        result = self._make_request('POST', url, headers, payload, 'llm')

        if 'choices' in result and len(result['choices']) > 0:
            optimized_translation = result['choices'][0]['message']['content'].strip()
            logger.info(f"翻译优化成功: {optimized_translation}")
            return {
                'optimized_translation': optimized_translation,
                'trace_id': result.get('trace_id'),
                'success': True
            }
        else:
            raise ExternalAPIError(f"翻译优化响应格式错误: {result}")

    def text_to_speech(self, text: str, voice_id: str, speed: float = 1.0,
                      emotion: str = "auto", language_boost: str = "Chinese") -> Dict[str, Any]:
        """
        文本转语音

        Args:
            text: 需要转换的文本
            voice_id: 音色ID
            speed: 语速 (0.5-2.0)
            emotion: 情绪参数
            language_boost: 语言增强

        Returns:
            包含音频URL和trace_id的字典
        """
        logger.info(f"开始TTS: {text[:30]}... voice={voice_id} speed={speed}")

        url = f"{self.tts_base_url}/v1/t2a_v2?GroupId={self.group_id}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        voice_setting = {
            "voice_id": voice_id,
            "speed": speed
        }

        # 只有非auto情绪才添加emotion参数
        if emotion != "auto":
            voice_setting["emotion"] = emotion

        payload = {
            "model": "speech-01-turbo",
            "text": text,
            "language_boost": language_boost,
            "output_format": "url",
            "voice_setting": voice_setting
        }

        result = self._make_request('POST', url, headers, payload, 'tts')

        if 'data' in result and result['data'] and 'audio' in result['data']:
            audio_url = result['data']['audio']
            logger.info(f"TTS成功: {audio_url}")
            return {
                'audio_url': audio_url,
                'trace_id': result.get('trace_id'),
                'success': True
            }
        else:
            raise ExternalAPIError(f"TTS响应格式错误: {result}")

    def upload_for_clone(self, audio_file_path: str) -> Dict[str, Any]:
        """
        上传音频文件用于音色克隆

        Args:
            audio_file_path: 音频文件路径

        Returns:
            包含file_id的字典
        """
        logger.info(f"开始上传音频文件: {audio_file_path}")

        url = f"{self.tts_base_url}/v1/files/upload?GroupId={self.group_id}"
        headers = {
            'authority': 'api.minimax.chat',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {'purpose': 'voice_clone'}

        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            result = self._make_request('POST', url, headers, data, 'tts')

        if 'file' in result and 'file_id' in result['file']:
            file_id = result['file']['file_id']
            logger.info(f"文件上传成功: {file_id}")
            return {
                'file_id': file_id,
                'trace_id': result.get('trace_id'),
                'success': True
            }
        else:
            raise ExternalAPIError(f"文件上传响应格式错误: {result}")

    def voice_clone(self, file_id: str, voice_id: str, text: str,
                   model: str = "speech-2.5-hd-preview",
                   language_boost: str = "Chinese,Yue") -> Dict[str, Any]:
        """
        音色克隆

        Args:
            file_id: 上传的音频文件ID
            voice_id: 自定义音色ID
            text: 测试文本
            model: 克隆模型
            language_boost: 语言增强

        Returns:
            包含克隆结果的字典
        """
        logger.info(f"开始音色克隆: file_id={file_id} voice_id={voice_id}")

        url = f"{self.tts_base_url}/v1/voice_clone?GroupId={self.group_id}"
        headers = {
            'authorization': f'Bearer {self.api_key}',
            'content-type': 'application/json'
        }

        payload = {
            "file_id": file_id,
            "voice_id": voice_id,
            "text": text,
            "model": model,
            "language_boost": language_boost,
            "need_volumn_normalization": True
        }

        result = self._make_request('POST', url, headers, payload, 'tts')

        logger.info(f"音色克隆完成: {result}")
        return {
            'result': result,
            'trace_id': result.get('trace_id'),
            'success': True
        }