#!/usr/bin/env python3
"""
创建测试用户
"""
import os
import sys
import django
from django.conf import settings

# 设置Django环境
sys.path.append('/home/Devin/minimax_translation')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from authentication.models import User

def create_test_user():
    """创建测试用户"""
    # 从环境变量读取配置
    group_id = os.getenv('DEFAULT_GROUP_ID', 'your-group-id-here')
    api_key = os.getenv('DEFAULT_API_KEY', 'your-api-key-here')

    if group_id == 'your-group-id-here' or api_key == 'your-api-key-here':
        print("请设置环境变量 DEFAULT_GROUP_ID 和 DEFAULT_API_KEY")
        return None

    # 检查用户是否已存在
    try:
        user = User.objects.get(group_id=group_id)
        print(f"用户已存在: {user.email}")
        return user
    except User.DoesNotExist:
        pass

    # 创建新用户
    user = User.objects.create(
        email="devin@minimaxi.com",
        username="devin",
        group_id=group_id,
        api_key=api_key
    )

    print(f"测试用户创建成功:")
    print(f"  Email: {user.email}")
    print(f"  Username: {user.username}")
    print(f"  Group ID: {user.group_id}")
    print(f"  API Key: {user.api_key[:50]}...")

    return user

if __name__ == '__main__':
    create_test_user()