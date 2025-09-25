from django.contrib import admin
from django.utils.html import format_html
from .models import Segment


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    """段落管理"""

    list_display = (
        'index', 'project_name', 'speaker', 'time_range',
        'original_text_preview', 'translated_text_preview',
        'status_display', 'voice_info', 'audio_status'
    )
    list_filter = ('status', 'speaker', 'emotion', 'project', 'project__user')
    search_fields = ('original_text', 'translated_text', 'speaker', 'project__name')
    ordering = ('project', 'index')
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('project', 'index', 'speaker')
        }),
        ('时间信息', {
            'fields': ('start_time', 'end_time', 'duration', 'time_display')
        }),
        ('文本内容', {
            'fields': ('original_text', 'translated_text')
        }),
        ('语音配置', {
            'fields': ('voice_id', 'emotion', 'speed'),
            'classes': ('collapse',)
        }),
        ('音频文件', {
            'fields': ('original_audio_url', 'translated_audio_url'),
            'classes': ('collapse',)
        }),
        ('时长分析', {
            'fields': ('t_tts_duration', 'target_duration', 'ratio', 'is_aligned'),
            'classes': ('collapse',)
        }),
        ('状态信息', {
            'fields': ('status', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('duration', 'time_display', 'is_aligned', 'created_at', 'updated_at')

    def project_name(self, obj):
        """显示项目名称"""
        return format_html(
            '<a href="/admin/projects/project/{}/change/">{}</a>',
            obj.project.id, obj.project.name
        )
    project_name.short_description = "项目"

    def time_range(self, obj):
        """显示时间范围"""
        return obj.time_display
    time_range.short_description = "时间范围"

    def original_text_preview(self, obj):
        """原文预览"""
        text = obj.original_text or ""
        if len(text) > 30:
            return text[:30] + "..."
        return text
    original_text_preview.short_description = "原文"

    def translated_text_preview(self, obj):
        """译文预览"""
        text = obj.translated_text or ""
        if len(text) > 30:
            return text[:30] + "..."
        return text or "未翻译"
    translated_text_preview.short_description = "译文"

    def status_display(self, obj):
        """状态显示"""
        colors = {
            'pending': '#6c757d',
            'translating': '#ffc107',
            'translated': '#17a2b8',
            'tts_processing': '#fd7e14',
            'completed': '#28a745',
            'failed': '#dc3545',
            'silent': '#6f42c1'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "状态"

    def voice_info(self, obj):
        """语音信息"""
        if obj.voice_id:
            return f"{obj.voice_id} ({obj.emotion}, {obj.speed}x)"
        return "未配置"
    voice_info.short_description = "语音配置"

    def audio_status(self, obj):
        """音频状态"""
        if obj.translated_audio_url:
            duration_info = ""
            if obj.t_tts_duration and obj.target_duration:
                ratio = obj.ratio or 0
                color = '#28a745' if ratio <= 1.2 else '#ffc107' if ratio <= 1.5 else '#dc3545'
                duration_info = format_html(
                    ' <span style="color: {};">({:.1f}s/{:.1f}s)</span>',
                    color, obj.t_tts_duration, obj.target_duration
                )
            return format_html('✅ 已生成{}', duration_info)
        return "❌ 未生成"
    audio_status.short_description = "音频状态"

    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).select_related('project', 'project__user')

    actions = ['mark_as_pending', 'mark_as_translated', 'mark_as_completed', 'clear_audio']

    def mark_as_pending(self, request, queryset):
        """批量标记为待处理"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'成功将 {updated} 个段落标记为待处理')
    mark_as_pending.short_description = "标记为待处理"

    def mark_as_translated(self, request, queryset):
        """批量标记为已翻译"""
        updated = queryset.update(status='translated')
        self.message_user(request, f'成功将 {updated} 个段落标记为已翻译')
    mark_as_translated.short_description = "标记为已翻译"

    def mark_as_completed(self, request, queryset):
        """批量标记为已完成"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'成功将 {updated} 个段落标记为已完成')
    mark_as_completed.short_description = "标记为已完成"

    def clear_audio(self, request, queryset):
        """清除音频文件"""
        updated = queryset.update(
            translated_audio_url='',
            t_tts_duration=None,
            ratio=None
        )
        self.message_user(request, f'成功清除 {updated} 个段落的音频文件')
    clear_audio.short_description = "清除音频文件"
