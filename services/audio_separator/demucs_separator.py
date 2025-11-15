"""
Demucs音频分离器实现

使用Facebook的Demucs模型进行人声分离
"""
import os
import shutil
import subprocess
import logging
from typing import Dict, Optional
from pathlib import Path
from .base_separator import BaseSeparator

logger = logging.getLogger(__name__)


class DemucsSeparator(BaseSeparator):
    """使用Demucs模型的音频分离器"""

    def __init__(self, device: str = 'cpu', model: str = 'htdemucs', jobs: Optional[int] = None):
        """
        初始化Demucs分离器

        Args:
            device: 设备类型 'cpu' 或 'cuda'
            model: 模型名称，htdemucs为标准高质量模型
            jobs: 并行任务数，None时自动检测
        """
        super().__init__(device)
        self.model = model
        self.shifts = 1  # CPU优化：减少shifts（默认10）
        self.segment = None  # 使用默认值

        # 自动检测最佳jobs值
        if jobs is None:
            self.jobs = self._auto_detect_jobs()
        else:
            self.jobs = jobs

        logger.info(f"Demucs配置: model={self.model}, device={self.device}, jobs={self.jobs}")

    def _get_container_cpu_limit(self) -> int:
        """
        获取容器 CPU 限制（优先读取 cgroup，否则使用 psutil）

        Returns:
            容器可用的 CPU 核心数
        """
        # 尝试 cgroup v2 (新版 Docker)
        try:
            with open('/sys/fs/cgroup/cpu.max') as f:
                content = f.read().strip()
                quota, period = content.split()
                quota = int(quota)
                period = int(period)

            if quota > 0 and period > 0:
                cpu_limit = quota // period
                logger.info(f"检测到容器 CPU 限制: {cpu_limit} 核 (cgroup v2)")
                return cpu_limit
        except (FileNotFoundError, ValueError, PermissionError) as e:
            logger.debug(f"无法读取 cgroup v2 CPU 限制: {e}")

        # 尝试 cgroup v1 (旧版 Docker)
        try:
            with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us') as f:
                quota = int(f.read().strip())
            with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us') as f:
                period = int(f.read().strip())

            if quota > 0 and period > 0:
                cpu_limit = quota // period
                logger.info(f"检测到容器 CPU 限制: {cpu_limit} 核 (cgroup v1)")
                return cpu_limit
        except (FileNotFoundError, ValueError, PermissionError) as e:
            logger.debug(f"无法读取 cgroup v1 CPU 限制: {e}")

        # 如果无法读取 cgroup，使用 psutil（物理核心数）
        try:
            import psutil
            cpu_count = psutil.cpu_count(logical=False) or 4
            logger.info(f"使用物理 CPU 核心数: {cpu_count} 核 (psutil)")
            return cpu_count
        except Exception as e:
            logger.warning(f"CPU 检测失败: {e}，使用默认值 4")
            return 4

    def _auto_detect_jobs(self) -> int:
        """
        自动检测最佳jobs值

        Returns:
            推荐的jobs值
        """
        try:
            import psutil

            # 获取容器实际可用的 CPU 核心数（而非宿主机 CPU）
            cpu_count = self._get_container_cpu_limit()

            # 获取可用内存（GB）
            mem_gb = psutil.virtual_memory().available / (1024**3)

            # 根据内存限制jobs（每job约2GB，保留30%内存）
            mem_limited_jobs = int(mem_gb * 0.7 / 2)

            # 取较小值，并限制在合理范围（超过16收益递减）
            optimal_jobs = max(1, min(cpu_count, mem_limited_jobs, 16))

            logger.info(f"资源检测: CPU={cpu_count}核, 可用内存={mem_gb:.1f}GB, 推荐jobs={optimal_jobs}")

            return optimal_jobs

        except ImportError:
            logger.warning("psutil未安装，使用默认jobs=4")
            return 4
        except Exception as e:
            logger.warning(f"自动检测jobs失败: {e}，使用默认jobs=4")
            return 4

    def is_available(self) -> bool:
        """检查Demucs是否可用"""
        try:
            result = subprocess.run(
                ['python', '-m', 'demucs', '--help'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Demucs不可用: {str(e)}")
            return False

    def separate(self, audio_path: str, output_dir: str) -> Dict[str, str]:
        """
        使用Demucs分离音频

        Args:
            audio_path: 输入音频文件路径
            output_dir: 输出目录

        Returns:
            Dict[str, str]: 分离后的文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            logger.info(f"开始Demucs分离: {audio_path}")
            logger.info(f"模型: {self.model}, 设备: {self.device}")

            # 构建Demucs命令（参考minimax-video-translation的实现）
            command = [
                'python', '-m', 'demucs.separate',
                '-n', self.model,
                '--two-stems', 'vocals',  # 只分离人声和伴奏
                '-d', self.device,
                '-j', str(self.jobs),  # 多进程并行加速
                '-o', output_dir,
                audio_path
            ]

            # 执行分离
            logger.info(f"执行命令: {' '.join(command)}")
            logger.info(f"使用 {self.jobs} 个并行进程进行人声分离（预计加速 {min(self.jobs, 8)}x）")

            # 设置环境变量限制每个进程的线程数，避免线程爆炸
            # 计算每个进程应使用的线程数 = CPU核心数 / jobs数
            cpu_count = self._get_container_cpu_limit()
            threads_per_process = max(1, cpu_count // self.jobs)

            env = os.environ.copy()
            env['OMP_NUM_THREADS'] = str(threads_per_process)
            env['MKL_NUM_THREADS'] = str(threads_per_process)
            env['OPENBLAS_NUM_THREADS'] = str(threads_per_process)
            env['NUMEXPR_NUM_THREADS'] = str(threads_per_process)

            logger.info(f"线程限制: 每个进程 {threads_per_process} 线程 (CPU={cpu_count}, jobs={self.jobs})")

            # 使用非阻塞方式读取输出
            import threading
            import queue

            def read_output(pipe, output_queue, prefix):
                """在单独线程中读取输出"""
                try:
                    for line in pipe:
                        if line.strip():
                            output_queue.put((prefix, line.strip()))
                finally:
                    pipe.close()

            process = subprocess.Popen(
                command,
                env=env,  # 传递环境变量
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # 行缓冲
            )

            # 创建输出队列和读取线程
            output_queue = queue.Queue()
            stderr_thread = threading.Thread(
                target=read_output,
                args=(process.stderr, output_queue, "Demucs")
            )
            stdout_thread = threading.Thread(
                target=read_output,
                args=(process.stdout, output_queue, "Demucs[OUT]")
            )

            stderr_thread.daemon = True
            stdout_thread.daemon = True
            stderr_thread.start()
            stdout_thread.start()

            # 实时输出日志并等待进程结束
            while process.poll() is None:
                try:
                    prefix, line = output_queue.get(timeout=0.1)
                    logger.info(f"{prefix}: {line}")
                except queue.Empty:
                    pass

            # 输出剩余的日志
            while not output_queue.empty():
                try:
                    prefix, line = output_queue.get_nowait()
                    logger.info(f"{prefix}: {line}")
                except queue.Empty:
                    break

            # 等待读取线程结束
            stderr_thread.join(timeout=1)
            stdout_thread.join(timeout=1)

            if process.returncode != 0:
                raise RuntimeError(f"Demucs分离失败，返回码: {process.returncode}")

            # 查找生成的文件
            # Demucs输出结构: output_dir/{model}/{audio_filename}/vocals.wav 和 no_vocals.wav
            audio_filename = Path(audio_path).stem
            model_output_dir = os.path.join(output_dir, self.model, audio_filename)

            vocals_path = os.path.join(model_output_dir, 'vocals.wav')
            background_path = os.path.join(model_output_dir, 'no_vocals.wav')

            # 验证文件是否生成
            if not os.path.exists(vocals_path):
                raise RuntimeError(f"人声文件未生成: {vocals_path}")
            if not os.path.exists(background_path):
                raise RuntimeError(f"背景音文件未生成: {background_path}")

            # 移动文件到目标位置（便于访问）
            final_vocals_path = os.path.join(output_dir, 'vocals.wav')
            final_background_path = os.path.join(output_dir, 'background.wav')

            shutil.copy2(vocals_path, final_vocals_path)
            shutil.copy2(background_path, final_background_path)

            logger.info(f"Demucs分离完成:")
            logger.info(f"  人声: {final_vocals_path} ({os.path.getsize(final_vocals_path)} bytes)")
            logger.info(f"  背景音: {final_background_path} ({os.path.getsize(final_background_path)} bytes)")

            return {
                'vocals': final_vocals_path,
                'background': final_background_path,
                'original': audio_path
            }

        except subprocess.TimeoutExpired:
            logger.error("Demucs分离超时")
            raise RuntimeError("分离超时，请尝试更短的音频")
        except Exception as e:
            logger.error(f"Demucs分离异常: {str(e)}")
            raise RuntimeError(f"分离失败: {str(e)}")
