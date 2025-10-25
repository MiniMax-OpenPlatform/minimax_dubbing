#!/usr/bin/env python3
"""
修复注册失败但用户已创建的问题

问题描述:
- 旧版本代码中，注册时 API Key 验证通过，用户创建成功
- 但创建 UserConfig 时失败（因为数据库缺少字段）
- 导致用户存在但没有关联的 config，功能异常

使用方法:
    python fix_incomplete_users.py
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from authentication.models import User, UserConfig


def fix_incomplete_users():
    """修复没有配置的用户"""
    print("=" * 60)
    print("检查并修复没有配置的用户")
    print("=" * 60)

    # 查找所有用户
    all_users = User.objects.all()
    print(f"\n总共有 {all_users.count()} 个用户")

    # 找出没有配置的用户
    users_without_config = []
    for user in all_users:
        if not hasattr(user, 'config'):
            users_without_config.append(user)
            print(f"  ❌ {user.username} ({user.group_id}) - 缺少配置")
        else:
            print(f"  ✅ {user.username} ({user.group_id}) - 配置正常")

    if not users_without_config:
        print("\n🎉 所有用户都有配置，无需修复！")
        return

    print(f"\n发现 {len(users_without_config)} 个用户缺少配置，开始修复...")

    # 为每个用户创建配置
    fixed_count = 0
    for user in users_without_config:
        try:
            UserConfig.objects.create(user=user)
            print(f"  ✅ 已为 {user.username} 创建配置")
            fixed_count += 1
        except Exception as e:
            print(f"  ❌ 为 {user.username} 创建配置失败: {str(e)}")

    print(f"\n修复完成！成功修复 {fixed_count}/{len(users_without_config)} 个用户")

    # 验证
    print("\n" + "=" * 60)
    print("验证修复结果")
    print("=" * 60)

    remaining_issues = 0
    for user in User.objects.all():
        if not hasattr(user, 'config'):
            print(f"  ❌ {user.username} ({user.group_id}) - 仍然缺少配置")
            remaining_issues += 1
        else:
            # 检查配置的字段
            config = user.config
            print(f"  ✅ {user.username} ({user.group_id}) - 配置正常")
            print(f"     - api_endpoint: {config.api_endpoint}")
            print(f"     - dashscope_api_key: {'已配置' if config.dashscope_api_key else '未配置'}")
            print(f"     - aliyun_access_key_id: {'已配置' if config.aliyun_access_key_id else '未配置'}")

    if remaining_issues == 0:
        print(f"\n🎉 所有 {all_users.count()} 个用户的配置都已修复！")
    else:
        print(f"\n⚠️  还有 {remaining_issues} 个用户存在问题，请手动检查")


if __name__ == '__main__':
    try:
        fix_incomplete_users()
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
