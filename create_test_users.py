#!/usr/bin/env python3
"""
创建测试用户脚本
"""
import os
import sys
import django

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def create_test_users():
    """创建测试用户"""

    test_users = [
        {
            'username': 'alice',
            'group_id': 'company_a',
            'api_key': 'test_api_key_alice_123',
            'password': 'password123'
        },
        {
            'username': 'bob',
            'group_id': 'company_a',
            'api_key': 'test_api_key_bob_456',
            'password': 'password123'
        },
        {
            'username': 'charlie',
            'group_id': 'company_b',
            'api_key': 'test_api_key_charlie_789',
            'password': 'password123'
        },
        {
            'username': 'alice',  # 同名但不同公司
            'group_id': 'company_c',
            'api_key': 'test_api_key_alice_c_999',
            'password': 'password123'
        }
    ]

    with transaction.atomic():
        for user_data in test_users:
            try:
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    group_id=user_data['group_id'],
                    defaults={
                        'api_key': user_data['api_key']
                    }
                )

                if created:
                    user.set_password(user_data['password'])
                    user.save()
                    print(f"✅ 创建用户: {user_data['username']}@{user_data['group_id']}")
                else:
                    # 更新API Key（如果需要）
                    user.api_key = user_data['api_key']
                    user.save()
                    print(f"📝 更新用户: {user_data['username']}@{user_data['group_id']}")

            except Exception as e:
                print(f"❌ 创建用户失败: {user_data['username']}@{user_data['group_id']} - {str(e)}")

def list_users():
    """列出所有用户"""
    users = User.objects.all().order_by('group_id', 'username')
    print("\n📋 用户列表:")
    print("=" * 80)
    print(f"{'ID':<5} {'用户名':<15} {'企业Group ID':<15} {'API Key':<30} {'创建时间'}")
    print("-" * 80)

    for user in users:
        print(f"{user.id:<5} {user.username:<15} {user.group_id:<15} {user.api_key[:20]+'...':<30} {user.created_at.strftime('%Y-%m-%d %H:%M')}")

    print(f"\n📊 总计: {users.count()} 个用户")

if __name__ == "__main__":
    print("🚀 开始创建测试用户...")
    create_test_users()
    list_users()

    print("\n💡 测试说明:")
    print("- alice@company_a 和 bob@company_a 属于同一企业但不能互相访问项目")
    print("- alice@company_a 和 alice@company_c 是不同企业的同名用户")
    print("- charlie@company_b 是独立企业用户")
    print("\n🔑 登录测试凭据:")
    print("用户名: alice, Group ID: company_a, API Key: test_api_key_alice_123")
    print("用户名: bob, Group ID: company_a, API Key: test_api_key_bob_456")
    print("用户名: charlie, Group ID: company_b, API Key: test_api_key_charlie_789")
    print("用户名: alice, Group ID: company_c, API Key: test_api_key_alice_c_999")