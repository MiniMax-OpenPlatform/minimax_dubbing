from django.db import models
from django.conf import settings


class Project(models.Model):
    """
    翻译项目模型
    """
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    LANGUAGE_CHOICES = [
        ('zh', '中文'),
        ('yue', '粤语'),
        ('en', '英语'),
        ('es', '西班牙语'),
        ('fr', '法语'),
        ('ru', '俄语'),
        ('de', '德语'),
        ('pt', '葡萄牙语'),
        ('ar', '阿拉伯语'),
        ('it', '意大利语'),
        ('ja', '日语'),
        ('ko', '韩语'),
        ('id', '印尼语'),
        ('vi', '越南语'),
        ('tr', '土耳其语'),
        ('nl', '荷兰语'),
        ('uk', '乌克兰语'),
        ('th', '泰语'),
        ('pl', '波兰语'),
        ('ro', '罗马尼亚语'),
        ('el', '希腊语'),
        ('cs', '捷克语'),
        ('fi', '芬兰语'),
        ('hi', '印地语'),
        ('bg', '保加利亚语'),
        ('da', '丹麦语'),
        ('he', '希伯来语'),
        ('ms', '马来语'),
        ('fa', '波斯语'),
        ('sk', '斯洛伐克语'),
        ('sv', '瑞典语'),
        ('hr', '克罗地亚语'),
        ('fil', '菲律宾语'),
        ('hu', '匈牙利语'),
        ('no', '挪威语'),
        ('sl', '斯洛文尼亚语'),
        ('ca', '加泰罗尼亚语'),
        ('nn', '尼诺斯克语'),
        ('ta', '泰米尔语'),
        ('af', '阿非利卡语'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200, help_text="项目名称")
    description = models.TextField(blank=True, help_text="项目描述")
    source_lang = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='zh', help_text="源语言")
    target_lang = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en', help_text="目标语言")

    # 文件路径
    srt_file_path = models.FileField(upload_to='srt/', blank=True, null=True, help_text="SRT文件路径")
    video_file_path = models.FileField(upload_to='videos/', blank=True, null=True, help_text="视频文件路径")

    # 项目级配置
    tts_model = models.CharField(max_length=50, default="speech-01-turbo", help_text="TTS模型")
    voice_mappings = models.JSONField(default=list, help_text="角色音色映射表")
    custom_vocabulary = models.JSONField(default=list, help_text="专有词汇表")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_source_lang_display()} → {self.get_target_lang_display()})"

    @property
    def segment_count(self):
        """返回段落总数"""
        return self.segments.count()

    @property
    def completed_segment_count(self):
        """返回已完成的段落数"""
        return self.segments.filter(status='completed').count()

    @property
    def progress_percentage(self):
        """返回项目进度百分比"""
        total = self.segment_count
        if total == 0:
            return 0
        completed = self.completed_segment_count
        return int((completed / total) * 100)
