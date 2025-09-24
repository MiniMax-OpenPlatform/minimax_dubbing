"""
音色克隆管理后台
"""
from django.contrib import admin
from .models import VoiceCloneRecord


@admin.register(VoiceCloneRecord)
class VoiceCloneRecordAdmin(admin.ModelAdmin):
    list_display = ['voice_id', 'user', 'status', 'model', 'created_at']
    list_filter = ['status', 'model', 'need_noise_reduction', 'need_volume_normalization']
    search_fields = ['voice_id', 'user__username', 'test_text']
    readonly_fields = ['created_at', 'updated_at', 'api_response']
    ordering = ['-created_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'voice_id', 'status')
        }),
        ('文件信息', {
            'fields': ('clone_audio_file_id', 'prompt_audio_file_id')
        }),
        ('配置参数', {
            'fields': ('prompt_text', 'test_text', 'model', 'need_noise_reduction', 'need_volume_normalization')
        }),
        ('结果信息', {
            'fields': ('demo_audio_url', 'error_message')
        }),
        ('系统信息', {
            'fields': ('api_response', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )