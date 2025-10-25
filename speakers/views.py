"""
说话人识别视图
"""
import logging
import os
import threading
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SpeakerDiarizationTask, SpeakerProfile
from projects.models import Project
from segments.models import Segment
from .serializers import (
    SpeakerDiarizationTaskListSerializer,
    SpeakerDiarizationTaskDetailSerializer,
    SpeakerDiarizationTaskCreateSerializer,
    ApplySpeakersSerializer
)
from services.speaker_diarization.pipeline import process_speaker_diarization
from backend.exceptions import ValidationError, handle_business_logic_error

logger = logging.getLogger(__name__)


class SpeakerDiarizationTaskViewSet(viewsets.ModelViewSet):
    """说话人识别任务ViewSet"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回当前用户的任务，支持按project_id过滤"""
        queryset = SpeakerDiarizationTask.objects.filter(
            project__user=self.request.user
        ).select_related('project').prefetch_related('speakers')

        # 如果传入了project_id参数，只返回该项目的任务
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return SpeakerDiarizationTaskListSerializer
        elif self.action == 'create':
            return SpeakerDiarizationTaskCreateSerializer
        else:
            return SpeakerDiarizationTaskDetailSerializer

    @handle_business_logic_error
    def create(self, request, *args, **kwargs):
        """创建并启动说话人识别任务"""
        serializer = SpeakerDiarizationTaskCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError("参数验证失败", details=serializer.errors)

        project_id = serializer.validated_data['project_id']

        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            raise ValidationError("项目不存在或无权限访问")

        # 检查是否已有进行中的任务
        existing_task = SpeakerDiarizationTask.objects.filter(
            project=project,
            status__in=['pending', 'running']
        ).first()

        if existing_task:
            raise ValidationError("该项目已有进行中的说话人识别任务")

        # 创建任务
        task = SpeakerDiarizationTask.objects.create(
            project=project,
            status='pending',
            progress=0,
            message='准备开始...'
        )

        logger.info(f"创建说话人识别任务: {task.id}, 项目: {project.name}")

        # 获取用户的DashScope API Key
        dashscope_api_key = None
        if hasattr(request.user, 'config') and request.user.config:
            dashscope_api_key = request.user.config.dashscope_api_key

        # 启动后台线程执行任务
        thread = threading.Thread(
            target=self._run_diarization_task,
            args=(task.id, project.id, dashscope_api_key)
        )
        thread.daemon = True
        thread.start()

        # 返回任务信息
        return Response(
            SpeakerDiarizationTaskDetailSerializer(task).data,
            status=status.HTTP_201_CREATED
        )

    def _run_diarization_task(self, task_id, project_id, api_key):
        """在后台线程中执行说话人识别任务"""
        try:
            task = SpeakerDiarizationTask.objects.get(id=task_id)
            project = Project.objects.get(id=project_id)

            # 更新状态为运行中
            task.status = 'running'
            task.save(update_fields=['status'])

            logger.info(f"开始执行说话人识别任务: {task_id}")

            # 准备输出目录
            output_dir = os.path.join('media', 'speaker_diarization', str(task_id))
            os.makedirs(output_dir, exist_ok=True)

            # 获取视频路径
            video_path = project.video_file_path.path if project.video_file_path else None
            if not video_path or not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")

            # 获取segments
            segments = project.segments.all().order_by('index')

            # 定义进度回调
            def progress_callback(progress, msg):
                task.progress = progress
                task.message = msg
                task.save(update_fields=['progress', 'message'])
                logger.info(f"任务 {task_id} 进度: {progress}% - {msg}")

            # 执行Pipeline
            result = process_speaker_diarization(
                video_path=video_path,
                segments=segments,
                output_dir=output_dir,
                dashscope_api_key=api_key,
                progress_callback=progress_callback
            )

            if result['success']:
                # 保存结果到数据库
                with transaction.atomic():
                    task.status = 'completed'
                    task.progress = 100
                    task.message = f"识别完成！检测到 {result['num_speakers']} 个说话人"
                    task.num_speakers_detected = result['num_speakers']
                    task.total_faces = result.get('total_faces', 0)
                    task.valid_faces = result.get('valid_faces', 0)
                    task.total_segments = result.get('total_segments', 0)
                    task.clustering_params = result.get('clustering_params', {})
                    task.filter_statistics = result.get('filter_statistics', {})
                    task.vlm_trace_id = result.get('vlm_trace_id')  # 阿里云API不提供trace_id，允许为None
                    task.llm_trace_id = result.get('llm_trace_id')  # 阿里云API不提供trace_id，允许为None
                    task.save()

                    # 创建说话人档案
                    for speaker_id, speaker_data in result['speakers'].items():
                        # 图片路径添加任务ID前缀，使其相对于media目录
                        relative_images = speaker_data.get('representative_images', [])
                        media_relative_images = [
                            f"speaker_diarization/{task_id}/{img}" for img in relative_images
                        ]

                        SpeakerProfile.objects.create(
                            task=task,
                            speaker_id=speaker_id,
                            name=speaker_data.get('name', f'说话人{speaker_id}'),
                            role=speaker_data.get('role', ''),
                            gender=speaker_data.get('gender', ''),
                            face_count=speaker_data.get('face_count', 0),
                            segment_count=speaker_data.get('segment_count', 0),
                            segments=speaker_data.get('segments', []),
                            appearance=speaker_data.get('appearance', {}),
                            character_analysis=speaker_data.get('character_analysis', {}),
                            representative_images=media_relative_images,
                            avg_confidence=speaker_data.get('avg_confidence', 0.0)
                        )

                logger.info(f"任务 {task_id} 执行成功，识别出 {result['num_speakers']} 个说话人")

                # 自动应用识别结果到项目
                logger.info(f"任务 {task_id} 开始自动应用识别结果...")
                try:
                    # 使用ViewSet实例调用内部方法
                    viewset = SpeakerDiarizationTaskViewSet()
                    viewset._apply_task_results(task)
                    logger.info(f"任务 {task_id} 识别结果已自动应用到项目")
                except Exception as apply_error:
                    logger.error(f"任务 {task_id} 自动应用结果失败: {str(apply_error)}", exc_info=True)
                    # 应用失败不影响识别任务的成功状态

            else:
                # 任务失败
                task.status = 'failed'
                task.error_message = result.get('error', '未知错误')
                task.save(update_fields=['status', 'error_message'])
                logger.error(f"任务 {task_id} 执行失败: {task.error_message}")

        except Exception as e:
            logger.error(f"任务 {task_id} 执行异常: {str(e)}", exc_info=True)
            try:
                task = SpeakerDiarizationTask.objects.get(id=task_id)
                task.status = 'failed'
                task.error_message = str(e)
                task.save(update_fields=['status', 'error_message'])
            except Exception as save_error:
                logger.error(f"保存任务错误状态失败: {str(save_error)}")

    @handle_business_logic_error
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """获取任务进度"""
        task = self.get_object()
        return Response({
            'task_id': str(task.id),
            'status': task.status,
            'progress': task.progress,
            'message': task.message
        })

    def _apply_task_results(self, task):
        """
        内部方法：应用任务结果到项目

        Args:
            task: SpeakerDiarizationTask实例
        """
        if task.status != 'completed':
            logger.warning(f"任务 {task.id} 状态为 {task.status}，无法应用结果")
            return

        if task.is_applied:
            logger.info(f"任务 {task.id} 结果已经应用过了，跳过")
            return

        # 将说话人分配结果应用到Segment模型
        with transaction.atomic():
            project = task.project
            default_voice_id = 'female-tianmei'  # 默认音色

            # 1. 完全覆盖所有片段的speaker字段（清空未分配的片段）
            # 先将所有片段的speaker设为空
            project.segments.all().update(speaker='')

            # 2. 根据每个SpeakerProfile的segments列表更新Segment的speaker字段
            for speaker_profile in task.speakers.all():
                speaker_name = speaker_profile.name
                segment_indices = speaker_profile.segments

                # 批量更新这些片段的speaker字段
                for seg_index in segment_indices:
                    try:
                        segment = project.segments.get(index=seg_index)
                        segment.speaker = speaker_name
                        segment.save(update_fields=['speaker'])
                    except Segment.DoesNotExist:
                        logger.warning(f"片段 {seg_index} 不存在，跳过")
                        continue

            # 3. 完全替换项目的voice_mappings（删除默认的SPEAKER_00等）
            new_voice_mappings = []
            for speaker_profile in task.speakers.all():
                speaker_name = speaker_profile.name
                new_voice_mappings.append({
                    'speaker': speaker_name,
                    'voice_id': default_voice_id
                })
                logger.info(f"添加说话人 '{speaker_name}' 到voice_mappings，默认音色: {default_voice_id}")

            project.voice_mappings = new_voice_mappings

            # 4. 标记任务为已应用
            task.is_applied = True
            task.applied_at = timezone.now()
            task.save(update_fields=['is_applied', 'applied_at'])

            # 5. 更新Project的current_diarization_task和voice_mappings
            project.current_diarization_task = task
            project.save(update_fields=['current_diarization_task', 'voice_mappings'])

            logger.info(f"任务 {task.id} 应用完成：替换了 {len(new_voice_mappings)} 个说话人配置")

        logger.info(f"任务 {task.id} 结果已应用到项目 {task.project.id}")

    @handle_business_logic_error
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """应用说话人分配结果到项目的segments（API endpoint，已废弃但保留兼容性）"""
        task = self.get_object()

        if task.status != 'completed':
            raise ValidationError("任务未完成，无法应用结果")

        if task.is_applied:
            raise ValidationError("该任务结果已经应用过了")

        # 调用内部方法应用结果
        self._apply_task_results(task)

        return Response({
            'message': '说话人分配结果已应用',
            'task_id': str(task.id)
        })

    @handle_business_logic_error
    @action(detail=True, methods=['delete'])
    def cancel(self, request, pk=None):
        """取消正在运行的任务"""
        task = self.get_object()

        if task.status not in ['pending', 'running']:
            raise ValidationError("只能取消未完成的任务")

        # 注意：由于使用Threading，无法真正停止线程
        # 只能标记为cancelled，线程会继续执行但不会保存结果
        task.status = 'cancelled'
        task.error_message = '用户取消'
        task.save(update_fields=['status', 'error_message'])

        logger.info(f"任务 {task.id} 已被取消")

        return Response({'message': '任务已取消'})
