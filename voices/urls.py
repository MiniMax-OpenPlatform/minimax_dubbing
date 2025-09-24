"""
音色管理URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VoiceViewSet

router = DefaultRouter()
router.register(r'voices', VoiceViewSet, basename='voice')

urlpatterns = [
    path('api/', include(router.urls)),
]