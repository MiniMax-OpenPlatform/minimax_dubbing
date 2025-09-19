"""
简化TTS服务
只做基本的TTS生成、去静音和比例检查，不进行时间戳对齐
"""
import logging
from typing import Dict, Any
from segments.models import Segment
from projects.models import Project
from services.clients.minimax_client import MiniMaxClient
from services.algorithms.timestamp_aligner import TimestampAligner
from .base import BaseService

logger = logging.getLogger(__name__)


class SimpleTTSService(BaseService):
    """简化TTS服务 - 不进行时间戳对齐"""

    def generate_simple_tts(self, segment: Segment, api_key: str, group_id: str) -> Dict[str, Any]:
        """
        生成简化TTS音频

        流程：
        1. 调用TTS API生成音频
        2. 去除前后静音并计算实际时长
        3. 计算ratio = t_tts / target_duration
        4. 如果ratio <= 1，则成功更新段落音频
        5. 如果ratio > 1，则失败，不更新段落音频

        Args:
            segment: 段落对象
            api_key: API密钥
            group_id: 组ID

        Returns:
            Dict: 生成结果
        """
        project = segment.project

        if not segment.translated_text:
            return {
                'success': False,
                'error': '段落译文为空，无法生成TTS',
                'status_code': 400
            }

        try:
            logger.info(f"开始简化TTS生成: 段落{segment.index} - {segment.translated_text[:30]}...")

            # 初始化MiniMax客户端
            client = MiniMaxClient(api_key=api_key, group_id=group_id)

            # 设置音色ID
            if not segment.voice_id:
                voice_mappings = project.voice_mappings or {}
                segment.voice_id = voice_mappings.get(segment.speaker, 'male-qn-qingse')

            # 直接使用项目的目标语言作为language_boost
            language_boost = project.target_lang

            # 第一步：调用TTS API生成音频
            logger.info(f"第一步: 调用TTS API生成音频")
            tts_result = client.text_to_speech(
                text=segment.translated_text,
                voice_id=segment.voice_id,
                speed=segment.speed or 1.0,
                emotion=segment.emotion or 'auto',
                language_boost=language_boost,
                model=project.tts_model
            )

            if not tts_result['success']:
                logger.error(f"TTS API调用失败: {tts_result}")
                return {
                    'success': False,
                    'error': 'TTS API调用失败',
                    'status_code': 500
                }

            audio_url = tts_result['audio_url']
            trace_id = tts_result['trace_id']

            # 第二步：去除前后静音并计算实际时长
            logger.info(f"第二步: 去除静音并计算音频时长")
            aligner = TimestampAligner(client)
            try:
                t_tts = aligner.get_audio_duration(audio_url)
            except Exception as e:
                logger.error(f"获取音频时长失败: {str(e)}")
                return {
                    'success': False,
                    'error': f'获取音频时长失败: {str(e)}',
                    'status_code': 500
                }

            # 第三步：计算ratio
            target_duration = segment.target_duration
            ratio = round(t_tts / target_duration, 2) if target_duration else 0

            logger.info(f"第三步: 计算ratio - T_tts={t_tts:.3f}s, 目标={target_duration:.3f}s, ratio={ratio:.2f}")

            # 第四步：根据ratio决定是否更新
            if ratio <= 1.0:
                # ratio <= 1，成功更新段落音频
                segment.translated_audio_url = audio_url
                segment.t_tts_duration = t_tts
                segment.calculate_ratio()
                segment.save()

                self.log_operation(
                    f"段落{segment.index}简化TTS生成成功",
                    {
                        'segment_id': segment.id,
                        'audio_url': audio_url,
                        'duration': t_tts,
                        'ratio': ratio,
                        'trace_id': trace_id
                    }
                )

                logger.info(f"简化TTS成功: ratio={ratio:.2f} <= 1.0，音频已更新")
                return {
                    'success': True,
                    'audio_url': audio_url,
                    'duration': t_tts,
                    'ratio': ratio,
                    'trace_id': trace_id,
                    'message': f'TTS生成成功，时长比例: {ratio:.2f}'
                }
            else:
                # ratio > 1，失败，不更新段落音频
                logger.warning(f"简化TTS失败: ratio={ratio:.2f} > 1.0，音频不更新")
                return {
                    'success': False,
                    'error': f'音频时长超出目标时长，比例: {ratio:.2f}',
                    'ratio': ratio,
                    'duration': t_tts,
                    'target_duration': target_duration,
                    'trace_id': trace_id,
                    'status_code': 400
                }

        except Exception as e:
            segment.save()
            self.logger.error(f"段落{segment.index}简化TTS生成异常: {str(e)}")
            return {
                'success': False,
                'error': f'简化TTS生成失败: {str(e)}',
                'status_code': 500
            }

    def batch_generate_simple_tts(self, project: Project, segments_queryset, api_key: str, group_id: str) -> Dict[str, Any]:
        """
        批量生成简化TTS音频

        Args:
            project: 项目对象
            segments_queryset: 段落查询集
            api_key: API密钥
            group_id: 组ID

        Returns:
            Dict: 批量处理结果
        """
        segments = segments_queryset.filter(
            translated_text__isnull=False
        ).exclude(translated_text='')

        if not segments.exists():
            logger.info(f"项目 {project.name} 没有可生成TTS的段落（译文为空）")
            return {
                'success': True,
                'message': '没有可生成TTS的段落（译文为空）'
            }

        try:
            logger.info(f"开始批量简化TTS: 项目 {project.name}, 共 {segments.count()} 个段落")

            counters = {'success': 0, 'failed': 0}
            total_count = segments.count()

            for index, segment in enumerate(segments, 1):
                logger.info(f"处理段落 {index}/{total_count} (ID: {segment.id}, 索引: {segment.index})")

                result = self.generate_simple_tts(segment, api_key, group_id)

                if result['success']:
                    counters['success'] += 1
                    logger.info(f"段落 {segment.index} 简化TTS成功")
                else:
                    counters['failed'] += 1
                    logger.warning(f"段落 {segment.index} 简化TTS失败: {result.get('error', '未知错误')}")

            logger.info(f"批量简化TTS完成: 成功{counters['success']}个，失败{counters['failed']}个")

            return {
                'success': True,
                'total_segments': total_count,
                'success_count': counters['success'],
                'failed_count': counters['failed'],
                'message': f'批量简化TTS完成: 成功{counters["success"]}个，失败{counters["failed"]}个'
            }

        except Exception as e:
            self.logger.error(f"批量简化TTS失败: {str(e)}")
            return {
                'success': False,
                'error': f'批量简化TTS失败: {str(e)}',
                'status_code': 500
            }