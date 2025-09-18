from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自定义用户模型，基于group_id和api_key认证
    """
    group_id = models.CharField(max_length=50, unique=True, help_text="MiniMax Group ID")
    api_key = models.TextField(help_text="MiniMax API Key")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

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
