"""
音色克隆URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VoiceCloneViewSet

router = DefaultRouter()
router.register(r'voice-cloning', VoiceCloneViewSet, basename='voice-cloning')

urlpatterns = [
    path('api/', include(router.urls)),
]