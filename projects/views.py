"""
项目管理视图
"""
import logging
import os
from django.db import transaction, models
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

    @handle_business_logic_error
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_srt(self, request, pk=None):
        """
        为现有项目导入SRT文件，追加段落
        """
        project = self.get_object()

        if 'srt_file' not in request.FILES:
            raise ValidationError("请提供SRT文件")

        srt_file = request.FILES['srt_file']

        # 验证文件类型
        if not srt_file.name.lower().endswith('.srt'):
            raise ValidationError("只支持.srt格式的文件")

        # 验证文件大小 (10MB)
        if srt_file.size > 10 * 1024 * 1024:
            raise ValidationError("SRT文件大小不能超过10MB")

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

        # 获取当前项目的最大index
        max_index = Segment.objects.filter(project=project).aggregate(
            max_idx=models.Max('index')
        )['max_idx'] or 0

        # 创建段落
        with transaction.atomic():
            for i, segment_data in enumerate(segments_data):
                Segment.objects.create(
                    project=project,
                    index=max_index + i + 1,
                    start_time=segment_data['start_time'],
                    end_time=segment_data['end_time'],
                    original_text=segment_data['text'],
                    target_duration=segment_data['duration'],
                    status='pending'
                )

            logger.info(f"SRT导入成功: 项目{project.name}, 新增{len(segments_data)}个段落")

            return Response({
                'success': True,
                'project_id': project.id,
                'project_name': project.name,
                'segment_count': len(segments_data),
                'message': f'SRT文件导入成功，新增{len(segments_data)}个段落'
            }, status=status.HTTP_200_OK)

    @handle_business_logic_error
    @action(detail=True, methods=['post'])
    def separate_vocals(self, request, pk=None):
        """
        人声分离：从视频提取音频并分离人声和背景音
        """
        project = self.get_object()

        # 检查视频是否已上传
        if not project.video_file_path:
            raise ValidationError("请先上传视频文件")

        # 检查是否已在处理中
        if project.separation_status == 'processing':
            return Response({
                'success': False,
                'message': '人声分离正在进行中，请稍后查看结果'
            }, status=status.HTTP_200_OK)

        # 检查是否已完成
        if project.separation_status == 'completed':
            # 询问是否重新分离
            force = request.data.get('force', False)
            if not force:
                return Response({
                    'success': False,
                    'message': '已完成人声分离，如需重新分离请设置force=true'
                }, status=status.HTTP_200_OK)

        # 启动后台任务
        from .tasks import start_vocal_separation_task
        task_id = start_vocal_separation_task(project.id)

        logger.info(f"人声分离任务已启动: 项目{project.name}, 任务ID={task_id}")

        return Response({
            'success': True,
            'task_id': task_id,
            'project_id': project.id,
            'message': '人声分离任务已启动，处理中...（预计需要5-10分钟）'
        }, status=status.HTTP_200_OK)

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
        自动分配说话人（异步模式）- 立即返回task_id，后台执行
        """
        try:
            project = self.get_object()

            # 获取项目配置的角色数量
            num_speakers = project.num_speakers
            if num_speakers < 2:
                return Response({
                    'success': False,
                    'error': '角色数量至少需要2个才能进行自动分配，请在项目设置中修改'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取项目的所有段落
            segments = project.segments.filter(
                original_text__isnull=False
            ).exclude(original_text__exact='').order_by('index')

            if not segments.exists():
                return Response({
                    'success': False,
                    'error': '项目中没有可用的段落文本'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 创建任务ID
            import time
            import threading
            from django.utils import timezone

            task_id = f"auto_assign_speakers_{project.id}_{int(time.time())}"

            logger.info(f"自动分配说话人任务启动: {task_id}, 项目{project.id}, {segments.count()}个段落")

            # 保存用户API Key
            user_api_key = request.user.api_key

            # 异步执行任务
            def async_auto_assign_task():
                import requests
                import json
                import re
                from system_monitor.models import TaskMonitor
                from django.conf import settings

                try:
                    logger.info(f"[{task_id}] 开始异步自动分配说话人任务")

                    # 创建任务监控记录
                    monitor, created = TaskMonitor.objects.get_or_create(
                        task_id=task_id,
                        defaults={
                            'task_type': 'auto_assign_speakers',
                            'project_id': project.id,
                            'project_name': project.name,
                            'total_segments': segments.count(),
                            'start_time': timezone.now(),
                            'status': 'running',
                            'current_step': '准备调用LLM API...'
                        }
                    )

                    # 重新获取segments（因为在新线程中）
                    from segments.models import Segment
                    segments_list = list(Segment.objects.filter(
                        project_id=project.id,
                        original_text__isnull=False
                    ).exclude(original_text__exact='').order_by('index'))

                    # 构建对话内容
                    dialogue_lines = []
                    for segment in segments_list:
                        dialogue_lines.append(f"[{segment.index}] {segment.original_text}")

                    dialogue_content = '\n'.join(dialogue_lines)

                    # 获取背景信息
                    background_info = project.background_info or ''
                    background_section = f"\n\n背景信息：{background_info}\n" if background_info else "\n"

                    # 构建prompt
                    prompt_template = f"""你是一个专业的对话分析专家。请分析以下对话，识别出每句话是谁说的。

对话内容（共{len(segments_list)}句）：
{dialogue_content}

任务：
1. 分析对话结构，尤其要关注当前内容与上一句内容的逻辑关系，进而逐句递推人物关系
2. 这段对话中预计有{num_speakers}个说话人
3. 为每句话分配说话人ID（从1到{num_speakers}）
{background_section}
分析要点：
- 问答对通常是不同人
- 反问、质疑通常是对话转换
- 连续的陈述、补充通常是同一人

请输出JSON格式的结果：
{{
  "segments": [
    {{
      "index": 片段编号,
      "text": "片段内容",
      "analysis": "1）与上一句的对话逻辑关系（回答响应，连续陈述，无关联的新话题），2）综合其他背景信息推断说话人身份",
      "speaker_name": "给说话人命名",
      "speaker_id": 说话人ID（1到{num_speakers}之间的数字）
    }}
  ]
}}

只输出JSON，不要其他说明："""

                    url = getattr(settings, 'MINIMAX_API_URL', "https://api.minimaxi.com/v1/text/chatcompletion_v2")
                    headers = {
                        "Authorization": f"Bearer {user_api_key}",
                        "Content-Type": "application/json",
                        "Accept-Encoding": "identity"
                    }

                    payload = {
                        "model": "MiniMax-Text-01",
                        "stream": True,
                        "max_tokens": 20480,
                        "temperature": 0.01,
                        "messages": [
                            {"role": "system", "content": "你的任务是分析对话内容分配说话人"},
                            {"role": "user", "content": prompt_template}
                        ]
                    }

                    # 更新状态：调用LLM API
                    monitor.current_step = f'正在调用LLM API分析{len(segments_list)}个段落...'
                    monitor.save()

                    logger.info(f"[{task_id}] 开始调用LLM API (流式)")

                    # 流式请求
                    response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)

                    # 获取trace_id
                    trace_id = (response.headers.get('Trace-Id') or
                               response.headers.get('X-Trace-Id') or
                               response.headers.get('trace-id') or
                               'unknown')

                    logger.info(f"[{task_id}] 收到流式响应, trace_id: {trace_id}, status: {response.status_code}")

                    if response.status_code != 200:
                        monitor.status = 'failed'
                        monitor.error_message = f'LLM API返回错误: {response.status_code}'
                        monitor.end_time = timezone.now()
                        monitor.save()
                        return

                    # 更新状态：接收数据
                    monitor.current_step = f'正在接收LLM分析结果... (trace_id: {trace_id})'
                    monitor.save()

                    # 流式接收内容
                    full_content = ""
                    chunk_count = 0

                    for line in response.iter_lines():
                        if not line:
                            continue

                        line_str = line.decode('utf-8').strip()

                        if line_str.startswith('data: '):
                            data_str = line_str[6:]

                            if data_str == '[DONE]':
                                break

                            try:
                                data = json.loads(data_str)
                                chunk_count += 1

                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')

                                    if content:
                                        full_content += content

                                        # 每100个chunk更新一次进度
                                        if chunk_count % 100 == 0:
                                            monitor.current_step = f'正在接收数据... (已收到{chunk_count}个数据块)'
                                            monitor.save()

                            except json.JSONDecodeError:
                                pass

                    logger.info(f"[{task_id}] 流式传输完成，收到 {chunk_count} 个数据块，长度 {len(full_content)} 字符")
                    logger.info(f"[{task_id}] 内容前100字符: {repr(full_content[:100])}")
                    logger.info(f"[{task_id}] 内容后100字符: {repr(full_content[-100:])}")

                    # 更新状态：解析JSON
                    monitor.current_step = f'正在解析LLM返回的JSON数据...'
                    monitor.save()

                    # 解析JSON
                    try:
                        json_content = full_content.strip()

                        # 尝试提取代码块
                        json_pattern = r'```json\s*\n(.*?)\n```'
                        json_match = re.search(json_pattern, full_content, re.DOTALL)
                        if json_match:
                            json_content = json_match.group(1)
                        else:
                            code_block_pattern = r'```\s*\n(.*?)\n```'
                            code_match = re.search(code_block_pattern, full_content, re.DOTALL)
                            if code_match:
                                json_content = code_match.group(1)

                        # 清理可能的省略符号（LLM有时会输出 . . . 来表示省略）
                        # 这些省略符号会导致JSON解析失败
                        json_content = re.sub(r',\s*"\.\s*\.\s*\."', '', json_content)  # 移除 ". . ." 字段
                        json_content = re.sub(r'\.\s*\.\s*\.', '', json_content)  # 移除 . . .

                        data = json.loads(json_content)

                        if 'segments' not in data or not isinstance(data['segments'], list):
                            raise ValueError("JSON格式错误: 缺少segments字段")

                        logger.info(f"[{task_id}] 成功解析JSON，包含{len(data['segments'])}个段落")

                    except (json.JSONDecodeError, ValueError) as e:
                        # 保存失败的JSON内容到文件
                        debug_file = f'/tmp/llm_response_{task_id}.txt'
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(json_content)

                        logger.error(f"[{task_id}] JSON解析失败: {e}")
                        logger.error(f"[{task_id}] 完整内容已保存到: {debug_file}")
                        logger.error(f"[{task_id}] 错误位置附近内容: {json_content[max(0, 21877-50):min(len(json_content), 21877+50)]}...")

                        monitor.status = 'failed'
                        monitor.error_message = f'JSON解析失败: {str(e)} (内容已保存到{debug_file})'
                        monitor.end_time = timezone.now()
                        monitor.save()
                        return

                    # 更新状态：更新voice_mappings
                    monitor.current_step = '正在更新项目角色配置...'
                    monitor.save()

                    # 收集speaker_name
                    speaker_names_by_id = {}
                    for seg_data in data['segments']:
                        speaker_id = seg_data.get('speaker_id')
                        speaker_name = seg_data.get('speaker_name', '')
                        if speaker_id and speaker_name and speaker_id not in speaker_names_by_id:
                            speaker_names_by_id[speaker_id] = speaker_name

                    # 更新voice_mappings
                    default_voice_id = "female-tianmei"
                    new_voice_mappings = []
                    for speaker_id in range(1, num_speakers + 1):
                        speaker_name = speaker_names_by_id.get(speaker_id, f"角色{speaker_id}")
                        new_voice_mappings.append({
                            "speaker": speaker_name,
                            "voice_id": default_voice_id
                        })

                    project.voice_mappings = new_voice_mappings
                    project.save(update_fields=['voice_mappings'])

                    logger.info(f"[{task_id}] 已更新voice_mappings: {new_voice_mappings}")

                    # 更新状态：更新段落
                    monitor.current_step = f'正在更新{len(segments_list)}个段落的说话人信息...'
                    monitor.save()

                    # 构建segment映射
                    segments_by_index = {seg.index: seg for seg in segments_list}

                    updated_count = 0
                    for seg_data in data['segments']:
                        index = seg_data.get('index')
                        speaker_id = seg_data.get('speaker_id')

                        if index is None or speaker_id is None:
                            continue

                        speaker_index = int(speaker_id) - 1
                        if speaker_index < 0 or speaker_index >= len(new_voice_mappings):
                            continue

                        assigned_speaker = new_voice_mappings[speaker_index]['speaker']

                        if index in segments_by_index:
                            segment = segments_by_index[index]
                            segment.speaker = assigned_speaker
                            segment.save(update_fields=['speaker'])
                            updated_count += 1

                            # 每10个段落更新一次进度
                            if updated_count % 10 == 0:
                                monitor.completed_segments = updated_count
                                monitor.current_step = f'已更新 {updated_count}/{len(segments_list)} 个段落...'
                                monitor.save()

                    # 任务完成
                    monitor.status = 'completed'
                    monitor.completed_segments = updated_count
                    monitor.end_time = timezone.now()
                    monitor.current_step = f'完成！成功更新{updated_count}个段落'
                    monitor.save()

                    logger.info(f"[{task_id}] 自动分配说话人完成，成功更新{updated_count}个段落")

                except Exception as e:
                    logger.error(f"[{task_id}] 自动分配说话人任务失败: {str(e)}")
                    try:
                        monitor = TaskMonitor.objects.get(task_id=task_id)
                        monitor.status = 'failed'
                        monitor.error_message = str(e)
                        monitor.end_time = timezone.now()
                        monitor.save()
                    except:
                        pass

            # 启动后台线程
            threading.Thread(target=async_auto_assign_task, daemon=True).start()

            # 立即返回
            return Response({
                'success': True,
                'task_id': task_id,
                'total_segments': segments.count(),
                'message': f'自动分配说话人任务已启动，共{segments.count()}个段落'
            })

        except Exception as e:
            logger.error(f"启动自动分配说话人任务失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'启动任务失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def auto_assign_speakers_progress(self, request, pk=None):
        """
        获取自动分配说话人任务的进度
        """
        try:
            from system_monitor.models import TaskMonitor

            project = self.get_object()
            task_id = request.query_params.get('task_id')

            if not task_id:
                return Response({
                    'success': False,
                    'error': '缺少task_id参数'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                monitor = TaskMonitor.objects.get(task_id=task_id)

                progress = {
                    'status': monitor.status,
                    'total': monitor.total_segments,
                    'completed': monitor.completed_segments,
                    'current_step': monitor.current_step or '',
                    'error_message': monitor.error_message or ''
                }

                return Response({
                    'success': True,
                    'progress': progress
                })

            except TaskMonitor.DoesNotExist:
                return Response({
                    'success': False,
                    'error': '任务不存在或已过期'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"获取进度失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'获取进度失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _seconds_to_srt_time(self, seconds):
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    def _parse_speaker_assignment(self, llm_result, segments, project, trace_id='unknown'):
        """解析LLM返回的说话人分配结果（JSON格式），并更新项目的voice_mappings"""
        try:
            import re
            import json

            logger.info(f"[解析说话人][{trace_id}] 开始解析，项目配置的角色数量: {project.num_speakers}")

            # 提取JSON内容 - 尝试从各种markdown格式中提取
            json_content = llm_result.strip()

            # 尝试提取```json```代码块
            json_pattern = r'```json\s*\n(.*?)\n```'
            json_match = re.search(json_pattern, llm_result, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
                logger.info(f"[解析说话人][{trace_id}] 从```json```代码块中提取到JSON")
            else:
                # 尝试提取普通```代码块
                code_block_pattern = r'```\s*\n(.*?)\n```'
                code_match = re.search(code_block_pattern, llm_result, re.DOTALL)
                if code_match:
                    json_content = code_match.group(1)
                    logger.info(f"[解析说话人][{trace_id}] 从代码块中提取到内容")

            # 尝试解析JSON
            try:
                data = json.loads(json_content)
                logger.info(f"[解析说话人][{trace_id}] 成功解析JSON，包含{len(data.get('segments', []))}个段落")
            except json.JSONDecodeError as e:
                logger.error(f"[解析说话人][{trace_id}] JSON解析失败: {str(e)}")
                logger.error(f"[解析说话人][{trace_id}] 内容前500字符:\n{json_content[:500]}")
                return None

            # 验证JSON结构
            if 'segments' not in data or not isinstance(data['segments'], list):
                logger.error(f"[解析说话人][{trace_id}] JSON格式错误: 缺少segments字段或不是列表")
                return None

            # 收集所有LLM返回的speaker_name，按speaker_id分组
            speaker_names_by_id = {}  # {speaker_id: speaker_name}
            for seg_data in data['segments']:
                speaker_id = seg_data.get('speaker_id')
                speaker_name = seg_data.get('speaker_name', '')
                if speaker_id and speaker_name and speaker_id not in speaker_names_by_id:
                    speaker_names_by_id[speaker_id] = speaker_name

            logger.info(f"[解析说话人][{trace_id}] LLM识别出的角色: {speaker_names_by_id}")

            # 更新项目的voice_mappings
            # 使用默认音色ID "female-tianmei"
            default_voice_id = "female-tianmei"
            new_voice_mappings = []
            for speaker_id in range(1, project.num_speakers + 1):
                speaker_name = speaker_names_by_id.get(speaker_id, f"角色{speaker_id}")
                new_voice_mappings.append({
                    "speaker": speaker_name,
                    "voice_id": default_voice_id
                })

            project.voice_mappings = new_voice_mappings
            project.save(update_fields=['voice_mappings'])
            logger.info(f"[解析说话人][{trace_id}] 已更新项目voice_mappings: {new_voice_mappings}")

            # 构建段落分配结果
            segments_by_index = {segment.index: segment for segment in segments}
            speaker_assignments = {}

            for i, seg_data in enumerate(data['segments']):
                try:
                    index = seg_data.get('index')
                    speaker_id = seg_data.get('speaker_id')
                    speaker_name = seg_data.get('speaker_name', '')

                    if index is None or speaker_id is None:
                        logger.warning(f"[解析说话人][{trace_id}] 段落数据缺少index或speaker_id: {seg_data}")
                        continue

                    # speaker_id是1-based
                    speaker_index = int(speaker_id) - 1
                    if speaker_index < 0 or speaker_index >= len(new_voice_mappings):
                        logger.warning(f"[解析说话人][{trace_id}] speaker_id {speaker_id} 超出范围(1-{len(new_voice_mappings)})")
                        continue

                    # 使用新的voice_mappings中的speaker名称
                    assigned_speaker = new_voice_mappings[speaker_index]['speaker']

                    # 打印前3个和后3个的调试信息
                    if i < 3 or i >= len(data['segments']) - 3:
                        logger.info(f"[解析说话人][{trace_id}] 段落{index}: speaker_id={speaker_id}, speaker_name='{speaker_name}' -> {assigned_speaker}")

                    # 找到对应的段落
                    if index in segments_by_index:
                        segment = segments_by_index[index]
                        speaker_assignments[segment.id] = assigned_speaker
                    else:
                        logger.warning(f"[解析说话人][{trace_id}] 段落索引{index}不存在")

                except (ValueError, KeyError, AttributeError) as e:
                    logger.error(f"[解析说话人][{trace_id}] 解析段落数据失败: {seg_data}, 错误: {str(e)}")
                    continue

            logger.info(f"[解析说话人][{trace_id}] 成功解析{len(speaker_assignments)}个段落的说话人分配")
            return speaker_assignments

        except Exception as e:
            logger.error(f"[解析说话人][{trace_id}] 解析异常: {str(e)}")
            import traceback
            logger.error(f"[解析说话人][{trace_id}] 异常堆栈:\n{traceback.format_exc()}")
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

    @handle_business_logic_error
    @action(detail=True, methods=['post'])
    def asr_recognize(self, request, pk=None):
        """
        使用阿里云 FlashRecognizer 识别人声分离后的音频并导入项目（同步API）

        Request Body:
        {
            "source_language": "Chinese",      // 可选，源语言，默认使用项目设置
            "merge_short_segments": true,      // 是否合并短字幕，默认 true
            "min_duration": 0.5,               // 最小字幕时长（秒），默认 0.5
            "max_gap": 0.5                     // 最大间隔时间（秒），默认 0.5
        }

        Returns:
        {
            "success": true,
            "message": "识别成功，已导入 13 个字幕段落",
            "segments_count": 13
        }
        """
        import uuid
        trace_id = str(uuid.uuid4())[:8]

        try:
            project = self.get_object()
            user = request.user

            logger.info(f"[{trace_id}] 开始 ASR 识别: {project.name} (ID: {project.id})")

            # 检查项目是否已进行人声分离
            if project.separation_status != 'completed':
                return Response({
                    'success': False,
                    'error': '请先完成人声分离操作'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 检查vocals文件是否存在
            if not project.vocal_audio_path:
                return Response({
                    'success': False,
                    'error': '未找到人声分离后的音频文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 将 FileField 转换为实际文件路径字符串
            vocal_audio_path = project.vocal_audio_path.path
            if not os.path.exists(vocal_audio_path):
                return Response({
                    'success': False,
                    'error': f'人声音频文件不存在: {vocal_audio_path}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取用户的阿里云 NLS 配置
            user_config = user.config
            app_key = user_config.aliyun_app_key
            access_key_id = user_config.aliyun_access_key_id
            access_key_secret = user_config.aliyun_access_key_secret

            if not app_key or not access_key_id or not access_key_secret:
                return Response({
                    'success': False,
                    'error': '请先在账户设置中配置阿里云智能语音 NLS（需要 APP KEY、AccessKey ID 和 AccessKey Secret）'
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"[{trace_id}] 音频文件: {vocal_audio_path}")

            # 创建 FlashRecognizer 服务
            from services.asr import FlashRecognizerService

            recognizer = FlashRecognizerService(
                app_key=app_key,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                region='cn-shanghai'
            )

            # 确定音频格式
            file_ext = os.path.splitext(vocal_audio_path)[1].lower()
            format_map = {
                '.wav': 'wav',
                '.mp3': 'mp3',
                '.opus': 'opus',
                '.aac': 'aac',
                '.amr': 'amr',
                '.pcm': 'pcm'
            }
            audio_format = format_map.get(file_ext, 'wav')

            # 获取源语言并转换为阿里云语言代码
            source_language = request.data.get('source_language') or project.source_lang
            language_hint = FlashRecognizerService.get_language_hint(source_language)
            language_hints = [language_hint] if language_hint else None

            # 获取合并参数
            merge_short_segments = request.data.get('merge_short_segments', True)
            min_duration = float(request.data.get('min_duration', 0.5))
            max_gap = float(request.data.get('max_gap', 0.5))

            logger.info(f"[{trace_id}] 识别参数: language={source_language} ({language_hint}), merge={merge_short_segments}, min_duration={min_duration}s, max_gap={max_gap}s")

            # 执行识别并获取段落数据
            success, segments, error_msg = recognizer.recognize_and_create_segments(
                audio_file_path=vocal_audio_path,
                audio_format=audio_format,
                merge_short_segments=merge_short_segments,
                min_duration=min_duration,
                max_gap=max_gap,
                language_hints=language_hints
            )

            if not success:
                logger.error(f"[{trace_id}] ASR 识别失败: {error_msg}")
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not segments:
                logger.warning(f"[{trace_id}] ASR 识别结果为空")
                return Response({
                    'success': False,
                    'error': '识别结果为空，请检查音频文件是否包含有效语音内容'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 导入识别结果到数据库
            from segments.models import Segment

            # 删除现有的所有段落
            Segment.objects.filter(project=project).delete()

            # 批量创建新段落
            segment_objects = []
            for seg_data in segments:
                segment_objects.append(Segment(
                    project=project,
                    index=seg_data['index'],
                    start_time=seg_data['start_time'],
                    end_time=seg_data['end_time'],
                    original_text=seg_data['original_text'],
                    translated_text=seg_data.get('translated_text', ''),
                    speaker=seg_data.get('speaker', 'SPEAKER_00'),
                    target_duration=seg_data.get('duration', seg_data['end_time'] - seg_data['start_time']),
                    status='pending'
                ))

            Segment.objects.bulk_create(segment_objects)

            segments_count = len(segment_objects)
            logger.info(f"[{trace_id}] ASR 识别成功，已导入 {segments_count} 个字幕段落")

            return Response({
                'success': True,
                'message': f'识别成功，已导入 {segments_count} 个字幕段落',
                'segments_count': segments_count
            })

        except Exception as e:
            logger.error(f"[{trace_id}] ASR 识别失败: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'识别失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @handle_business_logic_error
    @action(detail=True, methods=['post'])
    def synthesize_video(self, request, pk=None):
        """
        合成最终视频：混合翻译音频和背景音，然后与原始视频合并

        工作流程:
        1. 混合翻译音频（拼接后的完整TTS音频）和背景音
        2. 将混合音频替换原始视频的音轨
        3. 生成最终翻译视频

        Request Body:
        {
            "translated_volume": 1.0,    // 翻译音频音量（0.0-1.0），默认 1.0
            "background_volume": 0.3     // 背景音音量（0.0-1.0），默认 0.3
        }

        Returns:
        {
            "success": true,
            "message": "视频合成成功",
            "mixed_audio_url": "http://...",
            "final_video_url": "http://..."
        }
        """
        import uuid
        from django.conf import settings
        from services.audio_processor import AudioProcessor
        from services.video_processor import VideoProcessor
        from django.core.files import File

        project = self.get_object()
        trace_id = str(uuid.uuid4())[:8]

        try:
            logger.info(f"[{trace_id}] 开始视频合成: {project.name} (ID: {project.id})")

            # 1. 检查必需的文件
            if not project.concatenated_audio_url:
                return Response({
                    'success': False,
                    'error': '请先拼接翻译音频（批量TTS后点击"拼接音频"）'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not project.background_audio_path:
                return Response({
                    'success': False,
                    'error': '未找到背景音文件，请先进行人声分离'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not project.video_file_path:
                return Response({
                    'success': False,
                    'error': '未找到原始视频文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取参数
            translated_volume = float(request.data.get('translated_volume', 1.0))
            background_volume = float(request.data.get('background_volume', 0.3))

            logger.info(f"[{trace_id}] 音量参数: 翻译={translated_volume}, 背景={background_volume}")

            # 2. 准备文件路径
            # 翻译音频URL转本地路径
            concatenated_audio_url = project.concatenated_audio_url
            if concatenated_audio_url.startswith('http'):
                # 从URL中提取相对路径
                from urllib.parse import urlparse
                parsed = urlparse(concatenated_audio_url)
                relative_path = parsed.path.lstrip('/')
                if relative_path.startswith('media/'):
                    relative_path = relative_path[6:]  # 去掉 'media/' 前缀
                translated_audio_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            else:
                # 已经是相对路径
                translated_audio_path = os.path.join(settings.MEDIA_ROOT, concatenated_audio_url.lstrip('/'))

            background_audio_path = project.background_audio_path.path
            video_path = project.video_file_path.path

            logger.info(f"[{trace_id}] 翻译音频: {translated_audio_path}")
            logger.info(f"[{trace_id}] 背景音: {background_audio_path}")
            logger.info(f"[{trace_id}] 原始视频: {video_path}")

            # 检查文件存在性
            if not os.path.exists(translated_audio_path):
                return Response({
                    'success': False,
                    'error': f'翻译音频文件不存在: {translated_audio_path}'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not os.path.exists(background_audio_path):
                return Response({
                    'success': False,
                    'error': f'背景音文件不存在: {background_audio_path}'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not os.path.exists(video_path):
                return Response({
                    'success': False,
                    'error': f'视频文件不存在: {video_path}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 3. 混合音频
            logger.info(f"[{trace_id}] 步骤 1/2: 混合音频轨道")

            audio_processor = AudioProcessor()
            mixed_audio_filename = f"project_{project.id}_mixed_{trace_id}.mp3"
            mixed_audio_path = os.path.join(settings.MEDIA_ROOT, 'audio', 'mixed', mixed_audio_filename)

            # 确保目录存在
            os.makedirs(os.path.dirname(mixed_audio_path), exist_ok=True)

            success = audio_processor.mix_audio_tracks(
                translated_audio_path=translated_audio_path,
                background_audio_path=background_audio_path,
                output_path=mixed_audio_path,
                translated_volume=translated_volume,
                background_volume=background_volume,
                trace_id=trace_id
            )

            if not success:
                return Response({
                    'success': False,
                    'error': '音频混合失败'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 保存混合音频路径
            with open(mixed_audio_path, 'rb') as f:
                project.mixed_audio_path.save(mixed_audio_filename, File(f), save=False)

            logger.info(f"[{trace_id}] 音频混合完成")

            # 4. 合成视频
            logger.info(f"[{trace_id}] 步骤 2/2: 合成最终视频")

            video_processor = VideoProcessor()

            # 检查 ffmpeg
            if not video_processor.check_ffmpeg():
                return Response({
                    'success': False,
                    'error': 'ffmpeg 未安装或不可用'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            final_video_filename = f"project_{project.id}_final_{trace_id}.mp4"
            final_video_path = os.path.join(settings.MEDIA_ROOT, 'videos', 'final', final_video_filename)

            # 确保目录存在
            os.makedirs(os.path.dirname(final_video_path), exist_ok=True)

            success, error_msg = video_processor.replace_audio(
                video_path=video_path,
                audio_path=mixed_audio_path,
                output_path=final_video_path,
                trace_id=trace_id
            )

            if not success:
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 保存最终视频路径
            with open(final_video_path, 'rb') as f:
                project.final_video_path.save(final_video_filename, File(f), save=False)

            project.save()

            logger.info(f"[{trace_id}] 视频合成成功")

            # 生成访问URL
            mixed_audio_url = request.build_absolute_uri(project.mixed_audio_path.url)
            final_video_url = request.build_absolute_uri(project.final_video_path.url)

            return Response({
                'success': True,
                'message': '视频合成成功',
                'mixed_audio_url': mixed_audio_url,
                'final_video_url': final_video_url
            })

        except Exception as e:
            logger.error(f"[{trace_id}] 视频合成失败: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'视频合成失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
