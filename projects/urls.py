"""
项目相关URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from segments.views import SegmentViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='projects')

# 嵌套路由器 - 项目下的段落
projects_router = routers.NestedDefaultRouter(router, r'projects', lookup='project')
projects_router.register(r'segments', SegmentViewSet, basename='project-segments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
]