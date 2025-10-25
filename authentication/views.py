"""
认证相关视图
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserConfigSerializer, UserRegistrationSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """用户注册 - 通过验证group_id和api_key的LLM访问权限"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        from services.clients.minimax_client import MiniMaxClient
        import logging

        logger = logging.getLogger(__name__)

        # 先验证API访问权限
        username = request.data.get('username')
        group_id = request.data.get('group_id')
        api_key = request.data.get('api_key')

        if not username or not group_id or not api_key:
            return Response({
                'detail': '用户名、Group ID和API Key都是必填项'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 验证API Key是否有效（测试LLM访问）
        try:
            client = MiniMaxClient(api_key=api_key, group_id=group_id)
            # 进行一个简单的API测试调用
            test_result = client.translate(
                text="测试",
                target_language="English"
            )

            if not test_result.get('success'):
                return Response({
                    'detail': 'API Key验证失败，无法访问MiniMax服务'
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"API Key验证成功: {username}@{group_id}")

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"API Key验证失败: {str(e)}")
            logger.error(f"详细错误堆栈:\n{error_trace}")
            print(f"[注册验证错误] {str(e)}")
            print(f"[详细堆栈]\n{error_trace}")
            return Response({
                'detail': f'API Key验证失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # API验证通过，调用父类创建用户
        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            response.data['message'] = '注册成功，API Key验证通过'
            logger.info(f"新用户注册成功: {username}@{group_id}")

        return response


class UserProfileView(generics.RetrieveUpdateAPIView):
    """用户个人信息"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserConfigView(generics.RetrieveUpdateAPIView):
    """用户配置"""
    serializer_class = UserConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        from .models import UserConfig
        config, created = UserConfig.objects.get_or_create(
            user=self.request.user
        )
        return config


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_auth(request):
    """测试三要素认证接口"""
    user = request.user
    return Response({
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'group_id': user.group_id,
            'created_at': user.created_at,
            'last_login': user.last_login
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """用户统计信息"""
    user = request.user
    return Response({
        'user_info': {
            'username': user.username,
            'group_id': user.group_id,
            'created_at': user.created_at,
        },
        'project_stats': {
            'total_projects': user.projects.count(),
            'active_projects': user.projects.filter(status='processing').count(),
            'completed_projects': user.projects.filter(status='completed').count(),
        }
    })
