from django.contrib import admin
from .models import SpeakerDiarizationTask, SpeakerProfile


class SpeakerProfileInline(admin.TabularInline):
    model = SpeakerProfile
    extra = 0
    fields = ('speaker_id', 'name', 'role', 'gender', 'face_count', 'segment_count')
    readonly_fields = ('speaker_id', 'name', 'role', 'gender', 'face_count', 'segment_count')


@admin.register(SpeakerDiarizationTask)
class SpeakerDiarizationTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'progress', 'num_speakers_detected', 'is_applied', 'created_at')
    list_filter = ('status', 'is_applied', 'created_at')
    search_fields = ('project__name', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [SpeakerProfileInline]

    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'project', 'status', 'progress', 'message', 'error_message')
        }),
        ('识别结果', {
            'fields': ('num_speakers_detected', 'total_segments', 'total_faces', 'valid_faces')
        }),
        ('参数与统计', {
            'fields': ('clustering_params', 'filter_statistics'),
            'classes': ('collapse',)
        }),
        ('API Trace', {
            'fields': ('vlm_trace_id', 'llm_trace_id'),
            'classes': ('collapse',)
        }),
        ('应用状态', {
            'fields': ('is_applied', 'applied_at')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SpeakerProfile)
class SpeakerProfileAdmin(admin.ModelAdmin):
    list_display = ('task', 'speaker_id', 'name', 'role', 'gender', 'face_count', 'segment_count')
    list_filter = ('gender', 'task__status')
    search_fields = ('name', 'role', 'task__project__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('基本信息', {
            'fields': ('task', 'speaker_id', 'name', 'role', 'gender')
        }),
        ('统计信息', {
            'fields': ('face_count', 'segment_count', 'segments')
        }),
        ('详细档案', {
            'fields': ('appearance', 'character_analysis', 'representative_images'),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )
