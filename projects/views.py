"""
项目管理视图
"""
import logging
import os
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from .models import Project
from segments.models import Segment
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer,
    ProjectCreateSerializer, SRTUploadSerializer
)
from services.business.project_service import ProjectService
from services.parsers.srt_parser import SRTParser
from services.clients.minimax_client import MiniMaxClient
from services.audio_processor import AudioProcessor
from backend.exceptions import (
    ValidationError, handle_business_logic_error
)

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

    @handle_business_logic_error
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_srt(self, request):
        """
        上传SRT文件并创建项目
        """
        serializer = SRTUploadSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError("SRT文件验证失败", details=serializer.errors)

        srt_file = serializer.validated_data['srt_file']
        project_name = serializer.validated_data.get('project_name') or srt_file.name.replace('.srt', '')

        try:
            # 解析SRT文件内容
            srt_content = srt_file.read().decode('utf-8')
        except UnicodeDecodeError:
            raise ValidationError("SRT文件编码不正确，请使用UTF-8编码")

        # 解析SRT内容
        try:
            segments_data = SRTParser.parse_srt_content(srt_content)
        except Exception as e:
            raise ValidationError(f"SRT文件格式错误: {str(e)}")

        if not segments_data:
            raise ValidationError("SRT文件中没有找到有效的段落数据")

        # 创建项目和段落
        with transaction.atomic():

            project = Project.objects.create(
                    user=request.user,
                    name=project_name,
                    source_lang='Chinese',  # 默认中文
                    target_lang='English',  # 默认英文
                    status='draft',
                    voice_mappings=[
                        {"speaker": "SPEAKER_00", "voice_id": "female-tianmei"}
                    ]
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

    @handle_business_logic_error
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_video(self, request, pk=None):
        """
        为现有项目上传视频文件
        """
        project = self.get_object()

        if 'video_file' not in request.FILES:
            raise ValidationError("请提供视频文件")

        video_file = request.FILES['video_file']

        # 验证文件类型
        allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
        file_extension = os.path.splitext(video_file.name)[1].lower()

        if file_extension not in allowed_extensions:
            raise ValidationError(f"不支持的视频格式，请使用: {', '.join(allowed_extensions)}")

        # 验证文件大小 (500MB)
        if video_file.size > 500 * 1024 * 1024:
            raise ValidationError("视频文件大小不能超过500MB")

        try:
            # 保存视频文件到项目
            project.video_file_path = video_file
            project.save(update_fields=['video_file_path'])

            logger.info(f"视频上传成功: 项目{project.name}, 文件{video_file.name}")

            return Response({
                'success': True,
                'project_id': project.id,
                'project_name': project.name,
                'video_url': project.video_url,
                'message': '视频文件上传成功'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"视频上传失败: {str(e)}")
            raise ValidationError(f"视频上传失败: {str(e)}")

    @action(detail=True, methods=['post'])
    def batch_translate(self, request, pk=None):
        """
        批量翻译项目中的所有段落（统一异步模式）
        """
        try:
            project = self.get_object()

            # 获取需要翻译的段落
            segments = project.segments.filter(
                original_text__isnull=False
            ).exclude(original_text__exact='').order_by('index')

            if not segments.exists():
                return Response({
                    'success': True,
                    'message': '没有可翻译的段落（原文为空）'
                }, status=status.HTTP_200_OK)

            segment_ids = list(segments.values_list('id', flat=True))

            # 使用异步方式启动翻译任务，避免阻塞HTTP响应
            import time
            import threading
            from django.utils import timezone

            # 创建任务ID
            task_id = f"translate_{project.id}_{int(time.time())}"

            logger.info(f"批量翻译任务启动: {task_id}, 项目{project.id}, {len(segment_ids)}个段落")

            # 异步启动真实的翻译任务（不阻塞HTTP响应）
            def async_translate_task():
                try:
                    logger.info(f"[{task_id}] 开始异步翻译任务")

                    # 进行真实的批量翻译
                    from services.clients.minimax_client import MiniMaxClient
                    from segments.models import Segment
                    from system_monitor.models import SystemConfig, TaskMonitor

                    # 获取系统配置
                    config = SystemConfig.get_config()

                    # 创建任务监控记录
                    monitor, created = TaskMonitor.objects.get_or_create(
                        task_id=task_id,
                        defaults={
                            'task_type': 'batch_translate',
                            'project_id': project.id,
                            'project_name': project.name,
                            'total_segments': len(segment_ids),
                            'start_time': timezone.now(),
                            'status': 'running'
                        }
                    )

                    # 初始化翻译客户端
                    client = MiniMaxClient()
                    target_lang_display = project.get_target_lang_display()
                    custom_vocabulary = project.custom_vocabulary or []

                    completed = 0
                    failed = 0

                    # 获取所有需要翻译的段落
                    segments_to_translate = Segment.objects.filter(
                        id__in=segment_ids,
                        project=project
                    ).order_by('index')

                    for segment in segments_to_translate:
                        try:
                            # 检查是否有原文
                            if not segment.original_text or not segment.original_text.strip():
                                logger.warning(f"[{task_id}] 段落{segment.index}没有原文，跳过")
                                continue

                            logger.info(f"[{task_id}] 开始翻译段落{segment.index}: {segment.original_text[:50]}...")

                            # 调用真实翻译API
                            result = client.translate(
                                text=segment.original_text,
                                target_language=target_lang_display,
                                custom_vocabulary=custom_vocabulary
                            )

                            # 处理翻译结果
                            if isinstance(result, dict) and result.get('success'):
                                segment.translated_text = result['translation']
                                segment.save()
                                completed += 1
                                logger.info(f"[{task_id}] 段落{segment.index}翻译成功")
                            else:
                                failed += 1
                                error_msg = f"段落{segment.index}翻译失败: {result}"
                                logger.error(f"[{task_id}] {error_msg}")

                            # 更新监控记录
                            monitor.completed_segments = completed
                            monitor.failed_segments = failed
                            monitor.current_segment_text = segment.original_text[:50] + "..." if len(segment.original_text) > 50 else segment.original_text
                            monitor.save()

                            # 控制API调用频率
                            request_interval = config.batch_translate_request_interval
                            if completed + failed < len(segment_ids):  # 最后一个请求不需要等待
                                logger.debug(f"[{task_id}] 等待{request_interval}秒后处理下一个段落")
                                time.sleep(request_interval)

                        except Exception as e:
                            failed += 1
                            error_msg = f"段落{segment.index}翻译异常: {str(e)}"
                            logger.error(f"[{task_id}] {error_msg}")

                            monitor.completed_segments = completed
                            monitor.failed_segments = failed
                            monitor.error_message = error_msg
                            monitor.save()

                    # 任务完成，更新监控记录
                    monitor.status = 'completed'
                    monitor.end_time = timezone.now()
                    monitor.completed_segments = completed
                    monitor.failed_segments = failed
                    monitor.save()

                    logger.info(f"[{task_id}] 批量翻译完成，成功{completed}个，失败{failed}个")

                except Exception as e:
                    logger.error(f"[{task_id}] 翻译任务执行失败: {str(e)}")

                    # 更新监控记录为失败状态
                    try:
                        from system_monitor.models import TaskMonitor
                        monitor = TaskMonitor.objects.get(task_id=task_id)
                        monitor.status = 'failed'
                        monitor.error_message = str(e)
                        monitor.end_time = timezone.now()
                        monitor.save()
                    except Exception:
                        pass

            # 在单独线程中启动任务，不阻塞当前HTTP响应
            threading.Thread(target=async_translate_task, daemon=True).start()

            # 立即返回响应
            return Response({
                'success': True,
                'task_id': task_id,
                'total_segments': len(segment_ids),
                'message': f'批量翻译任务已启动，共{len(segment_ids)}个段落'
            })

        except Exception as e:
            logger.error(f"批量翻译失败: {str(e)}")
            return Response({
                'error': f'批量翻译失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def batch_translate_progress(self, request, pk=None):
        """
        获取批量翻译进度（真实版本）
        """
        try:
            project = self.get_object()
            task_id = request.query_params.get('task_id')

            if task_id:
                # 使用数据库任务监控获取进度
                from system_monitor.models import TaskMonitor

                try:
                    monitor = TaskMonitor.objects.get(task_id=task_id)

                    # 转换为前端期望的格式
                    progress = {
                        'status': monitor.status,
                        'total': monitor.total_segments,
                        'completed': monitor.completed_segments,
                        'failed': monitor.failed_segments,
                        'current_segment_text': monitor.current_segment_text or '',
                        'estimated_time_remaining': 0,  # 可以后续根据时间计算
                        'error_messages': [monitor.error_message] if monitor.error_message else []
                    }

                    logger.info(f"返回真实进度: 任务{task_id}, {progress['completed']}/{progress['total']}, 状态: {progress['status']}")

                    return Response({
                        'success': True,
                        'progress': progress
                    })

                except TaskMonitor.DoesNotExist:
                    # 任务不存在
                    return Response({
                        'success': False,
                        'error': '任务不存在或已过期'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'success': True,
                    'tasks': []
                })

        except Exception as e:
            logger.error(f"获取批量翻译进度失败: {str(e)}")
            return Response({
                'error': f'获取进度失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def batch_translate_stop(self, request, pk=None):
        """
        停止批量翻译任务
        """
        try:
            from system_monitor.models import TaskMonitor
            from django.utils import timezone

            project = self.get_object()
            task_id = request.data.get('task_id')

            if not task_id:
                return Response({
                    'error': '缺少task_id参数'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 停止任务
            try:
                monitor = TaskMonitor.objects.get(task_id=task_id)
                if monitor.status == 'running':
                    monitor.status = 'cancelled'
                    monitor.end_time = timezone.now()
                    monitor.save()

                    logger.info(f"手动停止批量翻译任务: {task_id}")

                    return Response({
                        'success': True,
                        'message': '批量翻译任务已停止'
                    })
                else:
                    return Response({
                        'success': False,
                        'error': f'任务已是{monitor.status}状态，无法停止'
                    })
            except TaskMonitor.DoesNotExist:
                return Response({
                    'success': False,
                    'error': '任务不存在或已过期'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"停止批量翻译任务失败: {str(e)}")
            return Response({
                'error': f'停止任务失败: {str(e)}'
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

            # 创建输出文件路径 - 使用项目ID作为固定文件名
            output_dir = os.path.join(settings.MEDIA_ROOT, 'concatenated')
            os.makedirs(output_dir, exist_ok=True)

            # 使用项目ID确保文件名唯一且固定
            safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_filename = f"project_{project.id}_{safe_project_name}_complete.mp3"
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

                # 保存到项目模型中
                project.concatenated_audio_url = audio_url
                project.save(update_fields=['concatenated_audio_url'])

                logger.info(f"[{trace_id}] 音频拼接成功并保存到项目: {audio_url}")

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
