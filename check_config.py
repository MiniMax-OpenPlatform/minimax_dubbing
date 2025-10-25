#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, '/data1/devin/minimax_translation')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from authentication.models import User, UserConfig

print("=" * 60)
print("用户和配置状态检查")
print("=" * 60)

users = User.objects.all()
print(f"\n总用户数: {users.count()}")
print(f"总配置数: {UserConfig.objects.count()}")

for user in users[:10]:
    try:
        config = user.config
        print(f"\n用户: {user.username} (ID: {user.id})")
        print(f"  - 有配置: ✓")
        print(f"  - API Endpoint: {config.api_endpoint}")
        print(f"  - DashScope Key: {'已配置' if config.dashscope_api_key else '未配置'}")
    except UserConfig.DoesNotExist:
        print(f"\n用户: {user.username} (ID: {user.id})")
        print(f"  - 有配置: ✗ (需要创建)")

# 测试创建配置
print("\n" + "=" * 60)
print("测试配置创建")
print("=" * 60)

if users.exists():
    test_user = users.first()
    print(f"\n测试用户: {test_user.username}")

    config, created = UserConfig.objects.get_or_create(
        user=test_user
    )

    if created:
        print("✓ 配置已创建")
    else:
        print("✓ 配置已存在")

    print(f"配置ID: {config.id}")
    print(f"API Endpoint: {config.api_endpoint}")
