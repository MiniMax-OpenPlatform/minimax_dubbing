from django.apps import AppConfig


class LogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs'

    def ready(self):
        """应用启动时初始化日志收集器"""
        # 临时禁用日志收集器以解决启动问题
        # try:
        #     from backend.utils import setup_logging
        #     setup_logging()
        # except ImportError:
        #     pass
        pass