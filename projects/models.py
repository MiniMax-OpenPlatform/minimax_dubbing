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
        ('Chinese', '中文'),
        ('Chinese,Yue', '粤语'),
        ('English', '英语'),
        ('Spanish', '西班牙语'),
        ('French', '法语'),
        ('Russian', '俄语'),
        ('German', '德语'),
        ('Portuguese', '葡萄牙语'),
        ('Arabic', '阿拉伯语'),
        ('Italian', '意大利语'),
        ('Japanese', '日语'),
        ('Korean', '韩语'),
        ('Indonesian', '印尼语'),
        ('Vietnamese', '越南语'),
        ('Turkish', '土耳其语'),
        ('Dutch', '荷兰语'),
        ('Ukrainian', '乌克兰语'),
        ('Thai', '泰语'),
        ('Polish', '波兰语'),
        ('Romanian', '罗马尼亚语'),
        ('Greek', '希腊语'),
        ('Czech', '捷克语'),
        ('Finnish', '芬兰语'),
        ('Hindi', '印地语'),
        ('Bulgarian', '保加利亚语'),
        ('Danish', '丹麦语'),
        ('Hebrew', '希伯来语'),
        ('Malay', '马来语'),
        ('Persian', '波斯语'),
        ('Slovak', '斯洛伐克语'),
        ('Swedish', '瑞典语'),
        ('Croatian', '克罗地亚语'),
        ('Filipino', '菲律宾语'),
        ('Hungarian', '匈牙利语'),
        ('Norwegian', '挪威语'),
        ('Slovenian', '斯洛文尼亚语'),
        ('Catalan', '加泰罗尼亚语'),
        ('Nynorsk', '尼诺斯克语'),
        ('Tamil', '泰米尔语'),
        ('Afrikaans', '阿非利卡语'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200, help_text="项目名称")
    description = models.TextField(blank=True, help_text="项目描述")
    source_lang = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='Chinese', help_text="源语言")
    target_lang = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='English', help_text="目标语言")

    # 文件路径
    srt_file_path = models.FileField(upload_to='srt/', blank=True, null=True, help_text="SRT文件路径")
    video_file_path = models.FileField(upload_to='videos/', blank=True, null=True, help_text="原始视频文件路径")
    concatenated_audio_url = models.CharField(max_length=500, blank=True, help_text="拼接后的完整翻译音频URL")
    mixed_audio_path = models.FileField(upload_to='audio/mixed/', blank=True, null=True, help_text="混合音频路径（翻译+背景）")
    final_video_path = models.FileField(upload_to='videos/final/', blank=True, null=True, help_text="最终合成视频路径")

    # 人声分离相关字段
    original_audio_path = models.FileField(upload_to='audio/original/', blank=True, null=True, help_text="从视频提取的原始音频")
    vocal_audio_path = models.FileField(upload_to='audio/vocals/', blank=True, null=True, help_text="分离后的人声音频")
    background_audio_path = models.FileField(upload_to='audio/background/', blank=True, null=True, help_text="分离后的背景音")
    separation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('processing', '分离中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='pending',
        help_text="人声分离状态"
    )
    separation_started_at = models.DateTimeField(blank=True, null=True, help_text="分离开始时间")
    separation_completed_at = models.DateTimeField(blank=True, null=True, help_text="分离完成时间")

    # 项目级配置
    tts_model = models.CharField(max_length=50, default="speech-2.5-hd-preview", help_text="TTS模型")
    voice_mappings = models.JSONField(default=list, help_text="角色音色映射表")
    custom_vocabulary = models.JSONField(default=list, help_text="专有词汇表")
    max_speed = models.FloatField(
        default=2.0,
        help_text="TTS时间戳对齐允许的最大speed参数，范围1.2-2.0"
    )
    num_speakers = models.IntegerField(default=2, help_text="对话中的角色数量，用于LLM自动分配说话人")
    background_info = models.TextField(blank=True, default='', help_text="对话背景信息，用于辅助LLM分配说话人")

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
        """返回已完成的段落数（ratio <= 1的段落）"""
        return self.segments.filter(
            ratio__lte=1.0,
            ratio__isnull=False
        ).count()

    @property
    def progress_percentage(self):
        """返回项目进度百分比"""
        total = self.segment_count
        if total == 0:
            return 0
        completed = self.completed_segment_count
        return int((completed / total) * 100)

    @property
    def progress_stats(self):
        """返回基于时长比例的进度统计信息"""
        segments = self.segments.all()
        total = segments.count()

        if total == 0:
            return {
                'total': 0,
                'aligned_count': 0,
                'unaligned_count': 0,
                'no_ratio_count': 0,
                'percentage': 0
            }

        # 统计有ratio值的段落
        with_ratio = segments.filter(ratio__isnull=False)
        aligned_count = with_ratio.filter(ratio__lte=1.0).count()  # ratio <= 1的段落
        unaligned_count = with_ratio.filter(ratio__gt=1.0).count()  # ratio > 1的段落
        no_ratio_count = segments.filter(ratio__isnull=True).count()  # 没有ratio的段落

        # 计算进度百分比（ratio <= 1的段落）
        percentage = int((aligned_count / total) * 100) if total > 0 else 0

        return {
            'total': total,
            'aligned_count': aligned_count,
            'unaligned_count': unaligned_count,
            'no_ratio_count': no_ratio_count,
            'percentage': percentage
        }

    @property
    def audio_url(self):
        """返回音频文件URL - 优先返回人声音频，其次原始音频"""
        # 优先返回分离后的人声音频
        if self.vocal_audio_path:
            return self.vocal_audio_path.url
        # 其次返回原始音频
        if self.original_audio_path:
            return self.original_audio_path.url
        return None

    @property
    def background_audio_url(self):
        """返回背景音URL"""
        if self.background_audio_path:
            return self.background_audio_path.url
        return None

    @property
    def video_url(self):
        """返回视频文件URL"""
        if self.video_file_path:
            return self.video_file_path.url
        return None

    @property
    def mixed_audio_url(self):
        """返回混合音频URL"""
        if self.mixed_audio_path:
            return self.mixed_audio_path.url
        return None

    @property
    def final_video_url(self):
        """返回最终视频URL"""
        if self.final_video_path:
            return self.final_video_path.url
        return None
