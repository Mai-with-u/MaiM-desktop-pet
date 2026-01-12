"""
Maim 协议实现
基于 maim_message 库的 WebSocket 通信协议
"""

import asyncio
from typing import Dict, Any, Callable, Optional
from maim_message import Router, RouteConfig, TargetConfig
from src.core.protocols.interfaces import IProtocol
from src.util.logger import logger
from src.util.message_util import (
    dict_to_message_base,
    message_base_to_dict,
    convert_message_format,
    is_valid_message,
    extract_text_content
)


class MaimProtocol(IProtocol):
    """Maim 协议实现"""
    
    def __init__(self):
        self._router: Optional[Router] = None
        self._config: Dict[str, Any] = {}
        self._message_handler: Optional[Callable] = None
        self._is_connected = False
        self._is_running = False
        self._run_task: Optional[asyncio.Task] = None
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化 Maim 协议
        
        Args:
            config: 协议配置，包含：
                - url: WebSocket 服务器地址
                - token: 认证令牌（可选）
                - platform: 平台名称
        
        Returns:
            是否初始化成功
        """
        try:
            self._config = config
            
            # 构建路由配置
            url = config.get('url', 'ws://127.0.0.1:19000/ws')
            platform = config.get('platform', 'default')
            token = config.get('token', None)
            
            route_config = RouteConfig(
                route_config={
                    platform: TargetConfig(
                        url=url,
                        token=token,
                    )
                }
            )
            
            # 创建路由器
            self._router = Router(route_config)
            logger.info(f"Maim 协议初始化成功: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Maim 协议初始化失败: {e}", exc_info=True)
            return False
    
    async def connect(self) -> bool:
        """
        建立连接并启动路由器
        
        Returns:
            是否连接成功
        """
        if not self._router:
            logger.error("协议未初始化")
            return False
        
        try:
            # 注册消息处理器
            if self._message_handler:
                self._router.register_class_handler(self._message_handler)
            
            # 启动路由器
            self._is_running = True
            self._run_task = asyncio.create_task(self._run_router())
            
            # 等待连接建立
            await asyncio.sleep(2)
            
            self._is_connected = True
            logger.info("Maim 协议连接成功")
            return True
            
        except Exception as e:
            logger.error(f"Maim 协议连接失败: {e}", exc_info=True)
            self._is_connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        try:
            # 先取消运行任务，避免 event loop 冲突
            if self._run_task and not self._run_task.done():
                self._run_task.cancel()
                try:
                    await self._run_task
                except asyncio.CancelledError:
                    logger.info("路由器运行任务已取消")
                except RuntimeError as e:
                    # 如果任务属于另一个 event loop，忽略错误
                    if "attached to a different loop" in str(e):
                        logger.info("路由器任务属于另一个事件循环，跳过等待")
                    else:
                        raise
            
            # 停止路由器（不等待，因为可能属于另一个 event loop）
            if self._router:
                try:
                    # 尝试停止路由器，但不等待完成
                    # 因为 router.stop() 内部可能包含对 _monitor_task 的 await
                    # 而那个任务可能属于另一个事件循环
                    stop_task = asyncio.create_task(self._router.stop())
                    # 不等待 stop_task 完成，让它在后台清理
                except RuntimeError as e:
                    if "attached to a different loop" in str(e):
                        logger.info("路由器停止失败：事件循环不匹配，跳过")
                    else:
                        raise
            
            self._is_running = False
            self._is_connected = False
            
            logger.info("Maim 协议已断开连接")
            
        except Exception as e:
            logger.error(f"断开连接时出错: {e}", exc_info=True)
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息
        
        Args:
            message: 消息字典，格式与 maim_message 兼容
        
        Returns:
            是否发送成功
        """
        if not self._router or not self._is_connected:
            logger.warning("协议未连接，无法发送消息")
            return False
        
        try:
            # 检查消息格式
            if not is_valid_message(message):
                logger.warning(f"消息格式不正确: {message}")
                return False
            
            # 使用消息转换工具将字典转换为 MessageBase 对象
            message_base = dict_to_message_base(message)
            
            # 使用 router 的 send_message 方法发送 MessageBase 对象
            await self._router.send_message(message_base)
            
            text_content = extract_text_content(message)
            logger.debug(f"发送消息成功: {text_content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            return False
    
    def register_message_handler(self, handler: Callable):
        """
        注册消息处理器
        
        Args:
            handler: 消息处理函数，签名: async handler(message: Dict[str, Any])
        """
        # 包装消息处理器，添加格式转换
        self._message_handler = self._create_message_handler_wrapper(handler)
        logger.info("Maim 协议消息处理器已注册")
    
    def _create_message_handler_wrapper(self, handler: Callable):
        """
        创建消息处理器包装器，负责格式转换
        
        Args:
            handler: 原始消息处理器
        
        Returns:
            包装后的消息处理器
        """
        async def wrapper(message: Dict[str, Any]):
            # 转换消息格式
            converted_message = self._convert_message_format(message)
            
            # 调用原始处理器
            await handler(converted_message)
        
        return wrapper
    
    def _convert_message_format(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换消息格式
        
        将 Maim 特有的消息格式（如 seglist）转换为统一格式
        
        Args:
            message: 原始消息（MessageBase 对象或字典）
        
        Returns:
            转换后的消息（字典格式）
        """
        try:
            # 如果是 MessageBase 对象，先转换为字典
            if hasattr(message, 'message_info'):
                message = message_base_to_dict(message)
            
            # 使用消息转换工具处理格式
            return convert_message_format(message)
            
        except Exception as e:
            logger.error(f"消息格式转换失败: {e}", exc_info=True)
            # 如果转换失败，尝试返回原始消息
            if hasattr(message, 'message_info'):
                try:
                    return message_base_to_dict(message)
                except:
                    pass
            return message
    
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected
    
    def get_name(self) -> str:
        """获取协议名称"""
        return "Maim"
    
    async def cleanup(self):
        """清理资源"""
        await self.disconnect()
        self._router = None
        self._message_handler = None
        logger.info("Maim 协议资源已清理")
    
    async def _run_router(self):
        """运行路由器（内部方法）"""
        try:
            await self._router.run()
        except asyncio.CancelledError:
            logger.info("路由器运行已取消")
            raise
        except RuntimeError as e:
            # 忽略 maim_message 库在取消时产生的特定错误
            if "await wasn't used with future" in str(e):
                logger.debug("路由器停止时的预期错误（任务已取消）")
            else:
                logger.error(f"路由器运行出错: {e}", exc_info=True)
            self._is_connected = False
        except Exception as e:
            logger.error(f"路由器运行出错: {e}", exc_info=True)
            self._is_connected = False
