"""
段落管理视图
"""
import logging
from django.db import models
from django.db.models import Max
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Segment
from .serializers import (
    SegmentListSerializer, SegmentDetailSerializer,
    SegmentUpdateSerializer, SegmentCreateSerializer, BatchUpdateSerializer
)
from projects.models import Project
from services.business.segment_service import SegmentService
from services.business.simple_tts_service import SimpleTTSService
from services.business.translation_optimizer_service import TranslationOptimizerService

logger = logging.getLogger(__name__)


class SegmentViewSet(viewsets.ModelViewSet):
    """段落管理ViewSet"""
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 禁用分页，返回全部段落

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
        elif self.action == 'create':
            return SegmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SegmentUpdateSerializer
        else:
            return SegmentDetailSerializer

    def perform_create(self, serializer):
        """创建段落时自动设置项目并处理索引重排"""
        from django.db import transaction

        project_id = self.kwargs.get('project_pk')
        project = Project.objects.get(id=project_id, user=self.request.user)

        # 获取插入位置的索引
        insert_index = serializer.validated_data.get('index', 1)

        with transaction.atomic():
            # 方案：先将需要移动的段落index增加足够大的数避免冲突
            # 1. 获取所有需要移动的段落（插入位置及之后）
            segments_to_move = list(Segment.objects.filter(
                project=project,
                index__gte=insert_index
            ).order_by('index'))

            # 2. 先将它们的index都加上10000避免冲突
            for segment in segments_to_move:
                segment.index += 10000
                segment.save()

            # 3. 创建新段落
            new_segment = serializer.save(project=project, index=insert_index)

            # 4. 恢复移动段落的正确index（从插入位置+1开始）
            for i, segment in enumerate(segments_to_move):
                segment.index = insert_index + 1 + i
                segment.save()

    def destroy(self, request, *args, **kwargs):
        """删除段落并重新排列索引"""
        from django.db import transaction

        segment = self.get_object()
        project = segment.project
        deleted_index = segment.index

        with transaction.atomic():
            # 先删除段落
            response = super().destroy(request, *args, **kwargs)

            # 将被删除段落后面的所有段落index减1
            segments_to_move = Segment.objects.filter(
                project=project,
                index__gt=deleted_index
            )
            for segment in segments_to_move:
                segment.index -= 1
                segment.save()

        return response

    @action(detail=True, methods=['post'])
    def translate(self, request, project_pk=None, pk=None):
        """
        翻译单个段落
        """
        segment = self.get_object()
        service = SegmentService(user=request.user)

        result = service.translate_segment(
            segment=segment,
            api_key=request.user.api_key,
            group_id=request.user.group_id
        )

        if result['success']:
            return Response(result)
        else:
            return Response(
                {'error': result['error']},
                status=getattr(status, f'HTTP_{result["status_code"]}_BAD_REQUEST', status.HTTP_500_INTERNAL_SERVER_ERROR)
            )

    @action(detail=True, methods=['post'])
    def generate_tts(self, request, project_pk=None, pk=None):
        """
        生成单个段落的TTS音频（带时间戳对齐）
        """
        segment = self.get_object()
        service = SegmentService(user=request.user)

        result = service.generate_tts_for_segment(
            segment=segment,
            api_key=request.user.api_key,
            group_id=request.user.group_id
        )

        if result['success']:
            return Response(result)
        else:
            status_code = result.get('status_code', 500)
            if status_code == 400:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def simple_tts(self, request, project_pk=None, pk=None):
        """
        生成单个段落的简化TTS音频（不进行时间戳对齐）

        简化流程：
        1. 调用TTS API生成音频
        2. 去除前后静音并计算实际时长
        3. 计算ratio = t_tts / target_duration
        4. 如果ratio <= 1，则成功更新段落音频
        5. 如果ratio > 1，则失败，不更新段落音频
        """
        segment = self.get_object()
        service = SimpleTTSService(user=request.user)

        result = service.generate_simple_tts(
            segment=segment,
            api_key=request.user.api_key,
            group_id=request.user.group_id
        )

        if result['success']:
            return Response(result)
        else:
            status_code = result.get('status_code', 500)
            if status_code == 400:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        service = SegmentService(user=request.user)
        result = service.batch_update_segments(
            segments_queryset=self.get_queryset(),
            segment_ids=segment_ids,
            update_data=update_data
        )

        if result['success']:
            return Response(result)
        else:
            status_code = result.get('status_code', 500)
            if status_code == 404:
                return Response({'error': result['error']}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def batch_tts(self, request, project_pk=None):
        """
        批量生成TTS音频
        """
        project = Project.objects.get(id=project_pk, user=request.user)
        service = SegmentService(user=request.user)

        result = service.batch_generate_tts(
            project=project,
            segments_queryset=self.get_queryset(),
            api_key=request.user.api_key,
            group_id=request.user.group_id
        )

        if result['success']:
            return Response(result)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def shorten(self, request, project_pk=None, pk=None):
        """
        缩短段落翻译文本
        """
        segment = self.get_object()
        service = TranslationOptimizerService(user=request.user)

        # 从请求参数获取目标字符数，如果没有则自动计算
        target_char_count = request.data.get('target_char_count')
        if target_char_count:
            target_char_count = int(target_char_count)

        result = service.shorten_translation(
            segment=segment,
            api_key=request.user.api_key,
            group_id=request.user.group_id,
            target_char_count=target_char_count
        )

        if result['success']:
            return Response(result)
        else:
            status_code = result.get('status_code', 500)
            if status_code == 400:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            elif status_code == 422:
                return Response({'error': result['error']}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            else:
                return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def lengthen(self, request, project_pk=None, pk=None):
        """
        加长段落翻译文本
        """
        segment = self.get_object()
        service = TranslationOptimizerService(user=request.user)

        # 从请求参数获取目标字符数，如果没有则自动计算
        target_char_count = request.data.get('target_char_count')
        if target_char_count:
            target_char_count = int(target_char_count)

        result = service.lengthen_translation(
            segment=segment,
            api_key=request.user.api_key,
            group_id=request.user.group_id,
            target_char_count=target_char_count
        )

        if result['success']:
            return Response(result)
        else:
            status_code = result.get('status_code', 500)
            if status_code == 400:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            elif status_code == 422:
                return Response({'error': result['error']}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            else:
                return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
