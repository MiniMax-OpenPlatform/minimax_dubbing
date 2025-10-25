import uuid
from django.db import models
from projects.models import Project


class SpeakerDiarizationTask(models.Model):
    """说话人识别任务"""

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '完成'),
        ('failed', '失败'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='diarization_tasks',
        verbose_name='所属项目'
    )

    # 任务状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态'
    )
    progress = models.IntegerField(default=0, verbose_name='进度(0-100)')
    message = models.TextField(blank=True, verbose_name='当前消息')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    # 处理结果统计
    num_speakers_detected = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='检测到的说话人数量'
    )
    total_segments = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='总字幕片段数'
    )
    total_faces = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='检测到的人脸总数'
    )
    valid_faces = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='高质量人脸数'
    )

    # 聚类参数
    clustering_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='聚类参数'
    )
    # {
    #   "eps": 0.28,
    #   "min_samples": 5,
    #   "metric": "cosine"
    # }

    # 过滤统计
    filter_statistics = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='过滤统计'
    )
    # {
    #   "total_filtered": 702,
    #   "low_confidence": 123,
    #   "too_small": 456,
    #   "side_face": 78,
    #   "blurry": 45
    # }

    # API Trace IDs (可选，某些API提供商如阿里云不提供)
    vlm_trace_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='VLM Trace ID'
    )
    llm_trace_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='LLM Trace ID'
    )

    # 是否应用到项目
    is_applied = models.BooleanField(default=False, verbose_name='是否已应用')
    applied_at = models.DateTimeField(null=True, blank=True, verbose_name='应用时间')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '说话人识别任务'
        verbose_name_plural = '说话人识别任务'
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Task {self.id} - {self.project.name} - {self.get_status_display()}"


class SpeakerProfile(models.Model):
    """说话人档案"""

    task = models.ForeignKey(
        SpeakerDiarizationTask,
        on_delete=models.CASCADE,
        related_name='speakers',
        verbose_name='识别任务'
    )
    speaker_id = models.IntegerField(verbose_name='说话人ID')

    # VLM识别信息
    name = models.CharField(max_length=100, default='', verbose_name='姓名')
    role = models.CharField(max_length=100, blank=True, verbose_name='角色')
    gender = models.CharField(max_length=20, blank=True, verbose_name='性别')

    # 统计信息
    face_count = models.IntegerField(default=0, verbose_name='人脸数量')
    segment_count = models.IntegerField(default=0, verbose_name='出现片段数')
    segments = models.JSONField(default=list, verbose_name='出现的片段编号列表')
    # [1, 2, 5, 8, ...]

    # VLM详细分析
    appearance = models.JSONField(default=dict, blank=True, verbose_name='外貌特征')
    # {
    #   "clothing": "白色上衣搭配黑色裙子",
    #   "facial_features": "长发，面容姣好",
    #   "age_estimate": "20-30岁",
    #   "distinctive_features": "佩戴珍珠项链"
    # }

    character_analysis = models.JSONField(default=dict, blank=True, verbose_name='性格分析')
    # {
    #   "personality": "强势、自信",
    #   "importance": "非常高",
    #   "relationship": "与裴宴有情感线索",
    #   "dialogue_characteristics": "说话果断，充满决策感"
    # }

    # 代表人脸图片路径
    representative_images = models.JSONField(default=list, verbose_name='代表人脸图片')
    # ["faces/task_uuid/speaker_1_frame_0.jpg", "faces/task_uuid/speaker_1_frame_1.jpg"]

    # 平均置信度
    avg_confidence = models.FloatField(default=0.0, verbose_name='平均置信度')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        ordering = ['speaker_id']
        verbose_name = '说话人档案'
        verbose_name_plural = '说话人档案'
        unique_together = [['task', 'speaker_id']]
        indexes = [
            models.Index(fields=['task', 'speaker_id']),
        ]

    def __str__(self):
        return f"Speaker {self.speaker_id} - {self.name or '未命名'} (Task {self.task.id})"
