"""
系统监控Admin界面
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import SystemConfig, TaskMonitor


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """系统配置管理"""

    list_display = [
        'id', 'batch_translate_request_interval', 'max_concurrent_translate_tasks',
        'task_timeout_minutes', 'enable_detailed_logging', 'updated_at', 'edit_button'
    ]

    fieldsets = (
        ('API并发控制', {
            'fields': (
                'batch_translate_request_interval',
                'max_concurrent_translate_tasks',
                'task_timeout_minutes',
                'batch_tts_request_interval',
                'max_concurrent_tts_tasks'
            ),
            'description': '控制批量翻译和TTS任务的执行频率和并发数量'
        }),
        ('任务监控和清理', {
            'fields': (
                'enable_detailed_logging',
                'auto_cleanup_completed_tasks',
                'cleanup_interval_hours'
            ),
            'description': '任务监控和TaskMonitor记录清理设置'
        }),
        ('数据自动清理 ⚠️', {
            'fields': (
                'enable_auto_cleanup_data',
                'cleanup_projects_after_days',
                'cleanup_users_after_days',
                'cleanup_execution_time'
            ),
            'description': '<strong style="color: red;">⚠️ 重要：启用后将定期自动删除不活跃的项目和用户数据，此操作不可逆！</strong><br>'
                          '- 项目清理：删除N天未更新的项目及其所有关联数据（段落、音频文件等）<br>'
                          '- 用户清理：删除N天未登录的普通用户及其所有数据（保留超级管理员）<br>'
                          '- 执行时间：每天在指定时间自动执行清理（建议凌晨时段）<br>'
                          '<strong>使用前请先运行命令测试：python manage.py cleanup_old_data --dry-run</strong>',
            'classes': ('wide',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        # 只允许一个配置实例
        return not SystemConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # 不允许删除配置
        return False

    def edit_button(self, obj):
        """添加修改按钮"""
        return format_html(
            '<a class="button" href="/admin/system_monitor/systemconfig/{}/change/">修改配置</a>',
            obj.pk
        )
    edit_button.short_description = "操作"


@admin.register(TaskMonitor)
class TaskMonitorAdmin(admin.ModelAdmin):
    """任务监控管理"""

    list_display = [
        'task_id', 'task_type', 'project_name', 'status_display',
        'progress_display', 'duration_display', 'created_at'
    ]

    list_filter = [
        'status', 'task_type', 'created_at'
    ]

    search_fields = [
        'task_id', 'project_name', 'current_segment_text'
    ]

    readonly_fields = [
        'task_id', 'task_type', 'project_id', 'project_name',
        'total_segments', 'completed_segments', 'failed_segments',
        'start_time', 'end_time', 'current_segment_text',
        'created_at', 'updated_at', 'progress_percentage', 'duration_seconds'
    ]

    fieldsets = (
        ('任务信息', {
            'fields': (
                'task_id', 'task_type', 'project_id', 'project_name', 'status'
            )
        }),
        ('执行进度', {
            'fields': (
                'total_segments', 'completed_segments', 'failed_segments',
                'progress_percentage', 'current_segment_text'
            )
        }),
        ('时间信息', {
            'fields': (
                'start_time', 'end_time', 'duration_seconds',
                'created_at', 'updated_at'
            )
        }),
        ('错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )

    def status_display(self, obj):
        """状态显示"""
        colors = {
            'pending': '#f39c12',
            'running': '#3498db',
            'completed': '#27ae60',
            'failed': '#e74c3c',
            'cancelled': '#95a5a6',
            'timeout': '#e67e22'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = '状态'

    def progress_display(self, obj):
        """进度显示"""
        if obj.status == 'pending':
            return '等待中'

        progress = obj.progress_percentage
        if progress == 100:
            color = '#27ae60'
        elif progress >= 50:
            color = '#3498db'
        else:
            color = '#f39c12'

        return format_html(
            '<div style="width: 100px; background-color: #ecf0f1; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; height: 20px; background-color: {}; text-align: center; line-height: 20px; color: white; font-size: 12px;">'
            '{}%</div></div>',
            progress, color, progress
        )
    progress_display.short_description = '进度'

    def duration_display(self, obj):
        """执行时长显示"""
        if not obj.start_time:
            return '-'

        duration = obj.duration_seconds
        if duration < 60:
            return f'{duration}秒'
        elif duration < 3600:
            return f'{duration // 60}分{duration % 60}秒'
        else:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            return f'{hours}时{minutes}分'
    duration_display.short_description = '执行时长'

    def has_add_permission(self, request):
        # 任务监控记录不允许手动添加
        return False

    def has_change_permission(self, request, obj=None):
        # 只允许查看，不允许修改（除了状态）
        return True

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['running']:
            # 运行中的任务只允许修改状态（用于手动取消）
            return [f for f in self.readonly_fields if f != 'status']
        return self.readonly_fields


# 自定义Admin站点标题
admin.site.site_header = "翻译系统管理后台"
admin.site.site_title = "翻译系统"
admin.site.index_title = "系统监控和配置"
