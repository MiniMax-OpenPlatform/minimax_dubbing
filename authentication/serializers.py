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
            'dashscope_api_key',
            'aliyun_access_key_id',
            'aliyun_access_key_secret',
            'aliyun_app_key',
            'aliyun_asr_appkey',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""

    class Meta:
        model = User
        fields = ['username', 'group_id', 'api_key']
        extra_kwargs = {
            'api_key': {'write_only': True}
        }

    def create(self, validated_data):
        from django.db import transaction
        import logging

        logger = logging.getLogger(__name__)

        # 使用事务确保用户和配置都创建成功，或都不创建
        try:
            with transaction.atomic():
                # 设置默认密码（由于Django要求，但我们不使用密码认证）
                user = User.objects.create_user(
                    password='unused_password_123',
                    **validated_data
                )
                logger.info(f"用户创建成功: {user.username}@{user.group_id}")

                # 创建用户配置
                UserConfig.objects.create(user=user)
                logger.info(f"用户配置创建成功: {user.username}")

                return user
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            logger.error(f"验证数据: {validated_data}")
            import traceback
            logger.error(f"详细堆栈:\n{traceback.format_exc()}")
            raise  # 重新抛出异常，让Django REST框架处理