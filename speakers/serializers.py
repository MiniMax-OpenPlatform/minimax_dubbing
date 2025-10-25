"""
说话人识别序列化器
"""
from rest_framework import serializers
from .models import SpeakerDiarizationTask, SpeakerProfile


class SpeakerProfileSerializer(serializers.ModelSerializer):
    """说话人档案序列化器"""

    class Meta:
        model = SpeakerProfile
        fields = [
            'id', 'speaker_id', 'name', 'role', 'gender',
            'face_count', 'segment_count', 'segments',
            'appearance', 'character_analysis',
            'representative_images', 'avg_confidence'
        ]


class SpeakerDiarizationTaskListSerializer(serializers.ModelSerializer):
    """说话人识别任务列表序列化器"""
    speaker_count = serializers.SerializerMethodField()

    class Meta:
        model = SpeakerDiarizationTask
        fields = [
            'id', 'project', 'status', 'progress', 'message',
            'num_speakers_detected', 'speaker_count',
            'is_applied', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_speaker_count(self, obj):
        """获取说话人数量"""
        return obj.speakers.count()


class SpeakerDiarizationTaskDetailSerializer(serializers.ModelSerializer):
    """说话人识别任务详情序列化器"""
    speakers = SpeakerProfileSerializer(many=True, read_only=True)

    class Meta:
        model = SpeakerDiarizationTask
        fields = [
            'id', 'project', 'status', 'progress', 'message',
            'num_speakers_detected', 'total_faces', 'valid_faces',
            'total_segments', 'clustering_params', 'filter_statistics',
            'vlm_trace_id', 'llm_trace_id', 'error_message',
            'is_applied', 'applied_at', 'speakers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SpeakerDiarizationTaskCreateSerializer(serializers.Serializer):
    """说话人识别任务创建序列化器"""
    project_id = serializers.UUIDField()

    def validate_project_id(self, value):
        """验证项目是否存在"""
        from projects.models import Project

        try:
            project = Project.objects.get(id=value)
        except Project.DoesNotExist:
            raise serializers.ValidationError("项目不存在")

        # 检查项目是否有视频文件
        if not project.video_file_path:
            raise serializers.ValidationError("项目没有视频文件，无法进行人脸识别")

        # 检查是否有segment
        if project.segments.count() == 0:
            raise serializers.ValidationError("项目没有字幕片段，无法进行说话人识别")

        return value


class ApplySpeakersSerializer(serializers.Serializer):
    """应用说话人分配结果序列化器"""
    task_id = serializers.UUIDField()

    def validate_task_id(self, value):
        """验证任务是否存在且已完成"""
        try:
            task = SpeakerDiarizationTask.objects.get(id=value)
        except SpeakerDiarizationTask.DoesNotExist:
            raise serializers.ValidationError("任务不存在")

        if task.status != 'completed':
            raise serializers.ValidationError("任务未完成，无法应用结果")

        return value
