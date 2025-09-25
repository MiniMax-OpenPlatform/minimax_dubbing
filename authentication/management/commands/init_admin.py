"""
创建默认管理员账号的Django管理命令
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = '创建系统默认管理员账号'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='管理员用户名 (默认: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='管理员邮箱 (默认: admin@example.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='管理员密码 (默认: admin123)'
        )
        parser.add_argument(
            '--group-id',
            type=str,
            default='system_admin',
            help='管理员组ID (默认: system_admin)'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            default='admin_api_key_12345',
            help='管理员API密钥 (默认: admin_api_key_12345)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建管理员账号（会删除已存在的账号）'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        group_id = options['group_id']
        api_key = options['api_key']
        force = options['force']

        # 检查是否已存在管理员账号
        existing_admin = User.objects.filter(username=username).first()
        existing_email = User.objects.filter(email=email).first()

        if existing_admin or existing_email:
            if force:
                self.stdout.write(
                    self.style.WARNING(f'删除已存在的管理员账号: {username}')
                )
                if existing_admin:
                    existing_admin.delete()
                if existing_email and existing_email != existing_admin:
                    existing_email.delete()
            else:
                if existing_admin:
                    self.stdout.write(
                        self.style.WARNING(f'管理员账号 "{username}" 已存在')
                    )
                if existing_email:
                    self.stdout.write(
                        self.style.WARNING(f'邮箱 "{email}" 已被使用')
                    )
                self.stdout.write(
                    self.style.WARNING('使用 --force 选项强制重新创建')
                )
                return

        # 创建管理员账号
        try:
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                group_id=group_id,
                api_key=api_key
            )

            self.stdout.write(
                self.style.SUCCESS(f'✅ 成功创建管理员账号')
            )
            self.stdout.write(f'   用户名: {username}')
            self.stdout.write(f'   邮箱: {email}')
            self.stdout.write(f'   密码: {password}')
            self.stdout.write(f'   组ID: {group_id}')
            self.stdout.write(f'   API密钥: {api_key}')
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(f'🌐 管理后台地址: http://localhost:5172/admin/')
            )

        except Exception as e:
            raise CommandError(f'创建管理员账号失败: {str(e)}')