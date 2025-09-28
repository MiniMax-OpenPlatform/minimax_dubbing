from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


class UserAdmin(BaseUserAdmin):
    """自定义用户管理"""

    list_display = (
        'username', 'email', 'group_id', 'api_key_display',
        'is_staff', 'is_active', 'project_count', 'created_at'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'group_id', 'created_at')
    search_fields = ('username', 'email', 'group_id')
    ordering = ('-created_at',)

    # 添加自定义字段到编辑表单
    fieldsets = BaseUserAdmin.fieldsets + (
        ('API配置', {'fields': ('group_id', 'api_key')}),
        ('统计信息', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    # 添加到创建表单
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('API配置', {'fields': ('group_id', 'api_key')}),
    )

    readonly_fields = ('created_at',)

    def api_key_display(self, obj):
        """显示API密钥的前8位"""
        if obj.api_key:
            return f"{obj.api_key[:8]}***"
        return "未设置"
    api_key_display.short_description = "API密钥"

    def project_count(self, obj):
        """显示用户的项目数量"""
        count = obj.projects.count() if hasattr(obj, 'projects') else 0
        if count > 0:
            return format_html(
                '<a href="/admin/projects/project/?user__id={}">{} 个项目</a>',
                obj.id, count
            )
        return "0 个项目"
    project_count.short_description = "项目数量"

    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).select_related().prefetch_related('projects')

    def has_add_permission(self, request):
        """用户应通过前端注册页面创建，不允许在管理后台添加"""
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
