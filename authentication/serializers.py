"""
认证相关序列化器
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserConfig

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""

    class Meta:
        model = User
        fields = ['id', 'username', 'group_id', 'created_at', 'last_login']
        read_only_fields = ['id', 'created_at', 'last_login']


class UserConfigSerializer(serializers.ModelSerializer):
    """用户配置序列化器"""

    class Meta:
        model = UserConfig
        fields = [
            'api_endpoint',
            'aliyun_access_key_id',
            'aliyun_access_key_secret',
            'aliyun_app_key',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'aliyun_access_key_secret': {'write_only': True}  # 安全起见，secret只写不读
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""

    class Meta:
        model = User
        fields = ['username', 'group_id', 'api_key']
        extra_kwargs = {
            'api_key': {'write_only': True}
        }

    def create(self, validated_data):
        # 设置默认密码（由于Django要求，但我们不使用密码认证）
        user = User.objects.create_user(
            password='unused_password_123',
            **validated_data
        )

        # 创建用户配置
        UserConfig.objects.create(user=user)

        return user