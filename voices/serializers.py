"""
音色管理序列化器
"""
from rest_framework import serializers
from .models import Voice, VoiceQueryLog


class VoiceSerializer(serializers.ModelSerializer):
    """音色序列化器"""

    voice_type_display = serializers.CharField(source='get_voice_type_display', read_only=True)
    description_text = serializers.SerializerMethodField()

    class Meta:
        model = Voice
        fields = [
            'id', 'voice_id', 'voice_name', 'voice_type', 'voice_type_display',
            'description', 'description_text', 'user_note', 'created_time',
            'updated_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_description_text(self, obj):
        """将描述列表转换为文本"""
        if isinstance(obj.description, list) and obj.description:
            return ' | '.join(obj.description)
        return ''


class VoiceQueryLogSerializer(serializers.ModelSerializer):
    """音色查询日志序列化器"""

    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = VoiceQueryLog
        fields = [
            'id', 'username', 'query_time', 'total_count',
            'system_voice_count', 'voice_cloning_count', 'voice_generation_count',
            'success', 'error_message'
        ]
        read_only_fields = ['id', 'query_time']