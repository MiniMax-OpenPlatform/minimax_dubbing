"""
说话人识别URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SpeakerDiarizationTaskViewSet

router = DefaultRouter()
router.register(r'tasks', SpeakerDiarizationTaskViewSet, basename='speaker-diarization-task')

urlpatterns = [
    path('', include(router.urls)),
]
