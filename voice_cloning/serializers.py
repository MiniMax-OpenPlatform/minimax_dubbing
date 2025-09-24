"""
音色克隆序列化器
"""
from rest_framework import serializers
from .models import VoiceCloneRecord


class VoiceCloneSerializer(serializers.ModelSerializer):
    """音色克隆序列化器"""

    class Meta:
        model = VoiceCloneRecord
        fields = [
            'id', 'voice_id', 'clone_audio_file_id', 'prompt_audio_file_id',
            'prompt_text', 'test_text', 'model', 'need_noise_reduction',
            'need_volume_normalization', 'status', 'demo_audio_url',
            'error_message', 'trace_id', 'created_at', 'updated_at',
            'clone_audio_file', 'prompt_audio_file', 'demo_audio_file'
        ]
        read_only_fields = ['id', 'status', 'demo_audio_url', 'error_message', 'trace_id', 'created_at', 'updated_at', 'clone_audio_file', 'prompt_audio_file', 'demo_audio_file']


class VoiceCloneCreateSerializer(serializers.Serializer):
    """音色克隆创建序列化器"""

    voice_id = serializers.CharField(max_length=200, help_text="音色ID")
    test_text = serializers.CharField(help_text="试听文本")
    model = serializers.CharField(
        max_length=50,
        default="speech-2.5-hd-preview",
        help_text="试听模型"
    )
    prompt_text = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Prompt文本（当使用prompt音频时必选）"
    )
    need_noise_reduction = serializers.BooleanField(
        default=False,
        help_text="是否开启降噪"
    )
    need_volume_normalization = serializers.BooleanField(
        default=False,
        help_text="是否开启音量归一化"
    )

    def validate(self, data):
        """验证数据"""
        # 如果有prompt_text但没有prompt音频文件，这里先放过，在view中处理文件验证
        return data