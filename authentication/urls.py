"""
认证相关URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('config/', views.UserConfigView.as_view(), name='user-config'),
    path('test-auth/', views.test_auth, name='test-auth'),
    path('stats/', views.user_stats, name='user-stats'),
]