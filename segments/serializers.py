"""
段落相关序列化器
"""
from rest_framework import serializers
from .models import Segment


class SegmentListSerializer(serializers.ModelSerializer):
    """段落列表序列化器"""
    time_display = serializers.ReadOnlyField()
    duration = serializers.ReadOnlyField()
    is_aligned = serializers.ReadOnlyField()

    class Meta:
        model = Segment
        fields = [
            'id', 'index', 'start_time', 'end_time', 'time_display',
            'duration', 'speaker', 'original_text', 'translated_text',
            'voice_id', 'emotion', 'speed', 'translated_audio_url',
            't_tts_duration', 'target_duration', 'ratio', 'is_aligned',
            'status', 'updated_at'
        ]


class SegmentDetailSerializer(serializers.ModelSerializer):
    """段落详情序列化器"""
    time_display = serializers.ReadOnlyField()
    duration = serializers.ReadOnlyField()
    is_aligned = serializers.ReadOnlyField()

    class Meta:
        model = Segment
        fields = [
            'id', 'index', 'start_time', 'end_time', 'time_display',
            'duration', 'speaker', 'original_text', 'translated_text',
            'voice_id', 'emotion', 'speed', 'original_audio_url',
            'translated_audio_url', 't_tts_duration', 'target_duration',
            'ratio', 'is_aligned', 'status', 'created_at', 'updated_at'
        ]


class SegmentUpdateSerializer(serializers.ModelSerializer):
    """段落更新序列化器"""

    class Meta:
        model = Segment
        fields = [
            'start_time', 'end_time', 'speaker', 'original_text',
            'translated_text', 'voice_id', 'emotion', 'speed'
        ]

    def update(self, instance, validated_data):
        # 如果修改了翻译文本或TTS参数，重置音频状态
        if ('translated_text' in validated_data or
            'voice_id' in validated_data or
            'emotion' in validated_data or
            'speed' in validated_data):
            instance.translated_audio_url = ''
            instance.t_tts_duration = None
            instance.ratio = None
            if instance.status in ['completed', 'tts_processing']:
                instance.status = 'translated'

        return super().update(instance, validated_data)


class BatchUpdateSerializer(serializers.Serializer):
    """批量更新序列化器"""
    segment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    speaker = serializers.CharField(max_length=50, required=False)
    voice_id = serializers.CharField(max_length=100, required=False)
    emotion = serializers.ChoiceField(
        choices=Segment.EMOTION_CHOICES,
        required=False
    )
    speed = serializers.FloatField(min_value=0.01, max_value=2.0, required=False)

    def validate_segment_ids(self, value):
        """验证段落ID"""
        if not value:
            raise serializers.ValidationError("段落ID列表不能为空")
        return value