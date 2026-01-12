"""
线程管理器 - 统一管理所有后台线程和清理函数
"""

import threading
import asyncio
from typing import Callable, List, Optional
from src.util.logger import logger


class ThreadManager:
    """线程管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化线程管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._threads: List[threading.Thread] = []
        self._thread_configs: List[dict] = []  # 存储线程配置，延迟启动
        self._cleanup_functions: List[Callable] = []
        self._is_cleaning = False
        self._is_started = False
        logger.info("线程管理器初始化完成")
    
    def register_thread(
        self,
        target: Callable,
        name: Optional[str] = None,
        daemon: bool = True,
        **kwargs
    ) -> threading.Thread:
        """
        注册并启动一个后台线程（立即启动）
        
        Args:
            target: 线程目标函数
            name: 线程名称
            daemon: 是否为守护线程
            **kwargs: 传递给 Thread 的其他参数
        
        Returns:
            创建的线程对象
        """
        if self._is_cleaning:
            logger.warning(f"正在清理中，无法注册新线程: {name}")
            return None
        
        thread = threading.Thread(
            target=target,
            name=name or f"Thread-{len(self._threads)}",
            daemon=daemon,
            **kwargs
        )
        
        self._threads.append(thread)
        thread.start()
        logger.info(f"线程已启动: {thread.name} (ID: {thread.ident}, daemon={daemon})")
        
        return thread
    
    def register_thread_deferred(
        self,
        target: Callable,
        name: Optional[str] = None,
        daemon: bool = True,
        **kwargs
    ):
        """
        注册线程配置（延迟启动，由 start_all 统一启动）
        
        各个模块可以预先注册线程配置，主程序在适当的时候调用 start_all 统一启动
        
        Args:
            target: 线程目标函数
            name: 线程名称
            daemon: 是否为守护线程
            **kwargs: 传递给 Thread 的其他参数
        """
        if self._is_started:
            logger.warning(f"线程已全部启动，无法延迟注册: {name}")
            return
        
        config = {
            'target': target,
            'name': name or f"Thread-{len(self._thread_configs)}",
            'daemon': daemon,
            **kwargs
        }
        self._thread_configs.append(config)
        logger.info(f"线程配置已注册（延迟启动）: {name}")
    
    def start_all(self):
        """启动所有延迟注册的线程"""
        if self._is_started:
            logger.warning("线程已经全部启动过，跳过")
            return
        
        if not self._thread_configs:
            logger.info("没有延迟注册的线程")
            return
        
        logger.info(f"开始启动 {len(self._thread_configs)} 个延迟线程...")
        
        for config in self._thread_configs:
            thread = threading.Thread(**config)
            self._threads.append(thread)
            thread.start()
            logger.info(f"线程已启动: {thread.name} (ID: {thread.ident}, daemon={thread.daemon})")
        
        self._is_started = True
        logger.info("所有延迟线程启动完成")
    
    def register_cleanup(self, func: Callable):
        """
        注册清理函数
        
        Args:
            func: 清理函数（可以是同步或异步函数）
        """
        if func not in self._cleanup_functions:
            self._cleanup_functions.append(func)
            logger.info(f"清理函数已注册: {func.__name__}")
        else:
            logger.warning(f"清理函数已存在，跳过: {func.__name__}")
    
    async def cleanup_all(self):
        """执行所有清理操作"""
        if self._is_cleaning:
            logger.info("已经在清理中，跳过重复调用")
            return
        
        self._is_cleaning = True
        logger.info("开始清理线程管理器资源...")
        
        # 执行所有清理函数
        logger.info(f"执行 {len(self._cleanup_functions)} 个清理函数...")
        for cleanup_func in self._cleanup_functions:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
                logger.info(f"清理函数执行完成: {cleanup_func.__name__}")
            except Exception as e:
                logger.error(f"清理函数执行失败: {cleanup_func.__name__}, 错误: {e}", exc_info=True)
        
        # 等待所有非守护线程结束
        logger.info(f"等待 {len(self._threads)} 个线程结束...")
        active_threads = [t for t in self._threads if t.is_alive()]
        
        for thread in active_threads:
            if not thread.daemon:
                logger.info(f"等待线程结束: {thread.name}")
                thread.join(timeout=5)  # 最多等待5秒
                if thread.is_alive():
                    logger.warning(f"线程未在超时时间内结束: {thread.name}")
            else:
                logger.info(f"守护线程，无需等待: {thread.name}")
        
        logger.info("线程管理器清理完成")
    
    def get_thread_info(self) -> List[dict]:
        """
        获取所有线程的信息
        
        Returns:
            线程信息列表
        """
        thread_info = []
        for i, thread in enumerate(self._threads):
            thread_info.append({
                "index": i,
                "name": thread.name,
                "alive": thread.is_alive(),
                "daemon": thread.daemon,
                "ident": thread.ident
            })
        return thread_info
    
    def print_status(self):
        """打印线程状态"""
        logger.info("=" * 50)
        logger.info("线程管理器状态")
        logger.info("=" * 50)
        logger.info(f"注册的清理函数数量: {len(self._cleanup_functions)}")
        logger.info(f"注册的线程数量: {len(self._threads)}")
        logger.info("-" * 50)
        
        for i, thread in enumerate(self._threads):
            status = "运行中" if thread.is_alive() else "已停止"
            daemon_str = "守护" if thread.daemon else "非守护"
            logger.info(f"[{i}] {thread.name}: {status}, {daemon_str}, ID={thread.ident}")
        
        logger.info("=" * 50)


# 创建全局单例
thread_manager = ThreadManager()
