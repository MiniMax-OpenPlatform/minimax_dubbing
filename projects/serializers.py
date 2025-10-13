"""
项目相关序列化器
"""
from rest_framework import serializers
from .models import Project
from segments.models import Segment


class ProjectListSerializer(serializers.ModelSerializer):
    """项目列表序列化器"""
    segment_count = serializers.ReadOnlyField()
    completed_segment_count = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    progress_stats = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'source_lang', 'target_lang', 'status',
            'created_at', 'updated_at', 'segment_count',
            'completed_segment_count', 'progress_percentage', 'progress_stats'
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    """项目详情序列化器"""
    segment_count = serializers.ReadOnlyField()
    completed_segment_count = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    audio_url = serializers.ReadOnlyField()
    video_url = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'source_lang', 'target_lang',
            'srt_file_path', 'video_file_path', 'concatenated_audio_url', 'tts_model',
            'voice_mappings', 'custom_vocabulary', 'max_speed', 'num_speakers', 'background_info', 'status',
            'created_at', 'updated_at', 'segment_count',
            'completed_segment_count', 'progress_percentage',
            'audio_url', 'video_url'
        ]


class ProjectCreateSerializer(serializers.ModelSerializer):
    """项目创建序列化器"""

    class Meta:
        model = Project
        fields = [
            'name', 'description', 'source_lang', 'target_lang',
            'tts_model', 'voice_mappings', 'custom_vocabulary', 'max_speed', 'num_speakers', 'background_info'
        ]

    def create(self, validated_data):
        # 设置用户
        validated_data['user'] = self.context['request'].user

        # 如果没有提供voice_mappings，设置默认值
        if 'voice_mappings' not in validated_data or not validated_data['voice_mappings']:
            validated_data['voice_mappings'] = [
                {"speaker": "SPEAKER_00", "voice_id": "female-tianmei"}
            ]

        return super().create(validated_data)


class SRTUploadSerializer(serializers.Serializer):
    """SRT文件上传序列化器"""
    srt_file = serializers.FileField()
    project_name = serializers.CharField(max_length=200, required=False)

    def validate_srt_file(self, value):
        """验证SRT文件"""
        if not value.name.endswith('.srt'):
            raise serializers.ValidationError("只支持.srt格式的文件")

        # 文件大小限制（1MB）
        if value.size > 1024 * 1024:
            raise serializers.ValidationError("文件大小不能超过1MB")

        return value