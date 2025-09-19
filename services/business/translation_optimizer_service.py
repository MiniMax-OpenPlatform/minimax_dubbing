"""
翻译优化服务
实现翻译文本的缩短和加长功能
"""
import logging
from typing import Dict, Any
from segments.models import Segment
from projects.models import Project
from services.clients.minimax_client import MiniMaxClient
from .base import BaseService

logger = logging.getLogger(__name__)


class TranslationOptimizerService(BaseService):
    """翻译优化服务 - 缩短和加长翻译"""

    def shorten_translation(self, segment: Segment, api_key: str, group_id: str, target_char_count: int = None) -> Dict[str, Any]:
        """
        缩短翻译文本

        Args:
            segment: 段落对象
            api_key: API密钥
            group_id: 组ID
            target_char_count: 目标字符数，如果不提供则自动计算为当前长度的80%

        Returns:
            Dict: 优化结果
        """
        project = segment.project

        if not segment.translated_text:
            return {
                'success': False,
                'error': '段落译文为空，无法进行缩短',
                'status_code': 400
            }

        try:
            logger.info(f"开始缩短翻译: 段落{segment.index} - {segment.translated_text[:30]}...")

            # 初始化MiniMax客户端
            client = MiniMaxClient(api_key=api_key, group_id=group_id)

            current_char_count = len(segment.translated_text)
            if target_char_count is None:
                # 默认缩短到80%
                target_char_count = int(current_char_count * 0.8)

            # 构建专有词汇表字符串
            vocab_str = self._build_vocabulary_string(project.custom_vocabulary)

            # 获取目标语言显示名称
            target_language = dict(Project.LANGUAGE_CHOICES).get(project.target_lang, project.target_lang)

            # 构建System Prompt
            system_prompt = "你是一个专业的文本优化专家。你必须严格按照指定的字符数要求进行文本缩短，不能超出范围。"

            # 构建User Prompt
            user_prompt = f"""【任务】：缩短翻译文本，严格控制字符数

【原文】：{segment.original_text}
【当前{target_language}翻译】：{segment.translated_text}
【当前字符数】：{current_char_count}字
【目标字符数】：{target_char_count}字（必须控制在{target_char_count-2}到{target_char_count+2}字之间）

【要求】：
1. 保持原意不变
2. 使用更简洁的表达
3. 删除冗余词汇
4. 如果包含以下专有词汇，请按照词表翻译，词表:{vocab_str}
5. 输出字符数必须在{target_char_count-2}-{target_char_count+2}字范围内
6. 只输出优化后的{target_language}翻译文本，不要其他说明

【输出】："""

            logger.info(f"缩短翻译请求 - 目标字符数: {target_char_count}, 当前字符数: {current_char_count}")

            # 调用LLM API
            result = client.translate(
                text=user_prompt,
                target_language="",  # 不需要额外指定，prompt中已包含
                custom_vocabulary=[]  # 已在prompt中处理
            )

            if result['success']:
                optimized_text = result['translation'].strip()
                optimized_char_count = len(optimized_text)

                # 验证是否真的变短了
                if optimized_char_count < current_char_count:
                    # 更新段落
                    segment.translated_text = optimized_text
                    segment.save()

                    self.log_operation(
                        f"段落{segment.index}翻译缩短成功",
                        {
                            'segment_id': segment.id,
                            'original_length': current_char_count,
                            'optimized_length': optimized_char_count,
                            'target_length': target_char_count,
                            'optimized_text': optimized_text,
                            'trace_id': result['trace_id']
                        }
                    )

                    logger.info(f"缩短成功: {current_char_count}字 -> {optimized_char_count}字")
                    return {
                        'success': True,
                        'optimized_text': optimized_text,
                        'original_length': current_char_count,
                        'optimized_length': optimized_char_count,
                        'target_length': target_char_count,
                        'trace_id': result['trace_id'],
                        'message': f'翻译缩短成功：{current_char_count}字 -> {optimized_char_count}字'
                    }
                else:
                    logger.warning(f"缩短失败，文本长度未减少: {current_char_count}字 -> {optimized_char_count}字")
                    return {
                        'success': False,
                        'error': f'缩短失败：文本长度未减少 ({current_char_count}字 -> {optimized_char_count}字)',
                        'optimized_text': optimized_text,
                        'optimized_length': optimized_char_count,
                        'original_length': current_char_count,
                        'status_code': 422
                    }
            else:
                logger.error(f"LLM调用失败: {result}")
                return {
                    'success': False,
                    'error': '翻译缩短失败：LLM调用失败',
                    'status_code': 500
                }

        except Exception as e:
            self.logger.error(f"段落{segment.index}翻译缩短异常: {str(e)}")
            return {
                'success': False,
                'error': f'翻译缩短失败: {str(e)}',
                'status_code': 500
            }

    def lengthen_translation(self, segment: Segment, api_key: str, group_id: str, target_char_count: int = None) -> Dict[str, Any]:
        """
        加长翻译文本

        Args:
            segment: 段落对象
            api_key: API密钥
            group_id: 组ID
            target_char_count: 目标字符数，如果不提供则自动计算为当前长度的120%

        Returns:
            Dict: 优化结果
        """
        project = segment.project

        if not segment.translated_text:
            return {
                'success': False,
                'error': '段落译文为空，无法进行加长',
                'status_code': 400
            }

        try:
            logger.info(f"开始加长翻译: 段落{segment.index} - {segment.translated_text[:30]}...")

            # 初始化MiniMax客户端
            client = MiniMaxClient(api_key=api_key, group_id=group_id)

            current_char_count = len(segment.translated_text)
            if target_char_count is None:
                # 默认加长到120%
                target_char_count = int(current_char_count * 1.2)

            # 构建专有词汇表字符串
            vocab_str = self._build_vocabulary_string(project.custom_vocabulary)

            # 获取目标语言显示名称
            target_language = dict(Project.LANGUAGE_CHOICES).get(project.target_lang, project.target_lang)

            # 构建System Prompt
            system_prompt = "你是一个专业的文本优化专家。你必须严格按照指定的字符数要求进行文本扩展，不能超出范围。"

            # 构建User Prompt
            user_prompt = f"""【任务】：扩展翻译文本，严格控制字符数

【原文】：{segment.original_text}
【当前{target_language}翻译】：{segment.translated_text}
【当前字符数】：{current_char_count}字
【目标字符数】：{target_char_count}字（必须控制在{target_char_count-2}到{target_char_count+2}字之间）

【要求】：
1. 保持原意不变
2. 增加适当的修饰词、语气词
3. 使表达更生动自然
4. 如果包含以下专有词汇，请按照词表翻译，词表:{vocab_str}
5. 输出字符数必须在{target_char_count-2}-{target_char_count+2}字范围内
6. 只输出优化后的{target_language}翻译文本，不要其他说明

【输出】："""

            logger.info(f"加长翻译请求 - 目标字符数: {target_char_count}, 当前字符数: {current_char_count}")

            # 调用LLM API
            result = client.translate(
                text=user_prompt,
                target_language="",  # 不需要额外指定，prompt中已包含
                custom_vocabulary=[]  # 已在prompt中处理
            )

            if result['success']:
                optimized_text = result['translation'].strip()
                optimized_char_count = len(optimized_text)

                # 验证是否真的变长了
                if optimized_char_count > current_char_count:
                    # 更新段落
                    segment.translated_text = optimized_text
                    segment.save()

                    self.log_operation(
                        f"段落{segment.index}翻译加长成功",
                        {
                            'segment_id': segment.id,
                            'original_length': current_char_count,
                            'optimized_length': optimized_char_count,
                            'target_length': target_char_count,
                            'optimized_text': optimized_text,
                            'trace_id': result['trace_id']
                        }
                    )

                    logger.info(f"加长成功: {current_char_count}字 -> {optimized_char_count}字")
                    return {
                        'success': True,
                        'optimized_text': optimized_text,
                        'original_length': current_char_count,
                        'optimized_length': optimized_char_count,
                        'target_length': target_char_count,
                        'trace_id': result['trace_id'],
                        'message': f'翻译加长成功：{current_char_count}字 -> {optimized_char_count}字'
                    }
                else:
                    logger.warning(f"加长失败，文本长度未增加: {current_char_count}字 -> {optimized_char_count}字")
                    return {
                        'success': False,
                        'error': f'加长失败：文本长度未增加 ({current_char_count}字 -> {optimized_char_count}字)',
                        'optimized_text': optimized_text,
                        'optimized_length': optimized_char_count,
                        'original_length': current_char_count,
                        'status_code': 422
                    }
            else:
                logger.error(f"LLM调用失败: {result}")
                return {
                    'success': False,
                    'error': '翻译加长失败：LLM调用失败',
                    'status_code': 500
                }

        except Exception as e:
            self.logger.error(f"段落{segment.index}翻译加长异常: {str(e)}")
            return {
                'success': False,
                'error': f'翻译加长失败: {str(e)}',
                'status_code': 500
            }

    def _build_vocabulary_string(self, custom_vocabulary: list) -> str:
        """构建专有词汇表字符串"""
        if not custom_vocabulary:
            return ""

        vocab_parts = []
        for item in custom_vocabulary:
            if isinstance(item, dict):
                序号 = item.get('序号', len(vocab_parts) + 1)
                词汇 = item.get('词汇', '')
                译文 = item.get('译文', '')
                if 词汇 and 译文:
                    vocab_parts.append(f"{序号}，{词汇}，{译文}")

        return "；".join(vocab_parts) + "；" if vocab_parts else ""