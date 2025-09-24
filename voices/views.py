"""
音色管理API视图
"""
import logging
import requests
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Voice, VoiceQueryLog
from .serializers import VoiceSerializer

logger = logging.getLogger(__name__)


class VoiceViewSet(viewsets.ModelViewSet):
    """音色管理视图集"""

    serializer_class = VoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回当前用户的音色"""
        return Voice.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """重写list方法以支持无分页查询"""
        # 如果请求参数中有no_pagination=true，则不分页
        if request.query_params.get('no_pagination') == 'true':
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        # 否则使用默认分页
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def query_and_update(self, request):
        """查询并更新音色数据"""
        try:
            # 获取用户API密钥
            api_key = request.user.api_key
            if not api_key:
                return Response({
                    'success': False,
                    'message': '用户API密钥未配置'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 调用MiniMax API查询音色
            url = 'https://api.minimaxi.com/v1/get_voice'
            headers = {
                'authority': 'api.minimaxi.com',
                'Authorization': f'Bearer {api_key}',
                'content-type': 'application/json'
            }
            data = {'voice_type': 'all'}

            logger.info(f"用户 {request.user.username} 查询音色数据")
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code != 200:
                logger.error(f"MiniMax API调用失败: {response.status_code} - {response.text}")
                # 记录查询失败日志
                VoiceQueryLog.objects.create(
                    user=request.user,
                    total_count=0,
                    success=False,
                    error_message=f"API调用失败: {response.status_code}"
                )
                return Response({
                    'success': False,
                    'message': f'API调用失败: {response.status_code}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            voice_data = response.json()

            # 统计数据
            system_voices = voice_data.get('system_voice', [])
            voice_cloning = voice_data.get('voice_cloning', [])
            voice_generation = voice_data.get('voice_generation', [])

            total_count = len(system_voices) + len(voice_cloning) + len(voice_generation)

            # 记录查询成功日志
            VoiceQueryLog.objects.create(
                user=request.user,
                total_count=total_count,
                system_voice_count=len(system_voices),
                voice_cloning_count=len(voice_cloning),
                voice_generation_count=len(voice_generation),
                success=True
            )

            # 更新数据库中的音色数据
            updated_count = 0
            created_count = 0

            # 处理系统音色
            for voice in system_voices:
                voice_obj, created = Voice.objects.update_or_create(
                    voice_id=voice['voice_id'],
                    user=request.user,
                    defaults={
                        'voice_name': voice.get('voice_name', ''),
                        'voice_type': 'system_voice',
                        'description': voice.get('description', []),
                        'created_time': voice.get('created_time', ''),
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            # 处理音色克隆
            for voice in voice_cloning:
                voice_obj, created = Voice.objects.update_or_create(
                    voice_id=voice['voice_id'],
                    user=request.user,
                    defaults={
                        'voice_name': voice.get('voice_name', ''),
                        'voice_type': 'voice_cloning',
                        'description': voice.get('description', []),
                        'created_time': voice.get('created_time', ''),
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            # 处理音色生成
            for voice in voice_generation:
                voice_obj, created = Voice.objects.update_or_create(
                    voice_id=voice['voice_id'],
                    user=request.user,
                    defaults={
                        'voice_name': voice.get('voice_name', ''),
                        'voice_type': 'voice_generation',
                        'description': voice.get('description', []),
                        'created_time': voice.get('created_time', ''),
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            logger.info(f"音色数据更新完成: 新增 {created_count} 个，更新 {updated_count} 个")

            return Response({
                'success': True,
                'message': f'查询成功，新增 {created_count} 个音色，更新 {updated_count} 个音色',
                'data': {
                    'total_count': total_count,
                    'created_count': created_count,
                    'updated_count': updated_count,
                    'system_voice_count': len(system_voices),
                    'voice_cloning_count': len(voice_cloning),
                    'voice_generation_count': len(voice_generation)
                }
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            # 记录查询失败日志
            VoiceQueryLog.objects.create(
                user=request.user,
                total_count=0,
                success=False,
                error_message=f"网络请求异常: {str(e)}"
            )
            return Response({
                'success': False,
                'message': f'网络请求失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"查询音色数据异常: {str(e)}")
            # 记录查询失败日志
            VoiceQueryLog.objects.create(
                user=request.user,
                total_count=0,
                success=False,
                error_message=f"系统异常: {str(e)}"
            )
            return Response({
                'success': False,
                'message': f'系统异常: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def update_note(self, request, pk=None):
        """更新音色备注"""
        try:
            voice = self.get_object()
            user_note = request.data.get('user_note', '')

            voice.user_note = user_note
            voice.save()

            logger.info(f"用户 {request.user.username} 更新音色 {voice.voice_id} 备注")

            return Response({
                'success': True,
                'message': '备注更新成功',
                'data': self.get_serializer(voice).data
            })

        except Exception as e:
            logger.error(f"更新音色备注异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
