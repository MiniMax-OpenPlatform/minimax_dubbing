"""
Segment业务逻辑服务
"""
import logging
from typing import Dict, Any, List, Optional
from django.db import transaction

from segments.models import Segment
from projects.models import Project
from services.clients.minimax_client import MiniMaxClient
from services.algorithms.timestamp_aligner import TimestampAligner
from .base import BaseService

logger = logging.getLogger(__name__)


class SegmentService(BaseService):
    """段落业务逻辑服务"""

    def translate_segment(self, segment: Segment, api_key: str, group_id: str) -> Dict[str, Any]:
        """翻译单个段落"""
        project = segment.project

        try:

            # 初始化MiniMax客户端
            client = MiniMaxClient(api_key=api_key, group_id=group_id)

            # 获取目标语言显示名称
            target_lang_display = dict(Project.LANGUAGE_CHOICES).get(
                project.target_lang, project.target_lang
            )

            # 调用翻译API
            result = client.translate(
                text=segment.original_text,
                target_language=target_lang_display,
                custom_vocabulary=project.custom_vocabulary
            )

            if result['success']:
                segment.translated_text = result['translation']
                segment.save()

                self.log_operation(
                    f"段落{segment.index}翻译成功",
                    {'segment_id': segment.id, 'translation': result['translation']}
                )

                return {
                    'success': True,
                    'translated_text': result['translation'],
                    'trace_id': result['trace_id'],
                    'message': '翻译成功'
                }
            else:
                segment.save()
                return {
                    'success': False,
                    'error': '翻译失败',
                    'status_code': 500
                }

        except Exception as e:
            segment.save()
            self.logger.error(f"段落{segment.index}翻译异常: {str(e)}")
            return {
                'success': False,
                'error': f'翻译失败: {str(e)}',
                'status_code': 500
            }

    def generate_tts_for_segment(self, segment: Segment, api_key: str, group_id: str) -> Dict[str, Any]:
        """生成单个段落的TTS音频（带时间戳对齐）"""
        project = segment.project

        if not segment.translated_text:
            return {
                'success': False,
                'error': '段落译文为空，无法生成TTS',
                'status_code': 400
            }

        try:

            # 初始化客户端和对齐器
            client = MiniMaxClient(api_key=api_key, group_id=group_id)
            aligner = TimestampAligner(client)

            # 设置音色ID
            if not segment.voice_id:
                voice_mappings = project.voice_mappings or {}
                segment.voice_id = voice_mappings.get(segment.speaker, 'male-qn-qingse')

            # 获取目标语言对应的language_boost
            language_boost = self._get_language_boost(project.target_lang)

            # 调用时间戳对齐算法
            align_result = aligner.align_timestamp(
                text=segment.translated_text,
                target_duration=segment.target_duration,
                voice_id=segment.voice_id,
                original_text=segment.original_text,
                target_language=dict(Project.LANGUAGE_CHOICES).get(project.target_lang),
                custom_vocabulary=project.custom_vocabulary,
                emotion=segment.emotion,
                language_boost=language_boost
            )

            return self._process_tts_result(segment, align_result)

        except Exception as e:
            segment.save()
            self.logger.error(f"段落{segment.index}TTS生成异常: {str(e)}")
            return {
                'success': False,
                'error': f'TTS生成失败: {str(e)}',
                'status_code': 500
            }

    def batch_update_segments(self, segments_queryset, segment_ids: List[int], update_data: Dict[str, Any]) -> Dict[str, Any]:
        """批量更新段落"""
        try:
            with transaction.atomic():
                segments = segments_queryset.filter(id__in=segment_ids)

                if not segments.exists():
                    return {
                        'success': False,
                        'error': '没有找到要更新的段落',
                        'status_code': 404
                    }

                updated_count = 0
                for segment in segments:
                    updated_count += self._update_single_segment(segment, update_data)

                self.log_operation(
                    f"批量更新完成: 更新了{updated_count}个段落",
                    {'updated_count': updated_count, 'segment_ids': segment_ids}
                )

                return {
                    'success': True,
                    'updated_count': updated_count,
                    'message': f'批量更新完成，共更新{updated_count}个段落'
                }

        except Exception as e:
            self.logger.error(f"批量更新失败: {str(e)}")
            return {
                'success': False,
                'error': f'批量更新失败: {str(e)}',
                'status_code': 500
            }

    def batch_generate_tts(self, project: Project, segments_queryset, api_key: str, group_id: str) -> Dict[str, Any]:
        """批量生成TTS音频（覆盖现有音频）"""
        segments = segments_queryset.filter(
            translated_text__isnull=False
        ).exclude(translated_text='')

        if not segments.exists():
            self.logger.info(f"项目 {project.name} (ID: {project.id}) 没有可生成TTS的段落（译文为空）")
            return {
                'success': True,
                'message': '没有可生成TTS的段落（译文为空）'
            }

        try:
            # 初始化客户端和对齐器
            self.logger.info(f"[批量TTS] 开始处理项目 {project.name} (ID: {project.id})")
            self.logger.info(f"[批量TTS] 初始化 MiniMax 客户端和时间戳对齐器")

            client = MiniMaxClient(api_key=api_key, group_id=group_id)
            aligner = TimestampAligner(client)

            language_boost = self._get_language_boost(project.target_lang)
            self.logger.info(f"[批量TTS] 目标语言: {project.target_lang}, language_boost: {language_boost}")

            counters = {'success': 0, 'failed': 0, 'silent': 0}
            total_count = segments.count()
            self.logger.info(f"[批量TTS] 共 {total_count} 个段落需要处理")

            for index, segment in enumerate(segments, 1):
                self.logger.info(f"[批量TTS] 处理段落 {index}/{total_count} (ID: {segment.id}, 索引: {segment.index})")
                self.logger.info(f"[批量TTS] 段落文本: {segment.translated_text[:50]}...")

                result = self._process_single_tts(segment, project, aligner, language_boost)
                counters[result] += 1

                self.logger.info(f"[批量TTS] 段落 {segment.index} 处理结果: {result}")
                self.logger.info(f"[批量TTS] 当前进度: {index}/{total_count} 完成")

            self.logger.info(f"[批量TTS] 项目 {project.name} 批量TTS完成")
            self.logger.info(f"[批量TTS] 最终统计 - 成功: {counters['success']}, 失败: {counters['failed']}, 静音: {counters['silent']}")

            return {
                'success': True,
                'total_segments': total_count,
                'success_count': counters['success'],
                'silent_count': counters['silent'],
                'failed_count': counters['failed'],
                'message': f'批量TTS完成: 成功{counters["success"]}个，静音{counters["silent"]}个，失败{counters["failed"]}个'
            }

        except Exception as e:
            self.logger.error(f"批量TTS失败: {str(e)}")
            return {
                'success': False,
                'error': f'批量TTS失败: {str(e)}',
                'status_code': 500
            }

    def _get_language_boost(self, target_lang: str) -> str:
        """获取目标语言对应的language_boost"""
        language_boost_map = {
            'zh': 'Chinese',
            'yue': 'Chinese,Yue',
            'en': 'English',
            'ja': 'Japanese',
            'ko': 'Korean',
        }
        return language_boost_map.get(target_lang, 'Chinese')

    def _process_tts_result(self, segment: Segment, align_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理TTS生成结果"""
        if align_result['success']:
            # 更新段落数据
            segment.translated_audio_url = align_result['audio_url']
            segment.t_tts_duration = align_result['final_duration']
            segment.speed = align_result['speed']
            segment.translated_text = align_result['optimized_text']
            segment.calculate_ratio()
            segment.save()

            self.log_operation(
                f"段落{segment.index}TTS生成成功，时间戳对齐完成",
                {'segment_id': segment.id, 'duration': align_result['final_duration']}
            )

            return {
                'success': True,
                'audio_url': align_result['audio_url'],
                'final_duration': align_result['final_duration'],
                'ratio': segment.ratio,
                'speed': align_result['speed'],
                'optimized_text': align_result['optimized_text'],
                'optimization_steps': len(align_result['optimization_steps']),
                'trace_ids': align_result['trace_ids'],
                'message': 'TTS生成并对齐成功'
            }
        else:
            # 对齐失败，设为静音
            segment.translated_audio_url = ''
            segment.t_tts_duration = 0.0
            segment.calculate_ratio()
            segment.save()

            self.logger.warning(f"段落{segment.index}时间戳对齐失败，设为静音")

            return {
                'success': False,
                'message': '时间戳对齐失败，段落已设为静音',
                'optimization_steps': align_result.get('optimization_steps', []),
                'trace_ids': align_result.get('trace_ids', [])
            }

    def _update_single_segment(self, segment: Segment, update_data: Dict[str, Any]) -> int:
        """更新单个段落"""
        for field, value in update_data.items():
            setattr(segment, field, value)

        # 如果修改了TTS相关参数，重置音频状态
        if any(field in update_data for field in ['voice_id', 'emotion', 'speed']):
            segment.translated_audio_url = ''
            segment.t_tts_duration = None
            segment.ratio = None
            if segment.status in ['completed', 'tts_processing']:
                segment.status = 'translated'

        segment.save()
        return 1

    def _process_single_tts(self, segment: Segment, project: Project, aligner: TimestampAligner, language_boost: str) -> str:
        """处理单个段落的TTS生成"""
        try:

            # 设置音色ID
            if not segment.voice_id:
                voice_mappings = project.voice_mappings or {}
                segment.voice_id = voice_mappings.get(segment.speaker, 'male-qn-qingse')

            # 调用时间戳对齐算法
            align_result = aligner.align_timestamp(
                text=segment.translated_text,
                target_duration=segment.target_duration,
                voice_id=segment.voice_id,
                original_text=segment.original_text,
                target_language=dict(Project.LANGUAGE_CHOICES).get(project.target_lang),
                custom_vocabulary=project.custom_vocabulary,
                emotion=segment.emotion,
                language_boost=language_boost
            )

            if align_result['success']:
                segment.translated_audio_url = align_result['audio_url']
                segment.t_tts_duration = align_result['final_duration']
                segment.speed = align_result['speed']
                segment.translated_text = align_result['optimized_text']
                segment.calculate_ratio()
                segment.save()
                return 'success'
            else:
                segment.translated_audio_url = ''
                segment.t_tts_duration = 0.0
                segment.calculate_ratio()
                segment.save()
                return 'silent'

        except Exception as e:
            segment.save()
            self.logger.error(f"段落{segment.index}批量TTS失败: {str(e)}")
            return 'failed'