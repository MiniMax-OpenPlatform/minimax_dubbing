from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import Project


class ProjectAdmin(admin.ModelAdmin):
    """项目管理"""

    list_display = (
        'name', 'user', 'source_lang', 'target_lang', 'status_display',
        'progress_display', 'segment_count', 'completed_count', 'created_at'
    )
    list_filter = ('status', 'source_lang', 'target_lang', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'user__email', 'description')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'user', 'description')
        }),
        ('语言配置', {
            'fields': ('source_lang', 'target_lang')
        }),
        ('文件信息', {
            'fields': ('srt_file_path', 'video_file_path', 'concatenated_audio_url'),
            'classes': ('collapse',)
        }),
        ('TTS配置', {
            'fields': ('tts_model', 'voice_mappings', 'custom_vocabulary', 'max_speed'),
            'classes': ('collapse',)
        }),
        ('统计信息', {
            'fields': ('status', 'segment_count', 'completed_segment_count', 'progress_percentage', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('segment_count', 'completed_segment_count', 'progress_percentage', 'created_at', 'updated_at')

    def status_display(self, obj):
        """彩色显示状态"""
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "状态"

    def progress_display(self, obj):
        """进度条显示"""
        progress = obj.progress_percentage or 0
        color = '#28a745' if progress == 100 else '#17a2b8' if progress > 50 else '#ffc107'
        return format_html(
            '<div style="width: 100px; background: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            progress, color, progress
        )
    progress_display.short_description = "进度"

    def completed_count(self, obj):
        """显示完成的段落数"""
        return f"{obj.completed_segment_count}/{obj.segment_count}"
    completed_count.short_description = "完成情况"

    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).select_related('user').prefetch_related('segments')

    actions = ['mark_as_pending', 'mark_as_processing', 'mark_as_completed']

    def mark_as_pending(self, request, queryset):
        """批量标记为待处理"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'成功将 {updated} 个项目标记为待处理')
    mark_as_pending.short_description = "标记为待处理"

    def mark_as_processing(self, request, queryset):
        """批量标记为处理中"""
        updated = queryset.update(status='processing')
        self.message_user(request, f'成功将 {updated} 个项目标记为处理中')
    mark_as_processing.short_description = "标记为处理中"

    def mark_as_completed(self, request, queryset):
        """批量标记为已完成"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'成功将 {updated} 个项目标记为已完成')
    mark_as_completed.short_description = "标记为已完成"

    def has_add_permission(self, request):
        """项目应通过前端页面创建，不允许在管理后台添加"""
        return False

    def get_urls(self):
        """移除添加URL"""
        urls = super().get_urls()
        # 过滤掉添加相关的URL
        filtered_urls = []
        for url in urls:
            if hasattr(url, 'name') and url.name and 'add' in url.name:
                continue
            filtered_urls.append(url)
        return filtered_urls
