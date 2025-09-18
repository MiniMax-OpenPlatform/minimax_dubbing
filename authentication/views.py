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
    """用户注册"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


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
        config, created = self.request.user.config.get_or_create(
            defaults={'user': self.request.user}
        )
        return config


@api_view(['POST'])
@permission_classes([AllowAny])
def test_auth(request):
    """测试认证接口"""
    group_id = request.data.get('group_id')
    api_key = request.data.get('api_key')

    if not group_id or not api_key:
        return Response({
            'error': 'group_id and api_key are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(group_id=group_id, api_key=api_key)
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'group_id': user.group_id
            }
        })
    except User.DoesNotExist:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


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
