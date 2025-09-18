"""
项目管理视图
"""
import os
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.http import HttpResponse
from .models import Project
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer,
    ProjectCreateSerializer, SRTUploadSerializer
)
from segments.models import Segment
from services.parsers.srt_parser import SRTParser
from services.clients.minimax_client import MiniMaxClient
from services.algorithms.timestamp_aligner import TimestampAligner
from services.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """项目管理ViewSet"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        else:
            return ProjectDetailSerializer

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_srt(self, request):
        """
        上传SRT文件并创建项目
        """
        serializer = SRTUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        srt_file = serializer.validated_data['srt_file']
        project_name = serializer.validated_data.get('project_name') or srt_file.name.replace('.srt', '')

        try:
            with transaction.atomic():
                # 解析SRT文件
                srt_content = srt_file.read().decode('utf-8')
                segments_data = SRTParser.parse_srt_content(srt_content)

                # 创建项目
                project = Project.objects.create(
                    user=request.user,
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

                logger.info(f"SRT上传成功: 项目{project.name}, 共{len(segments_data)}个段落")

                return Response({
                    'success': True,
                    'project_id': project.id,
                    'project_name': project.name,
                    'segment_count': len(segments_data),
                    'message': f'SRT文件上传成功，创建了{len(segments_data)}个段落'
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"SRT上传失败: {str(e)}")
            return Response({
                'error': f'SRT文件解析失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def batch_translate(self, request, pk=None):
        """
        批量翻译项目中的所有段落
        """
        project = self.get_object()

        # 检查项目状态
        if project.status == 'processing':
            return Response({
                'error': '项目正在处理中，请稍后再试'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 更新项目状态
            project.status = 'processing'
            project.save()

            # 获取待翻译的段落
            segments = project.segments.filter(status='pending').order_by('index')
            if not segments.exists():
                return Response({
                    'message': '没有待翻译的段落'
                }, status=status.HTTP_200_OK)

            # 初始化MiniMax客户端
            client = MiniMaxClient(
                api_key=request.user.api_key,
                group_id=request.user.group_id
            )

            success_count = 0
            total_count = segments.count()

            # 获取目标语言的显示名称
            target_lang_display = dict(Project.LANGUAGE_CHOICES).get(
                project.target_lang, project.target_lang
            )

            for segment in segments:
                try:
                    # 更新段落状态
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
                        logger.info(f"段落{segment.index}翻译成功: {result['translation']}")
                    else:
                        segment.status = 'failed'
                        segment.save()
                        logger.error(f"段落{segment.index}翻译失败")

                except Exception as e:
                    segment.status = 'failed'
                    segment.save()
                    logger.error(f"段落{segment.index}翻译异常: {str(e)}")

            # 更新项目状态
            if success_count == total_count:
                project.status = 'completed'
            else:
                project.status = 'draft'
            project.save()

            return Response({
                'success': True,
                'total_segments': total_count,
                'success_count': success_count,
                'failed_count': total_count - success_count,
                'message': f'批量翻译完成: 成功{success_count}个，失败{total_count - success_count}个'
            })

        except Exception as e:
            project.status = 'failed'
            project.save()
            logger.error(f"批量翻译失败: {str(e)}")
            return Response({
                'error': f'批量翻译失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def export_srt(self, request, pk=None):
        """
        导出项目的SRT文件
        """
        project = self.get_object()
        segments = project.segments.order_by('index')

        if not segments.exists():
            return Response({
                'error': '项目中没有段落数据'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 构建段落数据
            export_segments = []
            for segment in segments:
                export_segments.append({
                    'index': segment.index,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'text': segment.translated_text or segment.original_text
                })

            # 生成SRT内容
            srt_content = SRTParser.export_to_srt(export_segments)

            # 返回文件下载
            response = HttpResponse(srt_content, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{project.name}_translated.srt"'
            return response

        except Exception as e:
            logger.error(f"SRT导出失败: {str(e)}")
            return Response({
                'error': f'SRT导出失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def project_stats(self, request, pk=None):
        """
        获取项目统计信息
        """
        project = self.get_object()
        segments = project.segments.all()

        stats = {
            'project_info': {
                'name': project.name,
                'status': project.status,
                'source_lang': project.get_source_lang_display(),
                'target_lang': project.get_target_lang_display(),
                'created_at': project.created_at,
                'updated_at': project.updated_at,
            },
            'segment_stats': {
                'total': segments.count(),
                'pending': segments.filter(status='pending').count(),
                'translating': segments.filter(status='translating').count(),
                'translated': segments.filter(status='translated').count(),
                'tts_processing': segments.filter(status='tts_processing').count(),
                'completed': segments.filter(status='completed').count(),
                'failed': segments.filter(status='failed').count(),
                'silent': segments.filter(status='silent').count(),
            },
            'progress': {
                'percentage': project.progress_percentage,
                'completed_segments': project.completed_segment_count,
                'total_segments': project.segment_count,
            }
        }

        return Response(stats)

    @action(detail=True, methods=['post'])
    def concatenate_audio(self, request, pk=None):
        """
        拼接项目中所有音频段落为完整音频文件
        """
        import uuid
        from django.conf import settings

        project = self.get_object()
        trace_id = str(uuid.uuid4())[:8]

        try:
            logger.info(f"[{trace_id}] 开始拼接项目音频: {project.name}")

            # 获取所有有音频的段落
            segments = project.segments.filter(
                translated_audio_url__isnull=False
            ).exclude(
                translated_audio_url__exact=''
            ).order_by('index')

            if not segments.exists():
                return Response({
                    'error': '没有可用的音频段落进行拼接'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 准备音频段落数据
            audio_segments = []
            for segment in segments:
                audio_segments.append({
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'audio_url': segment.translated_audio_url,
                    'index': segment.index
                })

            # 创建输出文件路径
            output_dir = os.path.join(settings.MEDIA_ROOT, 'concatenated')
            os.makedirs(output_dir, exist_ok=True)

            output_filename = f"{project.name}_{trace_id}_complete.mp3"
            output_path = os.path.join(output_dir, output_filename)

            # 执行音频拼接
            processor = AudioProcessor()
            success = processor.concatenate_audios(
                audio_segments=audio_segments,
                output_path=output_path,
                trace_id=trace_id
            )

            if success:
                # 生成访问URL
                audio_url = request.build_absolute_uri(
                    f'/media/concatenated/{output_filename}'
                )

                logger.info(f"[{trace_id}] 音频拼接成功: {audio_url}")

                return Response({
                    'success': True,
                    'audio_url': audio_url,
                    'segments_count': len(audio_segments),
                    'trace_id': trace_id,
                    'message': f'成功拼接{len(audio_segments)}个音频段落'
                })
            else:
                return Response({
                    'error': '音频拼接失败，请查看日志'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"[{trace_id}] 音频拼接异常: {str(e)}")
            return Response({
                'error': f'音频拼接失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
