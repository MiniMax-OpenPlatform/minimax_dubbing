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
        fields = ['api_endpoint', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'group_id', 'api_key', 'password']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)

        # 创建用户配置
        UserConfig.objects.create(user=user)

        return user