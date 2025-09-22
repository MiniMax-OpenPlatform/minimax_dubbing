"""
系统监控和配置模型
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class SystemConfig(models.Model):
    """系统配置单例模型"""

    # API并发控制
    batch_translate_request_interval = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        verbose_name="批量翻译请求间隔（秒）",
        help_text="控制批量翻译API请求之间的间隔时间，范围：0.1-10秒"
    )

    max_concurrent_translate_tasks = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="最大并发翻译任务数",
        help_text="系统同时运行的批量翻译任务数量限制，范围：1-10"
    )

    task_timeout_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(5), MaxValueValidator(300)],
        verbose_name="任务超时时间（分钟）",
        help_text="批量翻译任务的最长执行时间，范围：5-300分钟"
    )

    # 日志和监控
    enable_detailed_logging = models.BooleanField(
        default=True,
        verbose_name="启用详细日志",
        help_text="记录批量翻译的详细执行日志"
    )

    auto_cleanup_completed_tasks = models.BooleanField(
        default=True,
        verbose_name="自动清理完成的任务",
        help_text="自动清理已完成或失败的任务数据"
    )

    cleanup_interval_hours = models.IntegerField(
        default=24,
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        verbose_name="清理间隔（小时）",
        help_text="自动清理任务的间隔时间，范围：1-168小时"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "系统配置"
        verbose_name_plural = "系统配置"

    def __str__(self):
        return f"系统配置 (更新时间: {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')})"

    @classmethod
    def get_config(cls):
        """获取系统配置（单例模式）"""
        config, created = cls.objects.get_or_create(pk=1)
        return config

    def save(self, *args, **kwargs):
        # 确保只有一个配置实例
        self.pk = 1
        super().save(*args, **kwargs)


class TaskMonitor(models.Model):
    """任务监控记录"""

    TASK_STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
        ('timeout', '超时'),
    ]

    task_id = models.CharField(max_length=100, unique=True, verbose_name="任务ID")
    task_type = models.CharField(max_length=50, default='batch_translate', verbose_name="任务类型")
    project_id = models.IntegerField(verbose_name="项目ID")
    project_name = models.CharField(max_length=200, verbose_name="项目名称")

    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default='pending',
        verbose_name="状态"
    )

    total_segments = models.IntegerField(default=0, verbose_name="总段落数")
    completed_segments = models.IntegerField(default=0, verbose_name="已完成段落数")
    failed_segments = models.IntegerField(default=0, verbose_name="失败段落数")

    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")

    current_segment_text = models.TextField(blank=True, verbose_name="当前处理段落")
    error_message = models.TextField(blank=True, verbose_name="错误信息")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "任务监控"
        verbose_name_plural = "任务监控"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_type}任务 {self.task_id} - {self.get_status_display()}"

    @property
    def progress_percentage(self):
        """进度百分比"""
        if self.total_segments == 0:
            return 0
        return int((self.completed_segments / self.total_segments) * 100)

    @property
    def duration_seconds(self):
        """执行时长（秒）"""
        if not self.start_time:
            return 0
        end_time = self.end_time or timezone.now()
        return int((end_time - self.start_time).total_seconds())
