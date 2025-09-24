"""
音色管理模型
"""
from django.db import models
from django.conf import settings


class Voice(models.Model):
    """音色模型"""

    VOICE_TYPES = [
        ('system_voice', '系统音色'),
        ('voice_cloning', '音色克隆'),
        ('voice_generation', '音色生成'),
    ]

    # 基本信息
    voice_id = models.CharField(max_length=200, verbose_name="音色ID")
    voice_name = models.CharField(max_length=200, blank=True, verbose_name="音色名称")
    voice_type = models.CharField(max_length=20, choices=VOICE_TYPES, verbose_name="音色类型")
    description = models.JSONField(default=list, blank=True, verbose_name="描述")

    # 用户相关
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    user_note = models.TextField(blank=True, verbose_name="用户备注")

    # 时间信息
    created_time = models.CharField(max_length=20, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="记录创建时间")

    class Meta:
        verbose_name = "音色"
        verbose_name_plural = "音色"
        ordering = ['-created_at']
        unique_together = ['voice_id', 'user']  # 同一用户的同一音色只能有一条记录

    def __str__(self):
        return f"{self.voice_name or self.voice_id} ({self.get_voice_type_display()})"


class VoiceQueryLog(models.Model):
    """音色查询日志"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    query_time = models.DateTimeField(auto_now_add=True, verbose_name="查询时间")
    total_count = models.IntegerField(verbose_name="查询到的音色总数")
    system_voice_count = models.IntegerField(default=0, verbose_name="系统音色数量")
    voice_cloning_count = models.IntegerField(default=0, verbose_name="音色克隆数量")
    voice_generation_count = models.IntegerField(default=0, verbose_name="音色生成数量")
    success = models.BooleanField(default=True, verbose_name="查询是否成功")
    error_message = models.TextField(blank=True, verbose_name="错误信息")

    class Meta:
        verbose_name = "音色查询日志"
        verbose_name_plural = "音色查询日志"
        ordering = ['-query_time']

    def __str__(self):
        return f"{self.user.username} - {self.query_time.strftime('%Y-%m-%d %H:%M:%S')}"
