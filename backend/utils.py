import logging
import threading
from typing import List, Dict
from datetime import datetime
import json

class InMemoryLogHandler(logging.Handler):
    """
    内存日志处理器，收集日志到内存中供API调用
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, max_logs=1000):
        # 单例模式，确保只有一个实例
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_logs=1000):
        if self._initialized:
            return
        super().__init__()
        self.max_logs = max_logs
        self.logs = []
        self.lock = threading.Lock()
        self._initialized = True

    def emit(self, record):
        with self.lock:
            try:
                # 格式化日志记录
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': self.format(record),
                    'pathname': getattr(record, 'pathname', ''),
                    'lineno': getattr(record, 'lineno', 0),
                    'funcName': getattr(record, 'funcName', ''),
                }

                self.logs.append(log_entry)

                # 保持日志数量在限制内
                if len(self.logs) > self.max_logs:
                    self.logs = self.logs[-self.max_logs:]

            except Exception:
                pass  # 静默处理格式化错误

    def get_logs(self, limit=None, level_filter=None, search=None):
        """获取日志，支持过滤"""
        with self.lock:
            logs = self.logs.copy()

        # 反转列表，最新的在前面
        logs.reverse()

        # 级别过滤
        if level_filter:
            logs = [log for log in logs if log['level'].lower() == level_filter.lower()]

        # 搜索过滤
        if search:
            search_lower = search.lower()
            logs = [log for log in logs if
                   search_lower in log['message'].lower() or
                   search_lower in log['logger'].lower()]

        # 限制数量
        if limit:
            logs = logs[:limit]

        return logs

    def clear_logs(self):
        """清空日志"""
        with self.lock:
            self.logs.clear()


# 全局日志收集器实例 - 确保和Django配置中的是同一个实例
memory_log_handler = InMemoryLogHandler(max_logs=2000)

def setup_logging():
    """设置日志收集"""
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    memory_log_handler.setFormatter(formatter)
    # 设置最低级别
    memory_log_handler.setLevel(logging.DEBUG)

    # 添加到Django的根日志器
    root_logger = logging.getLogger('')
    root_logger.addHandler(memory_log_handler)
    root_logger.setLevel(logging.DEBUG)

    # 也添加到具体的loggers
    loggers = [
        'django',
        'django.server',
        'django.request',
        'projects',
        'segments',
        'logs',
        'authentication',
        'minimax_client',
        'timestamp_aligner',
        'audio_processor',
        'views'
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(memory_log_handler)
        logger.setLevel(logging.DEBUG)

    # 手动添加一条测试日志
    test_logger = logging.getLogger('backend.utils')
    test_logger.info("日志收集器初始化完成")

    # 添加更多测试日志来验证
    test_logger.warning("测试WARNING级别日志")
    test_logger.error("测试ERROR级别日志")
    test_logger.debug("测试DEBUG级别日志")