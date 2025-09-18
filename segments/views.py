"""
段落管理视图
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Segment
from .serializers import (
    SegmentListSerializer, SegmentDetailSerializer,
    SegmentUpdateSerializer, BatchUpdateSerializer
)
from projects.models import Project
from services.clients.minimax_client import MiniMaxClient
from services.algorithms.timestamp_aligner import TimestampAligner

logger = logging.getLogger(__name__)


class SegmentViewSet(viewsets.ModelViewSet):
    """段落管理ViewSet"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        if project_id:
            # 通过项目过滤段落
            return Segment.objects.filter(
                project_id=project_id,
                project__user=self.request.user
            ).order_by('index')
        return Segment.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return SegmentListSerializer
        elif self.action in ['update', 'partial_update']:
            return SegmentUpdateSerializer
        else:
            return SegmentDetailSerializer

    @action(detail=True, methods=['post'])
    def translate(self, request, project_pk=None, pk=None):
        """
        翻译单个段落
        """
        segment = self.get_object()
        project = segment.project

        try:
            # 检查段落状态
            if segment.status == 'translating':
                return Response({
                    'error': '段落正在翻译中，请稍后再试'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 更新段落状态
            segment.status = 'translating'
            segment.save()

            # 初始化MiniMax客户端
            client = MiniMaxClient(
                api_key=request.user.api_key,
                group_id=request.user.group_id
            )

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
                segment.status = 'translated'
                segment.save()

                logger.info(f"段落{segment.index}翻译成功: {result['translation']}")

                return Response({
                    'success': True,
                    'translated_text': result['translation'],
                    'trace_id': result['trace_id'],
                    'message': '翻译成功'
                })
            else:
                segment.status = 'failed'
                segment.save()
                return Response({
                    'error': '翻译失败'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            segment.status = 'failed'
            segment.save()
            logger.error(f"段落{segment.index}翻译异常: {str(e)}")
            return Response({
                'error': f'翻译失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def generate_tts(self, request, project_pk=None, pk=None):
        """
        生成单个段落的TTS音频（带时间戳对齐）
        """
        segment = self.get_object()
        project = segment.project

        if not segment.translated_text:
            return Response({
                'error': '段落还未翻译，无法生成TTS'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 更新段落状态
            segment.status = 'tts_processing'
            segment.save()

            # 初始化客户端和对齐器
            client = MiniMaxClient(
                api_key=request.user.api_key,
                group_id=request.user.group_id
            )
            aligner = TimestampAligner(client)

            # 设置音色ID
            if not segment.voice_id:
                # 从项目配置获取默认音色
                voice_mappings = project.voice_mappings or {}
                segment.voice_id = voice_mappings.get(segment.speaker, 'male-qn-qingse')

            # 获取目标语言对应的language_boost
            language_boost_map = {
                'zh': 'Chinese',
                'yue': 'Chinese,Yue',
                'en': 'English',
                'ja': 'Japanese',
                'ko': 'Korean',
            }
            language_boost = language_boost_map.get(project.target_lang, 'Chinese')

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
                # 更新段落数据
                segment.translated_audio_url = align_result['audio_url']
                segment.t_tts_duration = align_result['final_duration']
                segment.speed = align_result['speed']
                segment.translated_text = align_result['optimized_text']  # 可能被优化过
                segment.calculate_ratio()
                segment.status = 'completed'
                segment.save()

                logger.info(f"段落{segment.index}TTS生成成功，时间戳对齐完成")

                return Response({
                    'success': True,
                    'audio_url': align_result['audio_url'],
                    'final_duration': align_result['final_duration'],
                    'ratio': segment.ratio,
                    'speed': align_result['speed'],
                    'optimized_text': align_result['optimized_text'],
                    'optimization_steps': len(align_result['optimization_steps']),
                    'trace_ids': align_result['trace_ids'],
                    'message': 'TTS生成并对齐成功'
                })
            else:
                # 对齐失败，设为静音
                segment.status = 'silent'
                segment.translated_audio_url = ''
                segment.t_tts_duration = 0.0
                segment.calculate_ratio()
                segment.save()

                logger.warning(f"段落{segment.index}时间戳对齐失败，设为静音")

                return Response({
                    'success': False,
                    'message': '时间戳对齐失败，段落已设为静音',
                    'optimization_steps': align_result.get('optimization_steps', []),
                    'trace_ids': align_result.get('trace_ids', [])
                }, status=status.HTTP_200_OK)

        except Exception as e:
            segment.status = 'failed'
            segment.save()
            logger.error(f"段落{segment.index}TTS生成异常: {str(e)}")
            return Response({
                'error': f'TTS生成失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def batch_update(self, request, project_pk=None):
        """
        批量更新段落
        """
        serializer = BatchUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        segment_ids = serializer.validated_data['segment_ids']
        update_data = {k: v for k, v in serializer.validated_data.items() if k != 'segment_ids'}

        try:
            with transaction.atomic():
                # 获取要更新的段落
                segments = self.get_queryset().filter(id__in=segment_ids)

                if not segments.exists():
                    return Response({
                        'error': '没有找到要更新的段落'
                    }, status=status.HTTP_404_NOT_FOUND)

                # 批量更新
                updated_count = 0
                for segment in segments:
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
                    updated_count += 1

                logger.info(f"批量更新完成: 更新了{updated_count}个段落")

                return Response({
                    'success': True,
                    'updated_count': updated_count,
                    'message': f'批量更新完成，共更新{updated_count}个段落'
                })

        except Exception as e:
            logger.error(f"批量更新失败: {str(e)}")
            return Response({
                'error': f'批量更新失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def batch_tts(self, request, project_pk=None):
        """
        批量生成TTS音频
        """
        project = Project.objects.get(id=project_pk, user=request.user)
        segments = self.get_queryset().filter(
            status='translated',
            translated_text__isnull=False
        ).exclude(translated_text='')

        if not segments.exists():
            return Response({
                'message': '没有可生成TTS的段落'
            }, status=status.HTTP_200_OK)

        try:
            # 初始化客户端和对齐器
            client = MiniMaxClient(
                api_key=request.user.api_key,
                group_id=request.user.group_id
            )
            aligner = TimestampAligner(client)

            success_count = 0
            failed_count = 0
            silent_count = 0
            total_count = segments.count()

            # 获取目标语言对应的language_boost
            language_boost_map = {
                'zh': 'Chinese',
                'yue': 'Chinese,Yue',
                'en': 'English',
                'ja': 'Japanese',
                'ko': 'Korean',
            }
            language_boost = language_boost_map.get(project.target_lang, 'Chinese')

            for segment in segments:
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
                        success_count += 1
                    else:
                        segment.status = 'silent'
                        segment.translated_audio_url = ''
                        segment.t_tts_duration = 0.0
                        segment.calculate_ratio()
                        segment.save()
                        silent_count += 1

                except Exception as e:
                    segment.status = 'failed'
                    segment.save()
                    failed_count += 1
                    logger.error(f"段落{segment.index}批量TTS失败: {str(e)}")

            return Response({
                'success': True,
                'total_segments': total_count,
                'success_count': success_count,
                'silent_count': silent_count,
                'failed_count': failed_count,
                'message': f'批量TTS完成: 成功{success_count}个，静音{silent_count}个，失败{failed_count}个'
            })

        except Exception as e:
            logger.error(f"批量TTS失败: {str(e)}")
            return Response({
                'error': f'批量TTS失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
