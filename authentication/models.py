from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自定义用户模型，基于username + group_id + api_key认证
    """
    # 覆盖username字段，移除unique约束
    username = models.CharField(max_length=150, help_text="用户名")

    # 使用组合字段作为唯一标识
    email = models.CharField(max_length=254, unique=True, help_text="内部唯一标识")

    group_id = models.CharField(max_length=50, help_text="MiniMax Group ID")
    api_key = models.TextField(help_text="MiniMax API Key")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    # 使用email作为登录字段
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'group_id']

    class Meta:
        # 同一企业内用户名唯一，不同企业可以有相同用户名
        unique_together = ('username', 'group_id')

    def save(self, *args, **kwargs):
        # 自动生成email字段作为内部唯一标识
        if not self.email:
            self.email = f"{self.username}@{self.group_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.group_id})"


class UserConfig(models.Model):
    """
    用户全局配置
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config')
    api_endpoint = models.URLField(
        default="https://api.minimaxi.com",
        help_text="MiniMax API端点"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "用户配置"
        verbose_name_plural = "用户配置"

    def __str__(self):
        return f"{self.user.username}的配置"
