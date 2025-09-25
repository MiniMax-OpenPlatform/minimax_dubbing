"""
系统完整初始化命令
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from system_monitor.models import SystemConfig

User = get_user_model()


class Command(BaseCommand):
    help = '初始化整个翻译系统（数据库迁移、管理员账号、系统配置）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrate',
            action='store_true',
            help='跳过数据库迁移'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='管理员用户名 (默认: admin)'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin123',
            help='管理员密码 (默认: admin123)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 开始初始化 MiniMax Translation 系统...')
        )
        self.stdout.write('')

        # 1. 数据库迁移
        if not options['skip_migrate']:
            self.stdout.write('📊 执行数据库迁移...')
            try:
                call_command('migrate', verbosity=0)
                self.stdout.write(self.style.SUCCESS('✅ 数据库迁移完成'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ 数据库迁移失败: {str(e)}'))
                return
        else:
            self.stdout.write(self.style.WARNING('⚠️  跳过数据库迁移'))

        self.stdout.write('')

        # 2. 创建管理员账号
        self.stdout.write('👤 创建管理员账号...')
        try:
            call_command(
                'init_admin',
                username=options['admin_username'],
                password=options['admin_password'],
                verbosity=0
            )
            self.stdout.write(self.style.SUCCESS('✅ 管理员账号创建完成'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  管理员账号创建跳过: {str(e)}'))

        self.stdout.write('')

        # 3. 创建系统配置
        self.stdout.write('⚙️  创建系统配置...')
        try:
            system_config, created = SystemConfig.objects.get_or_create(
                id=1,
                defaults={
                    'batch_translate_request_interval': 1.0,  # 请求间隔1秒
                    'max_concurrent_translate_tasks': 3,      # 最大3个并发任务
                    'task_timeout_minutes': 30,               # 任务超时30分钟
                    'enable_detailed_logging': True,          # 启用详细日志
                    'auto_cleanup_completed_tasks': True,     # 自动清理已完成任务
                    'cleanup_interval_hours': 24,             # 24小时清理一次
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS('✅ 系统配置创建完成'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  系统配置已存在，跳过创建'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 系统配置创建失败: {str(e)}'))

        self.stdout.write('')

        # 4. 显示初始化完成信息
        self.stdout.write(self.style.SUCCESS('🎉 系统初始化完成！'))
        self.stdout.write('')
        self.stdout.write('📋 初始化信息:')
        self.stdout.write(f'   管理员用户名: {options["admin_username"]}')
        self.stdout.write(f'   管理员密码: {options["admin_password"]}')
        self.stdout.write('')
        self.stdout.write('🌐 访问地址:')
        self.stdout.write('   前端应用: http://localhost:5173/')
        self.stdout.write('   后端API: http://localhost:5172/api/')
        self.stdout.write('   管理后台: http://localhost:5172/admin/')
        self.stdout.write('')
        self.stdout.write('🔧 启动命令:')
        self.stdout.write('   后端: python manage.py runserver 0.0.0.0:5172')
        self.stdout.write('   前端: cd frontend && npm run dev')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('系统已准备就绪，开始使用吧！ 🚀'))