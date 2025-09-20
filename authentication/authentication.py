"""
自定义认证类：基于username + group_id + api_key三要素认证
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ThreeFactorAuthentication(BaseAuthentication):
    """
    基于username + group_id + api_key的三要素认证
    """

    def authenticate(self, request):
        """
        认证逻辑
        从请求头或参数中获取username、group_id和api_key
        """
        # 从请求头获取认证信息
        username = request.META.get('HTTP_X_USERNAME') or request.GET.get('username')
        group_id = request.META.get('HTTP_X_GROUP_ID') or request.GET.get('group_id')
        api_key = request.META.get('HTTP_X_API_KEY') or request.GET.get('api_key')

        if not username or not group_id or not api_key:
            return None  # 未提供完整认证信息，让其他认证方式处理

        return self.authenticate_credentials(username, group_id, api_key)

    def authenticate_credentials(self, username, group_id, api_key):
        """
        验证三要素凭据
        """
        try:
            user = User.objects.get(
                username=username,
                group_id=group_id,
                api_key=api_key
            )
        except User.DoesNotExist:
            logger.warning(f"认证失败: username={username}, group_id={group_id}")
            raise AuthenticationFailed('Invalid username, group_id or api_key')

        if not user.is_active:
            raise AuthenticationFailed('User account is disabled')

        logger.info(f"用户认证成功: {user.username} ({group_id})")
        return (user, None)

    def authenticate_header(self, request):
        """
        返回认证头信息
        """
        return 'X-Username, X-Group-ID and X-API-Key'


# 保留旧的认证类以兼容现有代码
class GroupIDKeyAuthentication(ThreeFactorAuthentication):
    """
    向后兼容的认证类，实际使用三要素认证
    """
    pass