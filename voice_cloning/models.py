"""
音色克隆模型
"""
from django.db import models
from django.conf import settings


class VoiceCloneRecord(models.Model):
    """音色克隆记录"""

    STATUS_CHOICES = [
        ('pending', '处理中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    # 基本信息
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    voice_id = models.CharField(max_length=200, verbose_name="音色ID")

    # 上传的文件
    clone_audio_file_id = models.CharField(max_length=200, verbose_name="克隆音频文件ID")
    prompt_audio_file_id = models.CharField(max_length=200, blank=True, verbose_name="Prompt音频文件ID")

    # 参数配置
    prompt_text = models.TextField(blank=True, verbose_name="Prompt文本")
    test_text = models.TextField(verbose_name="试听文本")
    model = models.CharField(max_length=50, default="speech-2.5-hd-preview", verbose_name="试听模型")
    need_noise_reduction = models.BooleanField(default=False, verbose_name="是否开启降噪")
    need_volume_normalization = models.BooleanField(default=False, verbose_name="是否开启音量归一化")

    # 结果信息
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    demo_audio_url = models.URLField(blank=True, verbose_name="试听音频URL")
    error_message = models.TextField(blank=True, verbose_name="错误信息")

    # 本地音频文件存储
    clone_audio_file = models.FileField(upload_to='voice_clone/clone_audio/', blank=True, null=True, verbose_name="克隆音频文件")
    prompt_audio_file = models.FileField(upload_to='voice_clone/prompt_audio/', blank=True, null=True, verbose_name="Prompt音频文件")
    demo_audio_file = models.FileField(upload_to='voice_clone/demo_audio/', blank=True, null=True, verbose_name="试听音频文件")

    # API响应信息
    api_response = models.JSONField(blank=True, null=True, verbose_name="API响应")
    trace_id = models.CharField(max_length=100, blank=True, verbose_name="Trace ID")

    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "音色克隆记录"
        verbose_name_plural = "音色克隆记录"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.voice_id} - {self.get_status_display()}"