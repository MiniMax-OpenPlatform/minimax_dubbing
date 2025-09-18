from django.urls import path
from . import views

urlpatterns = [
    path('system/', views.get_system_logs, name='get_system_logs'),
    path('system/clear/', views.clear_system_logs, name='clear_system_logs'),
    path('system/stats/', views.get_log_stats, name='get_log_stats'),
]