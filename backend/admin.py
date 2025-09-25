"""
自定义管理后台首页
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from django.utils.html import format_html
from projects.models import Project
from segments.models import Segment

User = get_user_model()


class CustomAdminSite(admin.AdminSite):
    """自定义管理后台"""
    site_header = "MiniMax Translation 管理后台"
    site_title = "MiniMax Translation"
    index_title = "系统概览"

    def index(self, request, extra_context=None):
        """自定义首页显示统计信息"""
        extra_context = extra_context or {}

        # 用户统计
        user_stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
        }

        # 项目统计
        project_stats = {
            'total_projects': Project.objects.count(),
            'pending_projects': Project.objects.filter(status='pending').count(),
            'processing_projects': Project.objects.filter(status='processing').count(),
            'completed_projects': Project.objects.filter(status='completed').count(),
            'failed_projects': Project.objects.filter(status='failed').count(),
        }

        # 段落统计
        segment_stats = {
            'total_segments': Segment.objects.count(),
            'pending_segments': Segment.objects.filter(status='pending').count(),
            'translated_segments': Segment.objects.filter(status='translated').count(),
            'completed_segments': Segment.objects.filter(status='completed').count(),
            'failed_segments': Segment.objects.filter(status='failed').count(),
        }

        # 语言统计
        language_stats = list(
            Project.objects.values('source_lang', 'target_lang')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # 活跃用户（有项目的用户）
        active_users_with_projects = list(
            User.objects.annotate(project_count=Count('projects'))
            .filter(project_count__gt=0)
            .order_by('-project_count')[:10]
        )

        # 最新项目
        recent_projects = Project.objects.select_related('user').order_by('-created_at')[:10]

        extra_context.update({
            'user_stats': user_stats,
            'project_stats': project_stats,
            'segment_stats': segment_stats,
            'language_stats': language_stats,
            'active_users_with_projects': active_users_with_projects,
            'recent_projects': recent_projects,
        })

        return super().index(request, extra_context)

# 创建自定义管理站点实例
admin_site = CustomAdminSite(name='custom_admin')

# 注册所有模型到自定义站点
from authentication.admin import UserAdmin
from projects.admin import ProjectAdmin
from segments.admin import SegmentAdmin
from system_monitor.admin import SystemConfigAdmin, TaskMonitorAdmin
from system_monitor.models import SystemConfig, TaskMonitor
from voices.admin import VoiceAdmin, VoiceQueryLogAdmin
from voices.models import Voice, VoiceQueryLog
from voice_cloning.admin import VoiceCloneRecordAdmin
from voice_cloning.models import VoiceCloneRecord

admin_site.register(User, UserAdmin)
admin_site.register(Project, ProjectAdmin)
admin_site.register(Segment, SegmentAdmin)
admin_site.register(SystemConfig, SystemConfigAdmin)
admin_site.register(TaskMonitor, TaskMonitorAdmin)
admin_site.register(Voice, VoiceAdmin)
admin_site.register(VoiceQueryLog, VoiceQueryLogAdmin)
admin_site.register(VoiceCloneRecord, VoiceCloneRecordAdmin)