"""
段落管理视图
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Segment
from .serializers import (
    SegmentListSerializer, SegmentDetailSerializer,
    SegmentUpdateSerializer, BatchUpdateSerializer
)
from projects.models import Project
from services.business.segment_service import SegmentService
from services.business.simple_tts_service import SimpleTTSService

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
