from django.urls import path
from . import views

urlpatterns = [
    path('system/', views.get_system_logs, name='get_system_logs'),
    path('system/clear/', views.clear_system_logs, name='clear_system_logs'),
    path('system/stats/', views.get_log_stats, name='get_log_stats'),
    path('raw/', views.get_raw_logs, name='get_raw_logs'),
    path('clear/', views.clear_logs, name='clear_logs'),
]