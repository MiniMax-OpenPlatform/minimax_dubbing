"""
批量翻译任务管理
支持异步执行和进度跟踪
"""
import logging
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

class BatchTranslateTask:
    """批量翻译任务类"""

    def __init__(self, task_id: str, project_id: int, segment_ids: list, user_api_key: str = None, user_group_id: str = None):
        self.task_id = task_id
        self.project_id = project_id
        self.segment_ids = segment_ids
        self.user_api_key = user_api_key
        self.user_group_id = user_group_id

        # 进度状态
        self.status = 'pending'  # pending, running, completed, failed, cancelled
        self.total = len(segment_ids)
        self.completed = 0
        self.failed = 0
        self.current_segment_id = None
        self.current_segment_text = None

        # 时间统计
        self.start_time = None
        self.end_time = None
        self.estimated_time_remaining = None

        # 错误信息
        self.error_messages = []
        self.last_error = None

        # 控制标志
        self.should_stop = False
        self.thread = None

    def start(self):
        """启动异步翻译任务"""
        if self.status != 'pending':
            return False

        self.status = 'running'
        self.start_time = timezone.now()

        # 在新线程中执行翻译
        self.thread = threading.Thread(target=self._execute_translation)
        self.thread.daemon = True
        self.thread.start()

        logger.info(f"[Task {self.task_id}] 批量翻译任务已启动，共{self.total}个段落")
        return True

    def stop(self):
        """停止翻译任务"""
        self.should_stop = True
        if self.status == 'running':
            self.status = 'cancelled'
            logger.info(f"[Task {self.task_id}] 批量翻译任务已取消")

    def _execute_translation(self):
        """执行翻译的内部方法"""
        try:
            from .models import Project
            from segments.models import Segment
            from services.clients.minimax_client import MiniMaxClient
            from system_monitor.models import SystemConfig, TaskMonitor

            # 获取系统配置
            config = SystemConfig.get_config()

            # 创建或更新任务监控记录
            project = Project.objects.get(id=self.project_id)
            monitor, created = TaskMonitor.objects.get_or_create(
                task_id=self.task_id,
                defaults={
                    'task_type': 'batch_translate',
                    'project_id': self.project_id,
                    'project_name': project.name,
                    'total_segments': self.total,
                    'start_time': timezone.now(),
                    'status': 'running'
                }
            )

            if not created:
                monitor.status = 'running'
                monitor.start_time = timezone.now()
                monitor.save()

            # 获取段落
            segments = Segment.objects.filter(
                id__in=self.segment_ids,
                project=project
            ).order_by('index')

            # 初始化翻译客户端 - 使用用户的API Key
            client = MiniMaxClient(api_key=self.user_api_key, group_id=self.user_group_id)
            target_lang_display = project.get_target_lang_display()
            custom_vocabulary = project.custom_vocabulary or []

            for segment in segments:
                # 检查是否需要停止
                if self.should_stop:
                    break

                try:
                    self.current_segment_id = segment.id
                    self.current_segment_text = segment.original_text[:50] + "..." if len(segment.original_text) > 50 else segment.original_text

                    # 检查是否有原文
                    if not segment.original_text or not segment.original_text.strip():
                        logger.warning(f"[Task {self.task_id}] 段落{segment.index}没有原文，跳过")
                        continue

                    logger.info(f"[Task {self.task_id}] 开始翻译段落{segment.index}: {self.current_segment_text}")

                    # 调用真实翻译API
                    try:
                        result = client.translate(
                            text=segment.original_text,
                            target_language=target_lang_display,
                            custom_vocabulary=custom_vocabulary
                        )
                        logger.info(f"[Task {self.task_id}] 段落{segment.index}翻译API调用完成")
                    except Exception as api_error:
                        logger.error(f"[Task {self.task_id}] 段落{segment.index}翻译API调用失败: {str(api_error)}")
                        result = {
                            'success': False,
                            'error': str(api_error)
                        }

                    # 处理翻译结果
                    if isinstance(result, dict) and result.get('success'):
                        segment.translated_text = result['translation']
                        segment.save()
                        self.completed += 1
                        logger.info(f"[Task {self.task_id}] 段落{segment.index}翻译成功")
                    else:
                        self.failed += 1
                        error_msg = f"段落{segment.index}翻译失败: {result}"
                        self.error_messages.append(error_msg)
                        self.last_error = error_msg
                        logger.error(f"[Task {self.task_id}] {error_msg}")

                except Exception as e:
                    self.failed += 1
                    error_msg = f"段落{segment.index}翻译异常: {str(e)}"
                    self.error_messages.append(error_msg)
                    self.last_error = error_msg
                    logger.error(f"[Task {self.task_id}] {error_msg}")

                # 更新监控记录
                monitor.completed_segments = self.completed
                monitor.failed_segments = self.failed
                monitor.current_segment_text = self.current_segment_text
                if self.error_messages:
                    monitor.error_message = '\n'.join(self.error_messages[-5:])  # 保留最近5个错误
                monitor.save()

                # 更新预计剩余时间
                self._update_estimated_time()

                # 避免API请求过于频繁 - 使用数据库配置的请求间隔
                request_interval = config.batch_translate_request_interval
                if self.completed < self.total and not self.should_stop:  # 最后一个请求不需要等待
                    if config.enable_detailed_logging:
                        logger.debug(f"[Task {self.task_id}] 等待{request_interval}秒后处理下一个段落")
                    time.sleep(request_interval)

            # 任务完成，更新监控记录
            if self.should_stop:
                self.status = 'cancelled'
                monitor.status = 'cancelled'
            else:
                self.status = 'completed'
                monitor.status = 'completed'
                self.end_time = timezone.now()

            monitor.end_time = timezone.now()
            monitor.completed_segments = self.completed
            monitor.failed_segments = self.failed
            monitor.save()

            logger.info(f"[Task {self.task_id}] 批量翻译完成，成功{self.completed}个，失败{self.failed}个")

        except Exception as e:
            self.status = 'failed'
            self.last_error = f"任务执行失败: {str(e)}"
            self.error_messages.append(self.last_error)

            # 更新监控记录为失败状态
            try:
                from system_monitor.models import TaskMonitor
                monitor = TaskMonitor.objects.get(task_id=self.task_id)
                monitor.status = 'failed'
                monitor.error_message = str(e)
                monitor.end_time = timezone.now()
                monitor.save()
            except Exception:
                pass  # 监控记录更新失败不影响主任务

            logger.error(f"[Task {self.task_id}] 任务执行失败: {str(e)}")

    def _update_estimated_time(self):
        """更新预计剩余时间"""
        if self.start_time and self.completed > 0:
            elapsed = (timezone.now() - self.start_time).total_seconds()
            avg_time_per_item = elapsed / self.completed
            remaining_items = self.total - self.completed - self.failed
            self.estimated_time_remaining = avg_time_per_item * remaining_items

    def get_progress_info(self) -> Dict[str, Any]:
        """获取进度信息"""
        progress_percentage = 0
        if self.total > 0:
            progress_percentage = int(((self.completed + self.failed) / self.total) * 100)

        return {
            'task_id': self.task_id,
            'project_id': self.project_id,
            'status': self.status,
            'total': self.total,
            'completed': self.completed,
            'failed': self.failed,
            'progress_percentage': progress_percentage,
            'current_segment_id': self.current_segment_id,
            'current_segment_text': self.current_segment_text,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'estimated_time_remaining': self.estimated_time_remaining,
            'error_messages': self.error_messages[-5:],  # 只返回最后5个错误
            'last_error': self.last_error
        }


class BatchTranslateTaskManager:
    """批量翻译任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, BatchTranslateTask] = {}
        self._lock = threading.Lock()

    def create_task(self, project_id: int, segment_ids: list, user_api_key: str = None, user_group_id: str = None) -> str:
        """创建新的批量翻译任务"""
        task_id = f"translate_{project_id}_{int(time.time())}"

        with self._lock:
            # 停止同一项目的其他任务
            self.stop_project_tasks(project_id)

            # 创建新任务
            task = BatchTranslateTask(task_id, project_id, segment_ids, user_api_key, user_group_id)
            self.tasks[task_id] = task

            logger.info(f"创建批量翻译任务: {task_id}, 项目{project_id}, {len(segment_ids)}个段落")
            return task_id

    def start_task(self, task_id: str) -> bool:
        """启动任务（考虑并发限制）"""
        with self._lock:
            from system_monitor.models import SystemConfig

            task = self.tasks.get(task_id)
            if not task:
                return False

            # 检查并发限制
            config = SystemConfig.get_config()
            running_tasks = sum(1 for t in self.tasks.values() if t.status == 'running')

            if running_tasks >= config.max_concurrent_translate_tasks:
                logger.warning(f"[Task {task_id}] 任务启动失败：已达到最大并发数 {config.max_concurrent_translate_tasks}")
                return False

            return task.start()

    def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.stop()
                return True
            return False

    def stop_project_tasks(self, project_id: int):
        """停止指定项目的所有任务"""
        with self._lock:
            for task in self.tasks.values():
                if task.project_id == project_id and task.status == 'running':
                    task.stop()

    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度"""
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                return task.get_progress_info()
            return None

    def get_project_tasks(self, project_id: int) -> list:
        """获取项目的所有任务"""
        with self._lock:
            return [
                task.get_progress_info()
                for task in self.tasks.values()
                if task.project_id == project_id
            ]

    def cleanup_completed_tasks(self):
        """清理已完成的任务"""
        with self._lock:
            completed_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status in ['completed', 'failed', 'cancelled']
                and task.end_time
                and (timezone.now() - task.end_time).total_seconds() > 3600  # 1小时后清理
            ]

            for task_id in completed_tasks:
                del self.tasks[task_id]
                logger.info(f"清理已完成任务: {task_id}")


# 全局任务管理器实例
task_manager = BatchTranslateTaskManager()