"""
日志管理模块

功能：
1. 主日志文件 (pet.log) - 按天轮转，长期保存
2. 最近一次启动日志 (last_run.log) - 每次启动清空，仅保存当前运行的日志
3. 控制台输出 - 实时查看
"""

import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class StreamToLogger:
    """自定义日志处理器，将 print 输出重定向到日志"""
    
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self._writing = False

    def write(self, message):
        if self._writing:
            return
        if message.strip():  # 忽略空行
            self._writing = True
            try:
                self.logger.log(self.log_level, message.strip())
            except Exception:
                pass
            finally:
                self._writing = False

    def flush(self):
        pass  # 不需要实现

    def isatty(self):
        return False

    def fileno(self):
        raise OSError("StreamToLogger does not expose a file descriptor")


class LastRunHandler(logging.FileHandler):
    """
    自定义 Handler，专门用于保存最近一次运行的日志
    
    特点：
    - 每次程序启动时清空文件
    - 仅保存当前运行会话的日志
    - 方便查看最近一次运行的完整日志
    """
    
    def __init__(self, filename, mode='w', encoding='utf-8'):
        """
        初始化最近运行日志处理器
        
        Args:
            filename: 日志文件路径
            mode: 文件打开模式，默认 'w'（每次启动清空）
            encoding: 文件编码
        """
        super().__init__(filename, mode=mode, encoding=encoding)
        self.session_start_time = datetime.now()
        
    def emit(self, record):
        """
        发送日志记录
        
        在日志开头添加启动时间标记
        """
        if self.stream is None:
            self.stream = self._open()

        # 如果是第一条日志，添加启动时间标记
        if self.stream.tell() == 0:
            startup_banner = (
                f"\n{'=' * 80}\n"
                f"程序启动时间: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"{'=' * 80}\n\n"
            )
            self.stream.write(startup_banner)
        
        super().emit(record)


class SafeConsoleHandler(logging.StreamHandler):
    """Console handler that tolerates Windows console encoding limits."""

    def emit(self, record):
        try:
            msg = self.format(record) + self.terminator
            encoding = getattr(self.stream, "encoding", None) or "utf-8"
            safe_msg = msg.encode(encoding, errors="replace").decode(encoding, errors="replace")
            self.stream.write(safe_msg)
            self.flush()
        except Exception:
            pass


def setup_logger():
    """
    配置并初始化日志系统
    
    Returns:
        logging.Logger: 配置好的 logger 实例
    """
    # 确保日志目录存在
    log_dir = './logs'
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            logging.error(f"创建日志目录失败: {e}")
    
    # 创建根 logger
    logger = logging.getLogger('pet')
    logger.setLevel(logging.DEBUG)
    
    # 清除现有的 handlers（避免重复添加）
    logger.handlers.clear()
    
    # 日志格式
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%m-%d %H:%M:%S'
    )
    
    # 1. 控制台 Handler（实时输出）
    console_handler = SafeConsoleHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上级别
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # 2. 主日志文件 Handler（长期保存，按天轮转）
    main_log_path = os.path.join(log_dir, 'pet.log')
    main_handler = TimedRotatingFileHandler(
        filename=main_log_path,
        when='midnight',  # 每天午夜轮转
        interval=1,
        backupCount=30,  # 保留最近30天的日志
        encoding='utf-8'
    )
    main_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
    main_handler.setFormatter(detailed_formatter)
    logger.addHandler(main_handler)
    
    # 3. 最近一次运行日志 Handler（每次启动清空）
    last_run_log_path = os.path.join(log_dir, 'last_run.log')
    last_run_handler = LastRunHandler(
        filename=last_run_log_path,
        mode='w',  # 每次启动清空文件
        encoding='utf-8'
    )
    last_run_handler.setLevel(logging.DEBUG)  # 记录所有级别
    last_run_handler.setFormatter(detailed_formatter)
    logger.addHandler(last_run_handler)
    
    # 记录初始化完成
    logger.info("=" * 60)
    logger.info("日志系统初始化完成")
    logger.info(f"主日志文件: {main_log_path}")
    logger.info(f"最近运行日志: {last_run_log_path}")
    logger.info("=" * 60)
    
    return logger


# 初始化 logger
logger = setup_logger()

# 重定向 sys.stdout 和 sys.stderr 到日志记录器
# 注意：这会影响所有 print 语句
sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

# 导出 logger
__all__ = ['logger']
