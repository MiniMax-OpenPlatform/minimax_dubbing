"""
后端核心视图
包含支持HTTP Range请求的媒体文件服务
"""
import os
import mimetypes
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_http_methods
from ranged_response import RangedFileResponse


@require_http_methods(["GET", "HEAD"])
def serve_media_with_range(request, path):
    """
    提供支持HTTP Range请求的媒体文件服务

    Args:
        request: HTTP请求对象
        path: 媒体文件的相对路径

    Returns:
        RangedFileResponse: 支持Range请求的文件响应

    Raises:
        Http404: 文件不存在时抛出404错误
    """
    # 构建完整文件路径
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    # 安全检查：确保文件在MEDIA_ROOT目录内
    file_path = os.path.abspath(file_path)
    media_root = os.path.abspath(settings.MEDIA_ROOT)

    if not file_path.startswith(media_root):
        raise Http404("Invalid file path")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise Http404(f"File not found: {path}")

    # 检查是否是文件（不是目录）
    if not os.path.isfile(file_path):
        raise Http404(f"Not a file: {path}")

    # 获取文件的MIME类型
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'

    # 打开文件
    try:
        file_obj = open(file_path, 'rb')
    except IOError:
        raise Http404(f"Cannot open file: {path}")

    # 使用 RangedFileResponse 支持 Range 请求
    response = RangedFileResponse(
        request,
        file_obj,
        content_type=content_type
    )

    # 添加文件名到响应头（用于下载）
    filename = os.path.basename(file_path)
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    # 添加缓存控制
    response['Cache-Control'] = 'public, max-age=3600'

    # 声明支持 Range 请求
    response['Accept-Ranges'] = 'bytes'

    return response
