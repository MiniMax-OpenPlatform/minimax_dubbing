"""
自定义认证类：基于group_id和api_key
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class GroupIDKeyAuthentication(BaseAuthentication):
    """
    基于group_id和api_key的认证
    """

    def authenticate(self, request):
        """
        认证逻辑
        从请求头或参数中获取group_id和api_key
        """
        # 从请求头获取认证信息
        group_id = request.META.get('HTTP_X_GROUP_ID') or request.GET.get('group_id')
        api_key = request.META.get('HTTP_X_API_KEY') or request.GET.get('api_key')

        if not group_id or not api_key:
            return None  # 未提供认证信息，让其他认证方式处理

        return self.authenticate_credentials(group_id, api_key)

    def authenticate_credentials(self, group_id, api_key):
        """
        验证凭据
        """
        try:
            user = User.objects.get(group_id=group_id, api_key=api_key)
        except User.DoesNotExist:
            logger.warning(f"认证失败: group_id={group_id}")
            raise AuthenticationFailed('Invalid group_id or api_key')

        if not user.is_active:
            raise AuthenticationFailed('User account is disabled')

        logger.info(f"用户认证成功: {user.username} ({group_id})")
        return (user, None)

    def authenticate_header(self, request):
        """
        返回认证头信息
        """
        return 'X-Group-ID and X-API-Key'