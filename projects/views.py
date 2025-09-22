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

            # 检查系统级并发限制
            from system_monitor.models import SystemConfig, TaskMonitor
            config = SystemConfig.get_config()

            # 检查当前运行的翻译任务数量
            running_translate_tasks = TaskMonitor.objects.filter(
                task_type='batch_translate',
                status='running'
            ).count()

            if running_translate_tasks >= config.max_concurrent_translate_tasks:
                return Response({
                    'success': False,
                    'error': f'系统翻译任务已达上限（{config.max_concurrent_translate_tasks}个），请稍后再试'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # 检查用户级并发限制（每个用户最多1个翻译任务）
            user_running_tasks = TaskMonitor.objects.filter(
                task_type='batch_translate',
                status='running'
            ).values('project_id').distinct()

            user_projects = Project.objects.filter(
                user=request.user,
                id__in=[task['project_id'] for task in user_running_tasks]
            ).count()

            if user_projects > 0:
                return Response({
                    'success': False,
                    'error': '您已有翻译任务在运行中，请等待完成后再启动新任务'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

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

            # 保存用户API Key信息用于异步任务
            user_api_key = request.user.api_key
            user_group_id = request.user.group_id

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

                    # 初始化翻译客户端 - 使用用户的API Key
                    client = MiniMaxClient(api_key=user_api_key, group_id=user_group_id)
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

    @action(detail=True, methods=['post'])
    def batch_tts(self, request, pk=None):
        """
        批量TTS音频生成（统一异步模式）
        """
        try:
            project = self.get_object()

            # 检查系统级并发限制
            from system_monitor.models import SystemConfig, TaskMonitor
            config = SystemConfig.get_config()

            # 检查当前运行的TTS任务数量
            running_tts_tasks = TaskMonitor.objects.filter(
                task_type='batch_tts',
                status='running'
            ).count()

            if running_tts_tasks >= config.max_concurrent_tts_tasks:
                return Response({
                    'success': False,
                    'error': f'系统TTS任务已达上限（{config.max_concurrent_tts_tasks}个），请稍后再试'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # 检查用户级并发限制（每个用户最多1个TTS任务）
            user_running_tasks = TaskMonitor.objects.filter(
                task_type='batch_tts',
                status='running'
            ).values('project_id').distinct()

            user_projects = Project.objects.filter(
                user=request.user,
                id__in=[task['project_id'] for task in user_running_tasks]
            ).count()

            if user_projects > 0:
                return Response({
                    'success': False,
                    'error': '您已有TTS任务在运行中，请等待完成后再启动新任务'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # 获取需要TTS的段落
            segments = project.segments.filter(
                translated_text__isnull=False
            ).exclude(translated_text__exact='').order_by('index')

            if not segments.exists():
                return Response({
                    'success': True,
                    'message': '没有可TTS的段落（译文为空）'
                }, status=status.HTTP_200_OK)

            segment_ids = list(segments.values_list('id', flat=True))

            # 使用异步方式启动TTS任务，避免阻塞HTTP响应
            import time
            import threading

            # 创建任务ID
            task_id = f"tts_{project.id}_{int(time.time())}"

            logger.info(f"批量TTS任务启动: {task_id}, 项目{project.id}, {len(segment_ids)}个段落")

            # 异步启动真实的TTS任务（不阻塞HTTP响应）
            def async_tts_task():
                try:
                    logger.info(f"[{task_id}] 开始异步TTS任务")

                    # 进行真实的批量TTS
                    from services.business.segment_service import SegmentService
                    from system_monitor.models import SystemConfig, TaskMonitor

                    # 获取系统配置
                    config = SystemConfig.get_config()

                    # 创建任务监控记录
                    monitor, created = TaskMonitor.objects.get_or_create(
                        task_id=task_id,
                        defaults={
                            'task_type': 'batch_tts',
                            'project_id': project.id,
                            'project_name': project.name,
                            'total_segments': len(segment_ids),
                            'start_time': timezone.now(),
                            'status': 'running'
                        }
                    )

                    # 初始化服务
                    service = SegmentService(user=request.user)

                    completed = 0
                    failed = 0
                    silent = 0

                    # 获取所有需要TTS的段落
                    segments_to_process = project.segments.filter(
                        id__in=segment_ids
                    ).order_by('index')

                    for segment in segments_to_process:
                        try:
                            # 检查是否有译文
                            if not segment.translated_text or not segment.translated_text.strip():
                                logger.warning(f"[{task_id}] 段落{segment.index}没有译文，跳过")
                                continue

                            logger.info(f"[{task_id}] 开始TTS段落{segment.index}: {segment.translated_text[:50]}...")

                            # 更新当前步骤
                            monitor.current_step = f"处理段落{segment.index}"
                            monitor.current_segment_text = segment.translated_text[:50] + "..." if len(segment.translated_text) > 50 else segment.translated_text
                            monitor.save()

                            # 调用现有的单段落TTS处理逻辑
                            from services.algorithms.timestamp_aligner import TimestampAligner
                            from services.clients.minimax_client import MiniMaxClient

                            # 初始化客户端和对齐器
                            client = MiniMaxClient(api_key=request.user.api_key, group_id=request.user.group_id)
                            aligner = TimestampAligner(client)

                            # 调用现有的TTS处理逻辑，保持不变
                            result = service._process_single_tts(segment, project, aligner, project.target_lang)

                            if result == 'success':
                                completed += 1
                                logger.info(f"[{task_id}] 段落{segment.index}TTS成功")
                            elif result == 'silent':
                                silent += 1
                                logger.info(f"[{task_id}] 段落{segment.index}设为静音")
                            else:
                                failed += 1
                                logger.error(f"[{task_id}] 段落{segment.index}TTS失败")

                            # 更新监控记录
                            monitor.completed_segments = completed
                            monitor.failed_segments = failed
                            monitor.silent_segments = silent
                            monitor.save()

                            # 控制API调用频率 - TTS比翻译需要更严格的控制
                            request_interval = config.batch_tts_request_interval
                            if completed + failed + silent < len(segment_ids):  # 最后一个请求不需要等待
                                logger.debug(f"[{task_id}] 等待{request_interval}秒后处理下一个段落")
                                time.sleep(request_interval)

                        except Exception as e:
                            failed += 1
                            error_msg = f"段落{segment.index}TTS异常: {str(e)}"
                            logger.error(f"[{task_id}] {error_msg}")

                            monitor.completed_segments = completed
                            monitor.failed_segments = failed
                            monitor.silent_segments = silent
                            monitor.error_message = error_msg
                            monitor.save()

                    # 任务完成，更新监控记录
                    monitor.status = 'completed'
                    monitor.end_time = timezone.now()
                    monitor.completed_segments = completed
                    monitor.failed_segments = failed
                    monitor.silent_segments = silent
                    monitor.current_step = "任务完成"
                    monitor.save()

                    logger.info(f"[{task_id}] 批量TTS完成，成功{completed}个，静音{silent}个，失败{failed}个")

                except Exception as e:
                    logger.error(f"[{task_id}] TTS任务执行失败: {str(e)}")

                    # 更新监控记录为失败状态
                    try:
                        monitor = TaskMonitor.objects.get(task_id=task_id)
                        monitor.status = 'failed'
                        monitor.error_message = str(e)
                        monitor.end_time = timezone.now()
                        monitor.save()
                    except Exception:
                        pass

            # 在单独线程中启动任务，不阻塞当前HTTP响应
            threading.Thread(target=async_tts_task, daemon=True).start()

            # 立即返回响应
            return Response({
                'success': True,
                'task_id': task_id,
                'total_segments': len(segment_ids),
                'message': f'批量TTS任务已启动，共{len(segment_ids)}个段落'
            })

        except Exception as e:
            logger.error(f"批量TTS失败: {str(e)}")
            return Response({
                'error': f'批量TTS失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def batch_tts_progress(self, request, pk=None):
        """
        获取批量TTS进度
        """
        try:
            project = self.get_object()
            task_id = request.query_params.get('task_id')

            if task_id:
                # 使用数据库任务监控获取进度
                from system_monitor.models import TaskMonitor

                try:
                    monitor = TaskMonitor.objects.get(task_id=task_id)

                    # 转换为前端期望的格式，包含TTS特有字段
                    progress = {
                        'status': monitor.status,
                        'total': monitor.total_segments,
                        'completed': monitor.completed_segments,
                        'failed': monitor.failed_segments,
                        'silent': monitor.silent_segments,  # TTS特有：静音段落数
                        'current_segment_text': monitor.current_segment_text or '',
                        'current_step': monitor.current_step or '',  # TTS特有：当前步骤
                        'estimated_time_remaining': 0,  # 可以后续根据时间计算
                        'error_messages': [monitor.error_message] if monitor.error_message else []
                    }

                    logger.info(f"返回TTS进度: 任务{task_id}, {progress['completed']}/{progress['total']}, 静音{progress['silent']}, 状态: {progress['status']}")

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
            logger.error(f"获取批量TTS进度失败: {str(e)}")
            return Response({
                'error': f'获取进度失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def batch_tts_stop(self, request, pk=None):
        """
        停止批量TTS任务
        """
        try:
            from system_monitor.models import TaskMonitor

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
                    monitor.current_step = "任务已取消"
                    monitor.save()

                    logger.info(f"手动停止批量TTS任务: {task_id}")

                    return Response({
                        'success': True,
                        'message': '批量TTS任务已停止'
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
            logger.error(f"停止批量TTS任务失败: {str(e)}")
            return Response({
                'error': f'停止任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def auto_assign_speakers(self, request, pk=None):
        """
        自动分配说话人（使用LLM分析对话内容）
        """
        try:
            project = self.get_object()

            # 获取项目的voice_mappings（角色配置）
            voice_mappings = project.voice_mappings or []
            if not voice_mappings:
                return Response({
                    'success': False,
                    'error': '项目未配置角色，请先在项目设置中配置角色分配'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 提取说话人名称
            speakers = [mapping.get('speaker', '') for mapping in voice_mappings if mapping.get('speaker')]
            if len(speakers) < 2:
                return Response({
                    'success': False,
                    'error': '至少需要配置2个说话人才能进行自动分配'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取项目的所有段落，生成SRT格式文本
            segments = project.segments.filter(
                original_text__isnull=False
            ).exclude(original_text__exact='').order_by('index')

            if not segments.exists():
                return Response({
                    'success': False,
                    'error': '项目中没有可用的段落文本'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 构建SRT格式文本用于LLM分析
            srt_blocks = []
            for segment in segments:
                start_time_str = self._seconds_to_srt_time(float(segment.start_time))
                end_time_str = self._seconds_to_srt_time(float(segment.end_time))
                srt_block = f"{segment.index}\n{start_time_str} --> {end_time_str}\n{segment.original_text}\n"
                srt_blocks.append(srt_block)

            srt_content = '\n'.join(srt_blocks)

            # 调用LLM API进行说话人分配
            import requests
            import json
            import time
            import re

            # 使用用户的API Key而不是settings中的默认Key
            api_key = request.user.api_key
            if not api_key:
                return Response({
                    'success': False,
                    'error': 'User API key not configured'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            from django.conf import settings
            url = getattr(settings, 'MINIMAX_API_URL', "https://api.minimaxi.com/v1/text/chatcompletion_v2")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # 构建prompt，参考api_example/prompt_speakers
            speakers_str = "，".join(speakers)
            prompt_template = f"""请根据对话内容推断说话人，
1）说话人请用提供的人名，
2）严格按照示例格式输出推理过程和标注结果。
以下是示例：
----举例开始----
输入：
以下是小张，小王，小明之间的对话，请补充说话人
----
1
00:00:27,100 --> 00:00:28,833
你是谁啊

2
00:00:33,866 --> 00:00:36,900
我是小明啊

3
00:01:00,466 --> 00:01:02,333
那他呢？

4
00:01:02,533 --> 00:01:03,866
我是小王
----
输出：

推理过程：
{{
1. 首先，我注意到有3个不同的说话人：
   - 一个是打招呼问话的人
   - 一个是小明
   - 还有一个是小王

2. 根据对话内容：
   - 第1句是SPEAKER_00打招呼
   - 第2句是是小明回答
   - 第3句是SPEAKER_00向另一个人打招呼
   - 第4句是小王回答
}}
标注结果：
{{
1
00:00:27,100 --> 00:00:28,833 小张
你是谁啊

2
00:00:33,866 --> 00:00:36,900 小明
我是小明啊

3
00:01:00,466 --> 00:01:02,333 小张
那他呢？

4
00:01:02,533 --> 00:01:03,866 小王
我是小王
}}
----举例结束----

以下是{speakers_str}之间的对话，请补充说话人
{srt_content}

请输出推理过程和标注结果："""

            payload = {
                "model": "MiniMax-Text-01",
                "max_tokens": 8192,  # 增大token限制
                "temperature": 0.01,  # 降低随机性，提高输出稳定性
                "messages": [
                    {
                        "role": "system",
                        "content": "你的任务是分析对话内容分配说话人"
                    },
                    {
                        "role": "user",
                        "content": prompt_template
                    }
                ]
            }

            # 最多重试2次
            for attempt in range(2):
                try:
                    logger.info(f"[自动分配说话人] 第{attempt + 1}次尝试调用LLM API")

                    # 增加超时时间，因为文本较长
                    response = requests.post(url, headers=headers, json=payload, timeout=60)

                    if response.status_code != 200:
                        logger.error(f"[自动分配说话人] API请求失败: {response.status_code}, {response.text}")
                        continue

                    response_data = response.json()

                    # 获取trace_id，尝试多种可能的头部名称
                    trace_id = (response.headers.get('X-Trace-Id') or
                              response.headers.get('Trace-ID') or
                              response.headers.get('trace-id') or
                              response.headers.get('X-Request-Id') or
                              'unknown')

                    logger.info(f"[自动分配说话人] API调用成功, trace_id: {trace_id}")
                    print(f"Trace-ID: {trace_id}")
                    print(f"响应头信息: {dict(response.headers)}")

                    if 'choices' not in response_data or not response_data['choices']:
                        logger.error(f"[自动分配说话人] API响应格式错误: {response_data}")
                        continue

                    llm_result = response_data['choices'][0]['message']['content']
                    logger.info(f"[自动分配说话人] LLM返回结果长度: {len(llm_result)}")

                    # 解析LLM返回的结果
                    speaker_assignments = self._parse_speaker_assignment(llm_result, segments, speakers)

                    if speaker_assignments:
                        # 批量更新段落的说话人信息
                        updated_count = 0
                        for segment_id, speaker in speaker_assignments.items():
                            try:
                                segment = segments.get(id=segment_id)
                                segment.speaker = speaker
                                segment.save(update_fields=['speaker'])
                                updated_count += 1
                            except Exception as e:
                                logger.error(f"[自动分配说话人] 更新段落{segment_id}失败: {str(e)}")

                        logger.info(f"[自动分配说话人] 成功更新{updated_count}个段落的说话人信息")
                        return Response({
                            'success': True,
                            'message': f'自动分配说话人完成，成功更新{updated_count}个段落',
                            'updated_count': updated_count,
                            'trace_id': trace_id
                        })
                    else:
                        logger.warning(f"[自动分配说话人] 第{attempt + 1}次尝试解析失败，LLM返回格式无法识别")
                        if attempt == 1:  # 最后一次尝试
                            return Response({
                                'success': False,
                                'error': 'LLM返回格式无法解析，请检查项目角色配置是否正确',
                                'trace_id': trace_id
                            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        continue

                except requests.exceptions.Timeout:
                    logger.error(f"[自动分配说话人] 第{attempt + 1}次API调用超时")
                    if attempt == 1:
                        return Response({
                            'success': False,
                            'error': 'API调用超时，请稍后重试'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    logger.error(f"[自动分配说话人] 第{attempt + 1}次API调用异常: {str(e)}")
                    if attempt == 1:
                        return Response({
                            'success': False,
                            'error': f'API调用失败: {str(e)}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"[自动分配说话人] 处理失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'自动分配说话人失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _seconds_to_srt_time(self, seconds):
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    def _parse_speaker_assignment(self, llm_result, segments, speakers):
        """解析LLM返回的说话人分配结果"""
        try:
            import re

            # 提取"标注结果"部分
            result_pattern = r'标注结果：\s*\{(.*?)\}'
            result_match = re.search(result_pattern, llm_result, re.DOTALL)

            if not result_match:
                logger.error("[解析说话人] 未找到标注结果部分")
                return None

            result_content = result_match.group(1)

            # 解析每个段落的说话人分配
            # 格式示例：1\n00:00:27,100 --> 00:00:28,833 小张\n你是谁啊
            segment_pattern = r'(\d+)\s*\n[\d:,]+ --> [\d:,]+ ([^\n]+)\n'
            matches = re.findall(segment_pattern, result_content)

            if not matches:
                logger.error("[解析说话人] 未找到有效的段落-说话人匹配")
                return None

            # 构建段落ID到说话人的映射
            speaker_assignments = {}
            segments_by_index = {segment.index: segment for segment in segments}

            for index_str, speaker_name in matches:
                try:
                    index = int(index_str)
                    speaker_name = speaker_name.strip()

                    # 验证说话人名称是否在允许的列表中
                    if speaker_name not in speakers:
                        logger.warning(f"[解析说话人] 说话人'{speaker_name}'不在配置列表中: {speakers}")
                        continue

                    # 找到对应的段落
                    if index in segments_by_index:
                        segment = segments_by_index[index]
                        speaker_assignments[segment.id] = speaker_name
                    else:
                        logger.warning(f"[解析说话人] 段落索引{index}不存在")

                except (ValueError, AttributeError) as e:
                    logger.error(f"[解析说话人] 解析段落{index_str}失败: {str(e)}")
                    continue

            logger.info(f"[解析说话人] 成功解析{len(speaker_assignments)}个段落的说话人分配")
            return speaker_assignments

        except Exception as e:
            logger.error(f"[解析说话人] 解析异常: {str(e)}")
            return None

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
