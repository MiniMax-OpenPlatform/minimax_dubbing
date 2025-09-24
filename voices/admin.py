from django.contrib import admin
from .models import Voice, VoiceQueryLog


@admin.register(Voice)
class VoiceAdmin(admin.ModelAdmin):
    list_display = ['voice_id', 'voice_name', 'voice_type', 'user', 'created_time', 'updated_at']
    list_filter = ['voice_type', 'created_time', 'user']
    search_fields = ['voice_id', 'voice_name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(VoiceQueryLog)
class VoiceQueryLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'query_time', 'total_count', 'success']
    list_filter = ['success', 'query_time', 'user']
    readonly_fields = ['query_time']
