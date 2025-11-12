"""
内存监控和OOM保护工具

提供装饰器和工具函数，用于监控内存使用并防止OOM
"""
import logging
import psutil
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


def check_available_memory() -> float:
    """
    获取当前可用内存（GB）

    Returns:
        可用内存大小（GB）
    """
    try:
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        return available_gb
    except Exception as e:
        logger.warning(f"获取内存信息失败: {e}")
        return 0.0


def log_memory_status(prefix: str = ""):
    """
    记录当前内存状态到日志

    Args:
        prefix: 日志前缀
    """
    try:
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        used_gb = mem.used / (1024**3)
        available_gb = mem.available / (1024**3)
        percent = mem.percent

        log_msg = (f"{prefix}内存状态: "
                  f"总计{total_gb:.1f}GB, "
                  f"已用{used_gb:.1f}GB ({percent:.1f}%), "
                  f"可用{available_gb:.1f}GB")

        if percent > 80:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    except Exception as e:
        logger.warning(f"记录内存状态失败: {e}")


def require_memory(required_gb: float, task_name: str = ""):
    """
    内存检查装饰器：在执行前检查内存是否充足

    Args:
        required_gb: 所需内存（GB）
        task_name: 任务名称（用于日志）

    Usage:
        @require_memory(required_gb=32, task_name="Demucs人声分离")
        def my_task():
            # 任务代码
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                available_gb = check_available_memory()

                task_label = task_name or func.__name__

                # 检查内存是否充足
                if available_gb < required_gb:
                    error_msg = (f"[{task_label}] 内存不足: "
                               f"需要{required_gb:.1f}GB, "
                               f"可用{available_gb:.1f}GB")
                    logger.error(error_msg)
                    log_memory_status(f"[{task_label}] ")
                    raise MemoryError(error_msg)

                # 内存充足，记录状态并执行
                logger.info(f"[{task_label}] 内存检查通过: "
                          f"需要{required_gb:.1f}GB, "
                          f"可用{available_gb:.1f}GB")

                # 执行任务前记录内存状态
                mem_before = psutil.virtual_memory().used / (1024**3)

                result = func(*args, **kwargs)

                # 执行任务后记录内存状态
                mem_after = psutil.virtual_memory().used / (1024**3)
                mem_delta = mem_after - mem_before

                logger.info(f"[{task_label}] 任务完成，内存增量: {mem_delta:.1f}GB")

                return result

            except MemoryError:
                # 重新抛出 MemoryError
                raise
            except Exception as e:
                logger.error(f"[{task_name or func.__name__}] 执行失败: {e}")
                raise

        return wrapper
    return decorator


def get_safe_demucs_jobs() -> int:
    """
    根据当前可用内存计算安全的Demucs jobs值

    Returns:
        推荐的jobs值
    """
    try:
        available_gb = check_available_memory()

        # 每job约2GB，保留30%内存
        safe_gb = available_gb * 0.7
        max_jobs = int(safe_gb / 2)

        # 限制在[1, 16]范围
        optimal_jobs = max(1, min(max_jobs, 16))

        logger.info(f"安全Demucs jobs计算: 可用内存{available_gb:.1f}GB, 推荐jobs={optimal_jobs}")

        return optimal_jobs

    except Exception as e:
        logger.warning(f"计算安全jobs失败: {e}，返回默认值4")
        return 4


def get_safe_batch_size() -> int:
    """
    根据当前可用内存计算安全的FaceNet batch_size

    Returns:
        推荐的batch_size值
    """
    try:
        available_gb = check_available_memory()

        # 保守策略：为系统和其他任务预留50%内存
        safe_gb = available_gb * 0.5

        # 每batch约5MB
        max_batch_size = int((safe_gb * 1024) / 5)

        # 选择2的幂次
        for size in [256, 128, 64, 32, 16, 8]:
            if size <= max_batch_size:
                logger.info(f"安全batch_size计算: 可用内存{available_gb:.1f}GB, 推荐batch_size={size}")
                return size

        logger.info(f"安全batch_size计算: 可用内存{available_gb:.1f}GB, 返回最小值8")
        return 8

    except Exception as e:
        logger.warning(f"计算安全batch_size失败: {e}，返回默认值32")
        return 32


class MemoryMonitor:
    """内存监控器（上下文管理器）"""

    def __init__(self, task_name: str = ""):
        """
        初始化内存监控器

        Args:
            task_name: 任务名称
        """
        self.task_name = task_name
        self.mem_before = 0.0

    def __enter__(self):
        """进入上下文时记录内存"""
        try:
            self.mem_before = psutil.virtual_memory().used / (1024**3)
            log_memory_status(f"[{self.task_name}] 开始前 ")
        except Exception as e:
            logger.warning(f"记录开始内存失败: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时记录内存变化"""
        try:
            mem_after = psutil.virtual_memory().used / (1024**3)
            mem_delta = mem_after - self.mem_before

            if exc_type is None:
                logger.info(f"[{self.task_name}] 完成，内存增量: {mem_delta:.1f}GB")
            else:
                logger.error(f"[{self.task_name}] 失败，内存增量: {mem_delta:.1f}GB, 异常: {exc_val}")

            log_memory_status(f"[{self.task_name}] 结束后 ")

        except Exception as e:
            logger.warning(f"记录结束内存失败: {e}")

        # 不抑制异常
        return False
