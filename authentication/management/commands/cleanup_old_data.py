"""
数据自动清理命令

定期清理不活跃的项目和用户数据，释放存储空间。
- 删除N天未更新的项目及其所有关联数据（段落、说话人、音频文件等）
- 删除N天未登录的普通用户及其所有数据（项目、语音、配置等）
- 保留超级管理员账号

警告：此操作不可逆，请谨慎使用！建议先使用 --dry-run 预览。
"""
import os
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
from projects.models import Project
from system_monitor.models import SystemConfig

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '清理不活跃的项目和用户数据（谨慎使用！）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览模式：显示将要删除的数据，但不实际执行删除操作'
        )
        parser.add_argument(
            '--projects-days',
            type=int,
            help='项目清理天数（覆盖系统配置）'
        )
        parser.add_argument(
            '--users-days',
            type=int,
            help='用户清理天数（覆盖系统配置）'
        )
        parser.add_argument(
            '--only-projects',
            action='store_true',
            help='仅清理过期项目，不清理用户'
        )
        parser.add_argument(
            '--only-users',
            action='store_true',
            help='仅清理不活跃用户，不清理项目'
        )

    def handle(self, *args, **options):
        # 获取系统配置
        config = SystemConfig.get_config()

        # 判断是否启用自动清理
        if not config.enable_auto_cleanup_data and not options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  数据自动清理功能未启用！\n'
                    '   请在管理后台 "系统配置" 中启用 "启用数据自动清理" 选项\n'
                    '   或使用 --dry-run 参数预览清理效果'
                )
            )
            return

        # 确定清理天数
        projects_days = options['projects_days'] or config.cleanup_projects_after_days
        users_days = options['users_days'] or config.cleanup_users_after_days

        # 显示清理信息
        is_dry_run = options['dry_run']
        mode_text = '【预览模式】' if is_dry_run else '【执行模式】'

        self.stdout.write('')
        self.stdout.write(self.style.WARNING(f'🗑️  数据清理任务 {mode_text}'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'清理配置：')
        self.stdout.write(f'  - 项目清理天数: {projects_days} 天')
        self.stdout.write(f'  - 用户清理天数: {users_days} 天')
        self.stdout.write(f'  - 清理项目: {"否" if options["only_users"] else "是"}')
        self.stdout.write(f'  - 清理用户: {"否" if options["only_projects"] else "是"}')
        self.stdout.write('=' * 60)
        self.stdout.write('')

        # 统计信息
        stats = {
            'projects_deleted': 0,
            'users_deleted': 0,
            'files_deleted': 0,
            'files_size_mb': 0.0,
        }

        # 清理过期项目
        if not options['only_users']:
            self.stdout.write(f'📦 检查过期项目（{projects_days}天未更新）...')
            stats.update(self._cleanup_old_projects(projects_days, is_dry_run))
            self.stdout.write('')

        # 清理不活跃用户
        if not options['only_projects']:
            self.stdout.write(f'👤 检查不活跃用户（{users_days}天未登录）...')
            stats.update(self._cleanup_inactive_users(users_days, is_dry_run))
            self.stdout.write('')

        # 显示统计信息
        self._display_summary(stats, is_dry_run)

        # 记录日志
        if not is_dry_run:
            self._log_cleanup(stats, projects_days, users_days)

    def _cleanup_old_projects(self, days, dry_run=False):
        """清理过期项目"""
        cutoff_date = timezone.now() - timedelta(days=days)
        old_projects = Project.objects.filter(updated_at__lt=cutoff_date)

        count = old_projects.count()
        files_deleted = 0
        files_size_mb = 0.0

        if count == 0:
            self.stdout.write(self.style.SUCCESS('   ✅ 没有需要清理的过期项目'))
            return {'projects_deleted': 0, 'files_deleted': 0, 'files_size_mb': 0.0}

        self.stdout.write(f'   找到 {count} 个过期项目:')

        for project in old_projects:
            days_old = (timezone.now() - project.updated_at).days
            self.stdout.write(
                f'   - [{project.id}] {project.name} '
                f'(最后更新: {days_old}天前, 用户: {project.user.username})'
            )

            # 收集关联的媒体文件
            file_paths = self._collect_project_files(project)
            if file_paths:
                size_mb = sum(self._get_file_size(f) for f in file_paths) / (1024 * 1024)
                files_deleted += len(file_paths)
                files_size_mb += size_mb
                self.stdout.write(f'     → 关联文件: {len(file_paths)} 个, 约 {size_mb:.2f} MB')

        if not dry_run:
            with transaction.atomic():
                # 先删除文件
                for project in old_projects:
                    self._delete_project_files(project)

                # 再删除数据库记录（级联删除segments, speakers等）
                deleted_count = old_projects.delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ 已删除 {deleted_count} 个项目及其关联数据')
                )
        else:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  预览：将删除 {count} 个项目')
            )

        return {
            'projects_deleted': count if not dry_run else 0,
            'files_deleted': files_deleted,
            'files_size_mb': files_size_mb
        }

    def _cleanup_inactive_users(self, days, dry_run=False):
        """清理不活跃用户（保留超级管理员）"""
        cutoff_date = timezone.now() - timedelta(days=days)

        # 查询不活跃的普通用户（排除超级管理员）
        inactive_users = User.objects.filter(
            last_login__lt=cutoff_date,
            is_superuser=False  # 不删除超级管理员
        )

        count = inactive_users.count()
        files_deleted = 0
        files_size_mb = 0.0

        if count == 0:
            self.stdout.write(self.style.SUCCESS('   ✅ 没有需要清理的不活跃用户'))
            return {'users_deleted': 0, 'files_deleted': 0, 'files_size_mb': 0.0}

        self.stdout.write(f'   找到 {count} 个不活跃用户:')

        for user in inactive_users:
            days_inactive = (timezone.now() - user.last_login).days if user.last_login else 999
            project_count = user.projects.count()

            self.stdout.write(
                f'   - [{user.id}] {user.username} ({user.group_id}) '
                f'(最后登录: {days_inactive}天前, 项目数: {project_count})'
            )

            # 收集用户的所有文件
            user_files = []
            for project in user.projects.all():
                user_files.extend(self._collect_project_files(project))

            # 收集用户的语音克隆文件
            for voice_clone in user.voiceclonerecord_set.all():
                user_files.extend(self._collect_voice_clone_files(voice_clone))

            if user_files:
                size_mb = sum(self._get_file_size(f) for f in user_files) / (1024 * 1024)
                files_deleted += len(user_files)
                files_size_mb += size_mb
                self.stdout.write(f'     → 关联文件: {len(user_files)} 个, 约 {size_mb:.2f} MB')

        if not dry_run:
            with transaction.atomic():
                # 删除用户（级联删除所有关联数据：projects, segments, speakers, voices等）
                deleted_count = inactive_users.delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ 已删除 {deleted_count} 个用户及其所有数据')
                )
        else:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  预览：将删除 {count} 个用户')
            )

        return {
            'users_deleted': count if not dry_run else 0,
            'files_deleted': files_deleted,
            'files_size_mb': files_size_mb
        }

    def _collect_project_files(self, project):
        """收集项目的所有媒体文件路径"""
        files = []

        # 项目级别的文件
        file_fields = [
            'srt_file_path', 'video_file_path', 'mixed_audio_path',
            'final_video_path', 'original_audio_path', 'vocal_audio_path',
            'background_audio_path'
        ]

        for field_name in file_fields:
            file_field = getattr(project, field_name, None)
            if file_field:
                try:
                    if hasattr(file_field, 'path') and os.path.exists(file_field.path):
                        files.append(file_field.path)
                except ValueError:
                    # 文件路径无效
                    pass

        # 说话人识别的人脸图片
        for task in project.diarization_tasks.all():
            for speaker in task.speakers.all():
                if speaker.representative_images:
                    for img_path in speaker.representative_images:
                        full_path = os.path.join(settings.MEDIA_ROOT, img_path)
                        if os.path.exists(full_path):
                            files.append(full_path)

        return files

    def _collect_voice_clone_files(self, voice_clone):
        """收集语音克隆文件路径"""
        files = []
        file_fields = ['clone_audio_file', 'prompt_audio_file', 'demo_audio_file']

        for field_name in file_fields:
            file_field = getattr(voice_clone, field_name, None)
            if file_field:
                try:
                    if hasattr(file_field, 'path') and os.path.exists(file_field.path):
                        files.append(file_field.path)
                except ValueError:
                    pass

        return files

    def _delete_project_files(self, project):
        """删除项目的所有媒体文件"""
        files = self._collect_project_files(project)
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    # 尝试删除空目录
                    parent_dir = os.path.dirname(file_path)
                    if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'     ⚠️  文件删除失败: {file_path} - {str(e)}')
                )

    def _get_file_size(self, file_path):
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0
        except Exception:
            return 0

    def _display_summary(self, stats, is_dry_run):
        """显示清理统计信息"""
        self.stdout.write('=' * 60)
        self.stdout.write('📊 清理统计:')
        self.stdout.write(f'  - 项目: {stats["projects_deleted"]} 个')
        self.stdout.write(f'  - 用户: {stats["users_deleted"]} 个')
        self.stdout.write(f'  - 文件: {stats["files_deleted"]} 个')
        self.stdout.write(f'  - 空间: {stats["files_size_mb"]:.2f} MB')
        self.stdout.write('=' * 60)

        if is_dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  这是预览模式，没有实际删除任何数据。\n'
                    '   要执行实际清理，请去掉 --dry-run 参数'
                )
            )
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ 数据清理完成！'))

    def _log_cleanup(self, stats, projects_days, users_days):
        """记录清理操作日志"""
        try:
            log_message = (
                f"数据自动清理完成 - "
                f"删除项目: {stats['projects_deleted']}个({projects_days}天), "
                f"删除用户: {stats['users_deleted']}个({users_days}天), "
                f"释放空间: {stats['files_size_mb']:.2f}MB"
            )

            logger.info(log_message, extra={'stats': stats})
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  日志记录失败: {str(e)}')
            )
