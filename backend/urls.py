"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from .admin import admin_site
from .views import serve_media_with_range

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/', include('projects.urls')),
    path('api/', include('segments.urls')),
    path('api/logs/', include('logs.urls')),
    path('', include('voices.urls')),
    path('', include('voice_cloning.urls')),
]

# 添加媒体文件URL配置 - 支持HTTP Range请求
if settings.DEBUG:
    # 使用自定义视图提供媒体文件，支持Range请求
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media_with_range, name='media'),
    ]
