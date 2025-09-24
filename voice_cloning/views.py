"""
音色克隆API视图
"""
import logging
import requests
import json
import os
from urllib.parse import urlparse
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import VoiceCloneRecord
from .serializers import VoiceCloneSerializer, VoiceCloneCreateSerializer

logger = logging.getLogger(__name__)


class VoiceCloneViewSet(viewsets.ModelViewSet):
    """音色克隆视图集"""

    serializer_class = VoiceCloneSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """只返回当前用户的克隆记录"""
        return VoiceCloneRecord.objects.filter(user=self.request.user)

    def save_uploaded_file(self, uploaded_file, purpose):
        """保存上传的文件到本地存储"""
        try:
            # 获取文件扩展名
            file_name = uploaded_file.name
            file_ext = os.path.splitext(file_name)[1]

            # 根据用途和时间戳生成唯一文件名
            import time
            timestamp = str(int(time.time()))
            user_id = self.request.user.id
            saved_name = f"{user_id}_{purpose}_{timestamp}{file_ext}"

            # 根据用途确定保存路径
            if purpose == 'voice_clone':
                folder = 'voice_clone/clone_audio/'
            elif purpose == 'prompt_audio':
                folder = 'voice_clone/prompt_audio/'
            else:
                folder = 'voice_clone/other/'

            # 读取文件内容并重置文件指针
            file_content = uploaded_file.read()
            uploaded_file.seek(0)  # 重置文件指针到开始位置

            # 保存文件
            file_path = os.path.join(folder, saved_name)
            saved_path = default_storage.save(file_path, ContentFile(file_content))

            logger.info(f"文件保存成功: {saved_path}")
            # 返回相对路径而不是完整URL
            return saved_path

        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return None

    def download_and_save_demo_audio(self, demo_audio_url, voice_id):
        """下载并保存试听音频"""
        if not demo_audio_url:
            return None

        try:
            # 下载音频文件
            response = requests.get(demo_audio_url, timeout=60)
            if response.status_code != 200:
                logger.error(f"下载试听音频失败: {response.status_code}")
                return None

            # 从URL解析文件扩展名，默认使用.mp3
            parsed_url = urlparse(demo_audio_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.mp3'

            # 生成文件名
            import time
            timestamp = str(int(time.time()))
            user_id = self.request.user.id
            saved_name = f"{user_id}_demo_{voice_id}_{timestamp}{file_ext}"

            # 保存路径
            folder = 'voice_clone/demo_audio/'
            file_path = os.path.join(folder, saved_name)
            saved_path = default_storage.save(file_path, ContentFile(response.content))

            logger.info(f"试听音频保存成功: {saved_path}")
            return saved_path

        except Exception as e:
            logger.error(f"下载保存试听音频失败: {str(e)}")
            return None

    @action(detail=False, methods=['post'])
    def upload_file(self, request):
        """上传文件到MiniMax"""
        try:
            # 获取用户API密钥和group_id
            api_key = request.user.api_key
            group_id = request.user.group_id

            if not api_key or not group_id:
                return Response({
                    'success': False,
                    'message': '用户API密钥或Group ID未配置'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取文件和用途
            file = request.FILES.get('file')
            purpose = request.data.get('purpose', 'voice_clone')

            if not file:
                return Response({
                    'success': False,
                    'message': '请选择要上传的文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证用途
            if purpose not in ['voice_clone', 'prompt_audio']:
                return Response({
                    'success': False,
                    'message': '无效的文件用途'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 保存文件到本地存储
            local_file_path = self.save_uploaded_file(file, purpose)
            if not local_file_path:
                return Response({
                    'success': False,
                    'message': '保存文件到本地失败'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 调用MiniMax文件上传API
            url = f'https://api.minimaxi.com/v1/files/upload?GroupId={group_id}'
            headers = {
                'authority': 'api.minimaxi.com',
                'Authorization': f'Bearer {api_key}'
            }
            data = {'purpose': purpose}
            files = {'file': file}

            logger.info(f"用户 {request.user.username} 上传文件，用途: {purpose}")
            response = requests.post(url, headers=headers, data=data, files=files, timeout=60)

            # 记录Trace-ID
            trace_id = response.headers.get('Trace-ID', '')
            if trace_id:
                logger.info(f"上传文件 Trace-ID: {trace_id}")

            if response.status_code != 200:
                logger.error(f"文件上传失败: {response.status_code} - {response.text}")
                return Response({
                    'success': False,
                    'message': f'文件上传失败: {response.status_code}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            result = response.json()
            file_info = result.get('file', {})
            file_id = file_info.get('file_id')

            if not file_id:
                logger.error(f"文件上传响应中没有file_id: {result}")
                return Response({
                    'success': False,
                    'message': '文件上传失败，未获取到文件ID'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            logger.info(f"文件上传成功，file_id: {file_id}")
            return Response({
                'success': True,
                'message': '文件上传成功',
                'data': {
                    'file_id': file_id,
                    'file_info': file_info,
                    'local_file_path': local_file_path
                }
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'网络请求失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"文件上传异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'系统异常: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_file_url(self, request):
        """获取文件播放URL"""
        try:
            file_id = request.query_params.get('file_id')
            if not file_id:
                return Response({
                    'success': False,
                    'message': '请提供file_id参数'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取用户API密钥和group_id
            api_key = request.user.api_key
            group_id = request.user.group_id

            if not api_key or not group_id:
                return Response({
                    'success': False,
                    'message': '用户API密钥或Group ID未配置'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 调用MiniMax API获取文件信息
            url = f'https://api.minimaxi.com/v1/files/{file_id}?GroupId={group_id}'
            headers = {
                'authority': 'api.minimaxi.com',
                'Authorization': f'Bearer {api_key}'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"获取文件URL失败: {response.status_code} - {response.text}")
                return Response({
                    'success': False,
                    'message': f'获取文件URL失败: {response.status_code}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            file_info = response.json()
            download_url = file_info.get('download_url', '')

            return Response({
                'success': True,
                'data': {
                    'file_id': file_id,
                    'download_url': download_url,
                    'file_info': file_info
                }
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'网络请求失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"获取文件URL异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'系统异常: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'])
    def clone_voice(self, request):
        """执行音色克隆"""
        try:
            # 验证请求数据
            serializer = VoiceCloneCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': '请求参数错误',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取用户API密钥和group_id
            api_key = request.user.api_key
            group_id = request.user.group_id

            if not api_key or not group_id:
                return Response({
                    'success': False,
                    'message': '用户API密钥或Group ID未配置'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取表单数据
            data = serializer.validated_data
            clone_audio_file_id = request.data.get('clone_audio_file_id')
            prompt_audio_file_id = request.data.get('prompt_audio_file_id', '')

            # 获取本地文件路径（如果有）
            clone_local_path = request.data.get('clone_local_path', '')
            prompt_local_path = request.data.get('prompt_local_path', '')

            if not clone_audio_file_id:
                return Response({
                    'success': False,
                    'message': '请先上传克隆音频文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 如果有prompt音频，验证必须有prompt文本
            if prompt_audio_file_id and not data.get('prompt_text'):
                return Response({
                    'success': False,
                    'message': '使用Prompt音频时必须提供Prompt文本'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 创建克隆记录
            clone_record = VoiceCloneRecord.objects.create(
                user=request.user,
                voice_id=data['voice_id'],
                clone_audio_file_id=clone_audio_file_id,
                prompt_audio_file_id=prompt_audio_file_id,
                prompt_text=data.get('prompt_text', ''),
                test_text=data['test_text'],
                model=data['model'],
                need_noise_reduction=data['need_noise_reduction'],
                need_volume_normalization=data['need_volume_normalization'],
                status='pending'
            )

            # 保存本地文件路径（如果有）
            if clone_local_path:
                clone_record.clone_audio_file = clone_local_path
            if prompt_local_path:
                clone_record.prompt_audio_file = prompt_local_path
            clone_record.save()

            # 构建API请求payload
            payload = {
                "file_id": clone_audio_file_id,
                "voice_id": data['voice_id'],
                "text": data['test_text'],
                "model": data['model'],
                "accuracy": 0.7,
                "need_noise_reduction": data['need_noise_reduction'],
                "need_volumn_normalization": data['need_volume_normalization'],  # 注意这里是volumn而不是volume
                "aigc_watermark": False,
            }

            # 如果有prompt音频，添加clone_prompt
            if prompt_audio_file_id:
                payload["clone_prompt"] = {
                    "prompt_audio": prompt_audio_file_id,
                    "prompt_text": data['prompt_text']
                }

            # 调用MiniMax克隆API
            url = 'https://api.minimaxi.com/v1/voice_clone'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'content-type': 'application/json'
            }

            logger.info(f"用户 {request.user.username} 开始音色克隆，voice_id: {data['voice_id']}")
            response = requests.post(url, headers=headers, json=payload, timeout=120)

            # 记录Trace-ID
            trace_id = response.headers.get('Trace-ID', '')
            if trace_id:
                logger.info(f"音色克隆 Trace-ID: {trace_id}")
                clone_record.trace_id = trace_id

            # 保存API响应
            api_response = {}
            try:
                api_response = response.json()
            except:
                api_response = {'raw_response': response.text}

            clone_record.api_response = api_response

            if response.status_code != 200:
                logger.error(f"音色克隆API调用失败: {response.status_code} - {response.text}")
                clone_record.status = 'failed'
                clone_record.error_message = f"API调用失败: {response.status_code}"
                clone_record.save()

                return Response({
                    'success': False,
                    'message': f'音色克隆失败: {response.status_code}',
                    'data': {
                        'record_id': clone_record.id,
                        'status': clone_record.status,
                        'demo_audio_url': clone_record.demo_audio_url,
                        'error_message': clone_record.error_message,
                        'trace_id': clone_record.trace_id,
                        'api_response': api_response
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 处理成功响应
            base_resp = api_response.get('base_resp', {})
            if base_resp.get('status_code') == 0:
                clone_record.status = 'success'
                clone_record.demo_audio_url = api_response.get('demo_audio', '')
                logger.info(f"音色克隆成功，demo_audio: {clone_record.demo_audio_url}")

                # 下载并保存试听音频
                if clone_record.demo_audio_url:
                    demo_local_path = self.download_and_save_demo_audio(
                        clone_record.demo_audio_url,
                        clone_record.voice_id
                    )
                    if demo_local_path:
                        clone_record.demo_audio_file = demo_local_path
                        logger.info(f"试听音频已保存到本地: {demo_local_path}")
            else:
                clone_record.status = 'failed'
                clone_record.error_message = base_resp.get('status_msg', '未知错误')
                logger.error(f"音色克隆失败: {clone_record.error_message}")

            clone_record.save()

            return Response({
                'success': clone_record.status == 'success',
                'message': '音色克隆完成' if clone_record.status == 'success' else f'音色克隆失败: {clone_record.error_message}',
                'data': {
                    'record_id': clone_record.id,
                    'status': clone_record.status,
                    'demo_audio_url': clone_record.demo_audio_url,
                    'error_message': clone_record.error_message,
                    'trace_id': clone_record.trace_id,
                    'api_response': api_response
                }
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            if 'clone_record' in locals():
                clone_record.status = 'failed'
                clone_record.error_message = f"网络请求异常: {str(e)}"
                clone_record.save()

            return Response({
                'success': False,
                'message': f'网络请求失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"音色克隆异常: {str(e)}")
            if 'clone_record' in locals():
                clone_record.status = 'failed'
                clone_record.error_message = f"系统异常: {str(e)}"
                clone_record.save()

            return Response({
                'success': False,
                'message': f'系统异常: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_file_url(self, request):
        """获取文件播放URL"""
        try:
            file_id = request.query_params.get('file_id')
            if not file_id:
                return Response({
                    'success': False,
                    'message': '请提供file_id参数'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取用户API密钥和group_id
            api_key = request.user.api_key
            group_id = request.user.group_id

            if not api_key or not group_id:
                return Response({
                    'success': False,
                    'message': '用户API密钥或Group ID未配置'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 调用MiniMax API获取文件信息
            url = f'https://api.minimaxi.com/v1/files/{file_id}?GroupId={group_id}'
            headers = {
                'authority': 'api.minimaxi.com',
                'Authorization': f'Bearer {api_key}'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"获取文件URL失败: {response.status_code} - {response.text}")
                return Response({
                    'success': False,
                    'message': f'获取文件URL失败: {response.status_code}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            file_info = response.json()
            download_url = file_info.get('download_url', '')

            return Response({
                'success': True,
                'data': {
                    'file_id': file_id,
                    'download_url': download_url,
                    'file_info': file_info
                }
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'网络请求失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"获取文件URL异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'系统异常: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_local_audio(self, request):
        """获取本地存储的音频文件URL"""
        try:
            file_path = request.query_params.get('file_path')
            if not file_path:
                return Response({
                    'success': False,
                    'message': '请提供file_path参数'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 如果传入的是完整URL，提取相对路径
            if file_path.startswith('http'):
                # 从URL中提取media之后的路径
                import urllib.parse
                parsed_url = urllib.parse.urlparse(file_path)
                if '/media/' in parsed_url.path:
                    # 提取/media/之后的部分
                    relative_path = parsed_url.path.split('/media/', 1)[1]
                else:
                    relative_path = file_path
            else:
                relative_path = file_path

            # 验证文件是否存在
            if not default_storage.exists(relative_path):
                return Response({
                    'success': False,
                    'message': f'文件不存在: {relative_path}'
                }, status=status.HTTP_404_NOT_FOUND)

            # 生成文件URL
            file_url = default_storage.url(relative_path)

            return Response({
                'success': True,
                'data': {
                    'file_path': relative_path,
                    'file_url': file_url
                }
            })

        except Exception as e:
            logger.error(f"获取本地音频文件异常: {str(e)}")
            return Response({
                'success': False,
                'message': f'系统异常: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)