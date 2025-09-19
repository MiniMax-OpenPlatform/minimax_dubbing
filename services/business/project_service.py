"""
Project业务逻辑服务
"""
import os
import logging
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.http import HttpResponse

from projects.models import Project
from segments.models import Segment
from services.parsers.srt_parser import SRTParser
from services.clients.minimax_client import MiniMaxClient
from services.algorithms.timestamp_aligner import TimestampAligner
from services.audio_processor import AudioProcessor
from backend.exceptions import ValidationError, BusinessLogicError
from .base import BaseService

logger = logging.getLogger(__name__)


class ProjectService(BaseService):
    """项目业务逻辑服务"""

    def upload_srt_file(self, srt_file, project_name: Optional[str] = None) -> Dict[str, Any]:
        """上传SRT文件并创建项目"""
        if not project_name:
            project_name = srt_file.name.replace('.srt', '')

        try:
            # 解析SRT文件内容
            srt_content = srt_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return {
                'success': False,
                'error': "SRT文件编码不正确，请使用UTF-8编码",
                'status_code': 400
            }

        # 解析SRT内容
        try:
            segments_data = SRTParser.parse_srt_content(srt_content)
        except Exception as e:
            return {
                'success': False,
                'error': f"SRT文件格式错误: {str(e)}",
                'status_code': 400
            }

        if not segments_data:
            return {
                'success': False,
                'error': "SRT文件中没有找到有效的段落数据",
                'status_code': 400
            }

        # 创建项目和段落
        try:
            with transaction.atomic():
                project = Project.objects.create(
                    user=self.user,
                    name=project_name,
                    source_lang='zh',  # 默认中文
                    target_lang='en',  # 默认英文
                    status='draft'
                )

                # 创建段落
                for segment_data in segments_data:
                    Segment.objects.create(
                        project=project,
                        index=segment_data['index'],
                        start_time=segment_data['start_time'],
                        end_time=segment_data['end_time'],
                        original_text=segment_data['text'],
                        target_duration=segment_data['duration'],
                        status='pending'
                    )

                self.log_operation(
                    f"SRT上传成功: 项目{project.name}",
                    {'project_id': project.id, 'segments_count': len(segments_data)}
                )

                return {
                    'success': True,
                    'project_id': project.id,
                    'project_name': project.name,
                    'segments_count': len(segments_data),
                    'message': f'SRT文件上传成功，创建了{len(segments_data)}个段落'
                }

        except Exception as e:
            self.logger.error(f"创建项目失败: {str(e)}")
            return {
                'success': False,
                'error': f'创建项目失败: {str(e)}',
                'status_code': 500
            }

    def batch_translate_project(self, project: Project, api_key: str, group_id: str) -> Dict[str, Any]:
        """批量翻译项目中的所有段落"""
        if not self.validate_user_permission(project):
            return {
                'success': False,
                'error': '无权限访问此项目',
                'status_code': 403
            }

        # 获取待翻译的段落
        segments = project.segments.filter(status='pending')
        if not segments.exists():
            return {
                'success': True,
                'message': '没有待翻译的段落'
            }

        try:
            # 初始化客户端
            client = MiniMaxClient(api_key=api_key, group_id=group_id)
            target_lang_display = dict(Project.LANGUAGE_CHOICES).get(
                project.target_lang, project.target_lang
            )

            success_count = 0
            failed_count = 0
            total_count = segments.count()

            for segment in segments:
                try:
                    segment.status = 'translating'
                    segment.save()

                    # 调用翻译API
                    result = client.translate(
                        text=segment.original_text,
                        target_language=target_lang_display,
                        custom_vocabulary=project.custom_vocabulary
                    )

                    if result['success']:
                        segment.translated_text = result['translation']
                        segment.status = 'translated'
                        segment.save()
                        success_count += 1
                    else:
                        segment.status = 'failed'
                        segment.save()
                        failed_count += 1

                except Exception as e:
                    segment.status = 'failed'
                    segment.save()
                    failed_count += 1
                    self.logger.error(f"段落{segment.index}翻译失败: {str(e)}")

            # 更新项目状态
            if failed_count == 0:
                project.status = 'translated'
            elif success_count > 0:
                project.status = 'partial'
            else:
                project.status = 'failed'
            project.save()

            return {
                'success': True,
                'total_segments': total_count,
                'success_count': success_count,
                'failed_count': failed_count,
                'message': f'批量翻译完成: 成功{success_count}个，失败{failed_count}个'
            }

        except Exception as e:
            self.logger.error(f"批量翻译失败: {str(e)}")
            return {
                'success': False,
                'error': f'批量翻译失败: {str(e)}',
                'status_code': 500
            }

    def batch_generate_tts_for_project(self, project: Project, api_key: str, group_id: str) -> Dict[str, Any]:
        """批量生成项目中所有段落的TTS"""
        if not self.validate_user_permission(project):
            return {
                'success': False,
                'error': '无权限访问此项目',
                'status_code': 403
            }

        # 获取已翻译的段落
        segments = project.segments.filter(
            status='translated',
            translated_text__isnull=False
        ).exclude(translated_text='')

        if not segments.exists():
            return {
                'success': True,
                'message': '没有可生成TTS的段落'
            }

        try:
            # 初始化客户端和对齐器
            client = MiniMaxClient(api_key=api_key, group_id=group_id)
            aligner = TimestampAligner(client)

            language_boost = self._get_language_boost(project.target_lang)
            counters = {'success': 0, 'failed': 0, 'silent': 0}
            total_count = segments.count()

            for segment in segments:
                result = self._process_segment_tts(segment, project, aligner, language_boost)
                counters[result] += 1

            # 更新项目状态
            if counters['failed'] == 0 and counters['silent'] == 0:
                project.status = 'completed'
            elif counters['success'] > 0:
                project.status = 'partial'
            project.save()

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

    def concatenate_project_audio(self, project: Project) -> Dict[str, Any]:
        """拼接项目中所有段落的音频"""
        if not self.validate_user_permission(project):
            return {
                'success': False,
                'error': '无权限访问此项目',
                'status_code': 403
            }

        # 获取有音频的段落
        segments = project.segments.filter(
            status='completed',
            translated_audio_url__isnull=False
        ).exclude(translated_audio_url='').order_by('index')

        if not segments.exists():
            return {
                'success': False,
                'error': '没有可拼接的音频段落',
                'status_code': 400
            }

        try:
            processor = AudioProcessor()

            # 收集音频URL列表
            audio_urls = []
            total_duration = 0
            for segment in segments:
                if segment.translated_audio_url:
                    audio_urls.append({
                        'url': segment.translated_audio_url,
                        'start_time': segment.start_time,
                        'end_time': segment.end_time,
                        'duration': segment.t_tts_duration or 0
                    })
                    total_duration += segment.t_tts_duration or 0

            if not audio_urls:
                return {
                    'success': False,
                    'error': '没有找到有效的音频文件',
                    'status_code': 400
                }

            # 调用音频处理器进行拼接
            result = processor.concatenate_audio_segments(
                audio_urls,
                output_filename=f"project_{project.id}_concatenated.mp3"
            )

            if result['success']:
                self.log_operation(
                    f"项目{project.id}音频拼接成功",
                    {'project_id': project.id, 'segments_count': len(audio_urls), 'duration': total_duration}
                )

                return {
                    'success': True,
                    'audio_url': result['audio_url'],
                    'duration': total_duration,
                    'segments_count': len(audio_urls),
                    'message': '音频拼接成功'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '音频拼接失败'),
                    'status_code': 500
                }

        except Exception as e:
            self.logger.error(f"音频拼接失败: {str(e)}")
            return {
                'success': False,
                'error': f'音频拼接失败: {str(e)}',
                'status_code': 500
            }

    def export_project_srt(self, project: Project) -> Dict[str, Any]:
        """导出项目的SRT文件"""
        if not self.validate_user_permission(project):
            return {
                'success': False,
                'error': '无权限访问此项目',
                'status_code': 403
            }

        try:
            segments = project.segments.filter(
                translated_text__isnull=False
            ).exclude(translated_text='').order_by('index')

            if not segments.exists():
                return {
                    'success': False,
                    'error': '没有翻译内容可导出',
                    'status_code': 400
                }

            # 生成SRT内容
            srt_content = SRTParser.generate_srt_content(segments)

            return {
                'success': True,
                'srt_content': srt_content,
                'filename': f"{project.name}_translated.srt",
                'segments_count': segments.count()
            }

        except Exception as e:
            self.logger.error(f"SRT导出失败: {str(e)}")
            return {
                'success': False,
                'error': f'SRT导出失败: {str(e)}',
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

    def _process_segment_tts(self, segment: Segment, project: Project, aligner: TimestampAligner, language_boost: str) -> str:
        """处理单个段落的TTS生成"""
        try:
            segment.status = 'tts_processing'
            segment.save()

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
                segment.status = 'completed'
                segment.save()
                return 'success'
            else:
                segment.status = 'silent'
                segment.translated_audio_url = ''
                segment.t_tts_duration = 0.0
                segment.calculate_ratio()
                segment.save()
                return 'silent'

        except Exception as e:
            segment.status = 'failed'
            segment.save()
            self.logger.error(f"段落{segment.index}TTS生成失败: {str(e)}")
            return 'failed'