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
    group_id = "1747179187841536150"
    api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLmnZzno4oiLCJVc2VyTmFtZSI6IuadnOejiiIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzQ3MTc5MTg3ODQ5OTI0NzU4IiwiUGhvbmUiOiIxMzAyNTQ5MDQyMyIsIkdyb3VwSUQiOiIxNzQ3MTc5MTg3ODQxNTM2MTUwIiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiZGV2aW5AbWluaW1heGkuY29tIiwiQ3JlYXRlVGltZSI6IjIwMjQtMTItMjMgMTE6NTE6NTQiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.szVUN2AH7lJ9fQ3EYfzcLcamSCFAOye3Y6yO3Wj_tlNhnhBIYxEEMvZsVgH9mgOe6uhRczOqibmEMbVMUD_1DqtykrbD5klaB4_nhRnDl8fbaAf7m8B1OTRTUIiqgXRVglITenx3K_ugZ6teqiqypByJoLleHbZCSPWvy1-NaDiynb7qAsGzN1V6N4BOTNza1hL5PYdlrXLe2yjQv3YW8nOjQDIGCO1ZqnVBF0UghVaO4V-GZu1Z_0JnkLa7x_2ZXKXAe-LWhk9npwGFzQfLL3aH4oUzlsoEDGnuz3RZdZsFCe95MUiG8dCWfsxhVqlQ5GoFM3LQBAXuLZyqDpmSgg"

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