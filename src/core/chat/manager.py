"""
聊天管理器
负责聊天逻辑、消息收发和用户交互

核心职责：
1. 接收协议管理器提供的连接信息
2. 根据协议类型创建对应的客户端
3. 管理聊天会话
"""

import aiohttp
import asyncio
import threading
from typing import Dict, Any, Optional
from src.core.protocol import protocol_manager
from src.core.prompt import prompt_manager
from src.util.logger import logger

# maim_message 相关导入
try:
    from maim_message import Router, RouteConfig, TargetConfig, MessageBase, BaseMessageInfo, Seg, UserInfo, FormatInfo
    MAIM_MESSAGE_AVAILABLE = True
except ImportError:
    logger.warning("maim_message 库未安装，Maim 协议将不可用")
    MAIM_MESSAGE_AVAILABLE = False
    Router = None
    RouteConfig = None
    TargetConfig = None
    MessageBase = None
    BaseMessageInfo = None
    Seg = None
    UserInfo = None
    FormatInfo = None


class ChatManager:
    """聊天管理器"""
    
    def __init__(self):
        self._protocol_manager = protocol_manager
        self._initialized = False
        self._current_task = 'chat'

        # WebSocket Router（用于 maim）
        self._maim_router: Optional[Router] = None
        self._maim_platform: Optional[str] = None
        self._maim_thread: Optional[threading.Thread] = None
    
    async def initialize(self, task_type: str = 'chat') -> bool:
        """
        初始化聊天管理器
        
        Args:
            task_type: 任务类型，默认 'chat'
        
        Returns:
            是否初始化成功
        """
        try:
            # 1. 初始化协议管理器
            if not self._protocol_manager.is_initialized():
                success = await self._protocol_manager.initialize()
                if not success:
                    logger.error("协议管理器初始化失败")
                    return False
            
            # 2. 获取连接信息
            connection_info = self._protocol_manager.get_task_connection_info(task_type)
            if not connection_info:
                logger.error(f"无法获取任务 '{task_type}' 的连接信息")
                return False
            
            # 3. 根据协议类型初始化客户端
            protocol_type = connection_info['protocol_type']
            
            if protocol_type == 'maim':
                # WebSocket 协议
                success = await self._initialize_maim(connection_info)
            elif protocol_type in ['openai', 'gemini']:
                # HTTP API 协议
                success = await self._initialize_http(connection_info)
            else:
                logger.error(f"不支持的协议类型: {protocol_type}")
                return False
            
            if not success:
                logger.warning("初始化失败，但聊天管理器仍可用")
            
            self._current_task = task_type
            self._initialized = True
            
            logger.info("聊天管理器初始化成功")
            logger.info(f"  - 任务类型: {task_type}")
            logger.info(f"  - 协议类型: {protocol_type}")
            logger.info(f"  - 模型: {connection_info.get('model_name')}")
            
            return True
            
        except Exception as e:
            logger.error(f"聊天管理器初始化失败: {e}", exc_info=True)
            return False
    
    async def _initialize_http(self, connection_info: Dict[str, Any]) -> bool:
        """
        初始化 HTTP 客户端（OpenAI/Gemini）

        HTTP 客户端不需要预先初始化，每次请求时临时创建 session

        Args:
            connection_info: 连接信息

        Returns:
            是否初始化成功
        """
        logger.info("[OK] HTTP 客户端准备就绪（按需创建）")
        return True
    
    async def _initialize_maim(self, connection_info: Dict[str, Any]) -> bool:
        """
        初始化 Maim WebSocket 客户端（使用 maim_message.Router）

        Args:
            connection_info: 连接信息

        Returns:
            是否初始化成功
        """
        if not MAIM_MESSAGE_AVAILABLE:
            logger.error("maim_message 库未安装，无法使用 Maim 协议")
            return False

        try:
            # 获取连接配置
            ws_url = connection_info['base_url']
            platform = connection_info.get('platform', 'desktop-pet')
            api_key = connection_info.get('api_key', '')

            logger.info(f"初始化 Maim WebSocket 连接: {ws_url}")

            # 创建路由配置
            target_config = TargetConfig(url=ws_url, token=api_key if api_key else None)
            route_config = RouteConfig(route_config={platform: target_config})

            # 创建 Router
            self._maim_router = Router(config=route_config, custom_logger=logger)
            self._maim_platform = platform

            # 注册消息处理器（接收回复）
            self._maim_router.register_message_handler(self._handle_maim_message)

            # 在后台线程中启动 Router（run() 是阻塞方法）
            def run_router():
                """在后台线程中运行 Router"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._maim_router.run())
                except Exception as e:
                    logger.error(f"Router 运行失败: {e}", exc_info=True)

            self._maim_thread = threading.Thread(target=run_router, daemon=True, name="MaimRouter")
            self._maim_thread.start()

            # 等待连接建立
            import time
            max_wait = 5  # 最多等待 5 秒
            for i in range(max_wait * 10):
                if self._maim_router.check_connection(platform):
                    logger.info("Maim WebSocket 连接已建立")
                    logger.info(f"  - 平台: {platform}")
                    logger.info(f"  - 地址: {ws_url}")
                    return True
                time.sleep(0.1)

            logger.warning("Maim WebSocket 连接建立超时")
            return False

        except Exception as e:
            logger.error(f"Maim WebSocket 连接初始化失败: {e}", exc_info=True)
            self._maim_router = None
            return False
    
    async def send_message(self, content: str, user_id: str = '0', user_name: str = '麦麦') -> bool:
        """
        发送消息

        Args:
            content: 消息内容
            user_id: 用户 ID
            user_name: 用户昵称

        Returns:
            是否发送成功
        """
        if not self._initialized:
            logger.warning("聊天管理器未初始化")
            return False

        try:
            # 获取当前连接信息
            connection_info = self._protocol_manager.get_task_connection_info(self._current_task)

            if not connection_info:
                logger.warning("无法获取连接信息")
                return False

            protocol_type = connection_info['protocol_type']

            # 根据协议类型发送
            if protocol_type == 'maim':
                success = await self._send_maim(content, connection_info, user_id, user_name)
            elif protocol_type in ['openai', 'gemini']:
                success = await self._send_http(content, connection_info, user_id, user_name)
            else:
                logger.error(f"不支持的协议类型: {protocol_type}")
                return False

            if success:
                logger.info(f"消息发送成功: {content[:50]}...")
            else:
                logger.warning("消息发送失败")

            return success

        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            return False
    
    async def _send_http(self, content: str, connection_info: Dict[str, Any], user_id: str, user_name: str) -> bool:
        """
        通过 HTTP 发送消息（每次请求临时创建 session）

        Args:
            content: 消息内容
            connection_info: 连接信息
            user_id: 用户 ID
            user_name: 用户昵称

        Returns:
            是否发送成功
        """
        try:
            url = f"{connection_info['base_url']}/chat/completions"
            headers = {
                "Authorization": f"Bearer {connection_info['api_key']}",
                "Content-Type": "application/json"
            }

            # 使用 prompt_manager 构建消息列表（包含人设信息）
            messages = prompt_manager.build_messages(content, user_id, user_name)

            # 构建请求数据
            data = {
                "model": connection_info['model_identifier'],
                "messages": messages,
                "stream": False
            }

            # 每次请求临时创建 session，请求完成后自动关闭
            timeout = aiohttp.ClientTimeout(total=connection_info.get('timeout', 30))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        reply = result['choices'][0]['message']['content']

                        # 触发 UI 信号
                        from src.frontend.signals import signals_bus
                        signals_bus.message_received.emit(reply)

                        logger.debug(f"收到回复: {reply[:50]}...")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"HTTP 请求失败: {response.status} - {error}")
                        return False

        except Exception as e:
            logger.error(f"发送 HTTP 请求失败: {e}", exc_info=True)
            return False
    
    def _handle_maim_message(self, message: MessageBase):
        """
        处理从 Maim WebSocket 接收到的消息

        Args:
            message: MessageBase 对象
        """
        try:
            # 提取消息段
            message_segment = message.message_segment
            seg_type = message_segment.type
            seg_data = message_segment.data

            # 处理不同类型的消息
            if seg_type == 'text':
                # 文本消息
                reply_content = seg_data
            elif seg_type == 'seglist':
                # 复合消息（多个段落）
                text_parts = []
                if isinstance(seg_data, list):
                    for seg in seg_data:
                        if hasattr(seg, 'type') and seg.type == 'text':
                            text_parts.append(seg.data if isinstance(seg.data, str) else str(seg.data))
                        elif isinstance(seg, dict) and seg.get('type') == 'text':
                            text_parts.append(seg.get('data', ''))
                reply_content = ''.join(text_parts) if text_parts else '[复合消息]'
            elif seg_type in ['image', 'emoji']:
                # 图片或表情包（暂不支持显示）
                reply_content = f'[{seg_type}]'
            else:
                # 未知类型
                reply_content = f'[{seg_type}]'

            logger.debug(f"收到 Maim 回复: {reply_content[:50]}...")

            # 触发 UI 信号
            from src.frontend.signals import signals_bus
            signals_bus.message_received.emit(reply_content)

        except Exception as e:
            logger.error(f"处理 Maim 消息失败: {e}", exc_info=True)

    async def _send_maim(self, content: str, connection_info: Dict[str, Any], user_id: str, user_name: str) -> bool:
        """
        通过 WebSocket 发送消息（使用 maim_message.Router）

        Args:
            content: 消息内容
            connection_info: 连接信息
            user_id: 用户 ID
            user_name: 用户昵称

        Returns:
            是否发送成功
        """
        if not self._maim_router or not self._maim_platform:
            logger.warning("Maim WebSocket 未初始化")
            return False

        try:
            # 从主配置读取平台标识和用户名
            from config import load_config
            main_config = load_config()
            platform = main_config.platform
            # 优先使用 userNickname，如果为空则使用 Nickname
            actual_user_name = main_config.userNickname if main_config.userNickname else main_config.Nickname

            # 构建 UserInfo
            user_info = UserInfo(
                platform=platform,
                user_id=user_id,
                user_nickname=actual_user_name,
                user_cardname=''
            )

            # 构建 FormatInfo
            format_info = FormatInfo(
                content_format=['text'],
                accept_format=['text']
            )

            # 构建 BaseMessageInfo
            message_info = BaseMessageInfo(
                platform=platform,
                message_id='',
                time=0.0,
                user_info=user_info,
                format_info=format_info,
                additional_config={
                    "maimcore_reply_probability_gain": 1  # 回复概率增益
                }
            )

            # 构建 Seg（消息内容）
            seg = Seg(type='text', data=content)

            # 构建 MessageBase
            message = MessageBase(
                message_info=message_info,
                message_segment=seg,
                raw_message=content
            )

            # 发送消息
            await self._maim_router.send_message(message)

            logger.debug(f"Maim 消息已发送: {content[:50]}...")
            return True

        except Exception as e:
            logger.error(f"发送 Maim 消息失败: {e}", exc_info=True)
            return False
    
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理 WebSocket Router
            if self._maim_router:
                await self._maim_router.stop()
                self._maim_router = None
                logger.info("Maim WebSocket 连接已关闭")

            # 等待后台线程结束
            if self._maim_thread and self._maim_thread.is_alive():
                self._maim_thread.join(timeout=2)
                self._maim_thread = None

            self._initialized = False
            logger.info("聊天管理器已清理")

        except Exception as e:
            logger.error(f"清理资源失败: {e}", exc_info=True)


# 全局单例
chat_manager = ChatManager()