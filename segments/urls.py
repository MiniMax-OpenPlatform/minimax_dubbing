"""
段落相关URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'segments', views.SegmentViewSet, basename='segments')

urlpatterns = [
    path('', include(router.urls)),
]