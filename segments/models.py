from django.db import models
from projects.models import Project


class Segment(models.Model):
    """
    段落模型
    """
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('translating', '翻译中'),
        ('translated', '已翻译'),
        ('tts_processing', 'TTS处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('silent', '静音'),
    ]

    EMOTION_CHOICES = [
        ('auto', '自动'),
        ('happy', '高兴'),
        ('sad', '悲伤'),
        ('angry', '愤怒'),
        ('fearful', '恐惧'),
        ('disgusted', '厌恶'),
        ('surprised', '惊讶'),
        ('calm', '平静'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='segments')
    index = models.PositiveIntegerField(help_text="段落序号")

    # 时间戳
    start_time = models.FloatField(help_text="开始时间(秒)")
    end_time = models.FloatField(help_text="结束时间(秒)")

    # 说话人和文本
    speaker = models.CharField(max_length=50, default="SPEAKER_00", help_text="说话人")
    original_text = models.TextField(help_text="原文本")
    translated_text = models.TextField(blank=True, help_text="翻译文本")

    # 音频相关
    voice_id = models.CharField(max_length=100, blank=True, help_text="音色ID")
    emotion = models.CharField(max_length=20, choices=EMOTION_CHOICES, default='auto', help_text="情绪参数")
    speed = models.FloatField(default=1.0, help_text="语速参数(0-2.0]")

    # 音频文件
    original_audio_url = models.URLField(blank=True, help_text="原音频URL")
    translated_audio_url = models.URLField(blank=True, help_text="翻译音频URL")

    # 时长数据
    t_tts_duration = models.FloatField(null=True, blank=True, help_text="TTS音频时长(秒)")
    target_duration = models.FloatField(null=True, blank=True, help_text="目标时长(秒)")
    ratio = models.FloatField(null=True, blank=True, help_text="时长比例(T_tts/目标时长)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "段落"
        verbose_name_plural = "段落"
        ordering = ['project', 'index']
        unique_together = ['project', 'index']

    def __str__(self):
        return f"{self.project.name} - 段落{self.index}: {self.original_text[:30]}..."

    @property
    def duration(self):
        """返回段落时长"""
        return self.end_time - self.start_time

    @property
    def time_display(self):
        """返回时间戳显示格式"""
        start_min, start_sec = divmod(int(self.start_time), 60)
        start_ms = int((self.start_time % 1) * 1000)
        end_min, end_sec = divmod(int(self.end_time), 60)
        end_ms = int((self.end_time % 1) * 1000)

        return f"{start_min:02d}:{start_sec:02d}.{start_ms:03d} → {end_min:02d}:{end_sec:02d}.{end_ms:03d}"

    @property
    def is_aligned(self):
        """检查时间戳是否对齐成功"""
        if self.t_tts_duration is None or self.target_duration is None:
            return False
        return self.t_tts_duration <= self.target_duration

    def calculate_ratio(self):
        """计算并更新时长比例"""
        if self.t_tts_duration and self.target_duration:
            self.ratio = round(self.t_tts_duration / self.target_duration, 2)
            return self.ratio
        return None
