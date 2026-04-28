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
import time
import uuid
import concurrent.futures
from typing import Dict, Any, Optional, List, Tuple
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


def _safe_emit_signal(signal_bus, signal_name: str, *args):
    """安全地发送信号，处理导入失败和信号不存在的情况"""
    try:
        if signal_bus is None:
            return
        signal = getattr(signal_bus, signal_name, None)
        if signal is not None and hasattr(signal, 'emit'):
            signal.emit(*args)
    except Exception as e:
        logger.error(f"发送信号失败: {signal_name}, 错误: {e}")


class ChatManager:
    """聊天管理器"""
    
    def __init__(self):
        self._protocol_manager = protocol_manager
        self._initialized = False
        self._current_task = 'chat'
        self._current_connection_key: Optional[tuple] = None
        self._switch_lock = asyncio.Lock()

        # WebSocket Router（用于 maim）
        self._maim_router: Optional[Router] = None
        self._maim_platform: Optional[str] = None
        self._maim_thread: Optional[threading.Thread] = None
        self._maim_loop: Optional[asyncio.AbstractEventLoop] = None
        self._maim_loop_ready: Optional[threading.Event] = None
        self._maim_startup_error: Optional[str] = None
    
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
            
            success = await self._activate_first_available_model(task_type)
            if not success:
                logger.error(f"任务 '{task_type}' 没有可用的聊天连接")
                self._initialized = False
                return False

            self._current_task = task_type
            self._initialized = True

            connection_info = self._protocol_manager.get_task_connection_info(task_type)
            logger.info("聊天管理器初始化成功")
            logger.info(f"  - 任务类型: {task_type}")
            logger.info(f"  - 协议类型: {connection_info.get('protocol_type') if connection_info else '未知'}")
            logger.info(f"  - 模型: {connection_info.get('model_name') if connection_info else '未知'}")

            return True
            
        except Exception as e:
            logger.error(f"聊天管理器初始化失败: {e}", exc_info=True)
            return False

    async def _activate_first_available_model(self, task_type: str, start_index: Optional[int] = None) -> bool:
        """从任务候选模型中选择第一个可初始化的连接"""
        candidates = self._ordered_candidates(task_type, start_index)
        if not candidates:
            logger.error(f"任务 '{task_type}' 没有可用候选模型")
            return False

        for connection_info in candidates:
            protocol_type = connection_info.get('protocol_type')
            model_index = connection_info.get('model_index', 0)

            logger.info("=" * 60)
            logger.info(f"尝试协议: {protocol_type}")
            logger.info(f"  模型: {connection_info.get('model_name', '未知')}")
            logger.info(f"  供应商: {connection_info.get('provider_name', '未知')}")
            logger.info("=" * 60)

            if await self._prepare_connection(connection_info):
                self._protocol_manager.set_active_task_model(task_type, model_index)
                self._current_task = task_type
                self._current_connection_key = self._connection_key(connection_info)
                return True

        return False

    def _ordered_candidates(self, task_type: str, start_index: Optional[int] = None) -> List[Dict[str, Any]]:
        """按当前索引开始，循环返回任务候选连接"""
        candidates = self._protocol_manager.get_task_connection_candidates(task_type)
        if not candidates:
            return []

        if start_index is None:
            start_index = self._protocol_manager.get_active_model_index(task_type)
        if start_index < 0 or start_index >= len(candidates):
            start_index = 0

        return candidates[start_index:] + candidates[:start_index]

    def _connection_key(self, connection_info: Dict[str, Any]) -> tuple:
        """用于判断连接是否需要重建的稳定键"""
        return (
            connection_info.get('protocol_type'),
            connection_info.get('base_url'),
            connection_info.get('api_key'),
            connection_info.get('platform'),
            connection_info.get('model_name'),
        )

    async def _prepare_connection(self, connection_info: Dict[str, Any]) -> bool:
        """按协议准备连接，并清理不再需要的旧连接"""
        protocol_type = connection_info.get('protocol_type')
        if protocol_type == 'maim':
            return await self._initialize_maim(connection_info)
        if protocol_type in ['openai', 'gemini']:
            await self._cleanup_maim()
            return await self._initialize_http(connection_info)

        logger.error(f"不支持的协议类型: {protocol_type}")
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
            ws_url = connection_info.get('base_url')
            if not ws_url:
                logger.error("连接信息中缺少 base_url")
                return False

            platform = connection_info.get('platform', 'desktop-pet')
            api_key = connection_info.get('api_key', '')
            connection_key = self._connection_key(connection_info)

            if (
                self._maim_router
                and self._maim_platform == platform
                and self._current_connection_key == connection_key
                and self._is_maim_connected()
            ):
                logger.info(f"Maim WebSocket 已连接，复用现有连接: {platform}")
                return True

            await self._cleanup_maim()

            logger.info(f"初始化 Maim WebSocket 连接: {ws_url}")

            # 创建路由配置
            target_config = TargetConfig(url=ws_url, token=api_key if api_key else None)
            route_config = RouteConfig(route_config={platform: target_config})

            # 创建 Router
            self._maim_router = Router(config=route_config, custom_logger=logger)
            self._maim_platform = platform

            # 注册消息处理器（接收回复）
            self._maim_router.register_message_handler(self._handle_maim_message)

            # 线程启动状态跟踪
            self._maim_startup_error = None
            self._maim_loop_ready = threading.Event()

            # 在后台线程中启动 Router（run() 是阻塞方法）
            def run_router():
                """在后台线程中运行 Router"""
                loop = asyncio.new_event_loop()
                self._maim_loop = loop
                self._maim_loop_ready.set()
                try:
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._maim_router.run())
                except asyncio.CancelledError:
                    logger.info("Maim Router 已取消")
                except Exception as e:
                    self._maim_startup_error = str(e)
                    logger.error(f"Router 运行失败: {e}", exc_info=True)
                finally:
                    try:
                        pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
                        for task in pending:
                            task.cancel()
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    except Exception as cleanup_error:
                        logger.debug(f"Maim Router 事件循环清理异常: {cleanup_error}", exc_info=True)
                    finally:
                        loop.close()
                        if self._maim_loop is loop:
                            self._maim_loop = None

            self._maim_thread = threading.Thread(target=run_router, daemon=True, name="MaimRouter")
            self._maim_thread.start()

            if not self._maim_loop_ready.wait(timeout=2):
                logger.error("Maim Router 事件循环启动超时")
                return False

            # 等待连接建立（使用 asyncio.sleep 保持异步特性）
            max_wait = 5  # 最多等待 5 秒
            for i in range(max_wait * 10):
                if self._maim_startup_error:
                    logger.error(f"Maim WebSocket 启动失败: {self._maim_startup_error}")
                    return False
                if self._is_maim_connected():
                    logger.info("Maim WebSocket 连接已建立")
                    logger.info(f"  - 平台: {platform}")
                    logger.info(f"  - 地址: {ws_url}")
                    self._current_connection_key = connection_key
                    return True
                await asyncio.sleep(0.1)

            if self._maim_startup_error:
                logger.error(f"Maim WebSocket 启动失败: {self._maim_startup_error}")
                return False

            logger.warning("Maim WebSocket 连接建立超时")
            await self._cleanup_maim()
            return False

        except Exception as e:
            logger.error(f"Maim WebSocket 连接初始化失败: {e}", exc_info=True)
            await self._cleanup_maim()
            return False

    def _is_maim_connected(self) -> bool:
        """检查当前 Maim Router 是否已经连接"""
        try:
            if not self._maim_router or not self._maim_platform:
                return False
            return self._maim_router.check_connection(self._maim_platform)
        except Exception as e:
            logger.debug(f"检查 Maim 连接状态失败: {e}")
            return False

    async def _run_on_maim_loop(self, coro, timeout: Optional[float] = None):
        """把协程投递到 Maim Router 所在线程的事件循环执行"""
        if not self._maim_loop or not self._maim_loop.is_running():
            raise RuntimeError("Maim Router 事件循环未运行")

        future = asyncio.run_coroutine_threadsafe(coro, self._maim_loop)
        wrapped = asyncio.wrap_future(future)
        if timeout:
            return await asyncio.wait_for(wrapped, timeout=timeout)
        return await wrapped

    async def _cleanup_maim(self):
        """清理 Maim Router，确保停止发生在它自己的事件循环里"""
        router = self._maim_router
        loop = self._maim_loop
        thread = self._maim_thread

        self._maim_router = None
        self._maim_platform = None
        self._maim_thread = None
        self._maim_loop_ready = None
        self._maim_startup_error = None
        if self._current_connection_key and self._current_connection_key[0] == 'maim':
            self._current_connection_key = None

        if router and loop and loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(router.stop(), loop)
                await asyncio.wait_for(asyncio.wrap_future(future), timeout=5)
                logger.info("Maim WebSocket 连接已关闭")
            except (asyncio.CancelledError, concurrent.futures.CancelledError):
                logger.info("Maim WebSocket 清理任务已取消")
            except asyncio.TimeoutError:
                logger.warning("停止 Maim Router 超时，将继续退出流程")
            except Exception as e:
                logger.warning(f"停止 Maim Router 时出现异常: {e}")

        if thread and thread.is_alive():
            try:
                running_loop = asyncio.get_running_loop()
                await running_loop.run_in_executor(None, thread.join, 2)
            except Exception as e:
                logger.debug(f"等待 Maim Router 线程结束失败: {e}", exc_info=True)
    
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
        async with self._switch_lock:
            if not self._initialized:
                logger.warning("聊天管理器未初始化，尝试自动初始化")
                if not await self.initialize(self._current_task):
                    return False

            try:
                candidates = self._ordered_candidates(self._current_task)
                if not candidates:
                    logger.warning("无法获取连接候选")
                    return False

                for connection_info in candidates:
                    protocol_type = connection_info.get('protocol_type')
                    model_index = connection_info.get('model_index', 0)

                    if not await self._prepare_connection(connection_info):
                        logger.warning(f"连接准备失败，尝试下一个模型: {connection_info.get('model_name')}")
                        continue

                    self._protocol_manager.set_active_task_model(self._current_task, model_index)
                    self._current_connection_key = self._connection_key(connection_info)

                    logger.info(f"[发送消息] {protocol_type} | {connection_info.get('model_name')} | {content[:50]}")

                    if protocol_type == 'maim':
                        success = await self._send_maim(content, connection_info, user_id, user_name)
                    elif protocol_type in ['openai', 'gemini']:
                        success = await self._send_http(content, connection_info, user_id, user_name)
                    else:
                        logger.error(f"不支持的协议类型: {protocol_type}")
                        success = False

                    if success:
                        logger.info(f"[发送成功] {connection_info.get('model_name')} | {content[:30]}...")
                        return True

                    logger.warning(f"[发送失败] {connection_info.get('model_name')}，准备切换候选")

                logger.error("所有聊天候选模型均发送失败")
                return False

            except Exception as e:
                logger.error(f"发送消息失败: {e}", exc_info=True)
                return False
    
    async def _load_prompt_context(self, limit: int) -> List[Dict[str, Any]]:
        """读取最近聊天记录，供 OpenAI 兼容请求拼接上下文。"""
        if limit <= 0:
            return []

        try:
            from src.database import db_manager

            if not db_manager.is_initialized():
                return []

            messages = await db_manager.get_messages(limit=limit, offset=0)
            return list(reversed(messages))
        except Exception as e:
            logger.warning(f"读取 prompt 上下文失败，继续无上下文请求: {e}")
            return []

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
            url = f"{connection_info.get('base_url', '')}/chat/completions"
            if not url or url == "/chat/completions":
                logger.error("HTTP 请求缺少 base_url")
                return False

            headers = {
                "Authorization": f"Bearer {connection_info.get('api_key', '')}",
                "Content-Type": "application/json"
            }

            context_limit = prompt_manager.get_context_limit()
            context_fetch_limit = context_limit + 2 if context_limit > 0 else 0
            context_messages = await self._load_prompt_context(context_fetch_limit)
            messages = prompt_manager.build_messages(
                content,
                user_id,
                user_name,
                context_messages=context_messages,
            )

            model_identifier = connection_info.get('model_identifier', '')
            if not model_identifier:
                logger.error("HTTP 请求缺少 model_identifier")
                return False

            # 构建请求数据
            data = {
                "model": model_identifier,
                "messages": messages,
                "stream": False
            }
            if connection_info.get('temperature') is not None:
                data['temperature'] = connection_info['temperature']
            if connection_info.get('max_tokens') is not None:
                data['max_tokens'] = connection_info['max_tokens']
            extra_params = connection_info.get('extra_params') or {}
            if isinstance(extra_params, dict):
                data.update(extra_params)

            # HTTP 发送日志
            logger.info(f"[HTTP发送] {connection_info.get('base_url', '')}")
            logger.info(f"  模型: {model_identifier}")
            logger.info(f"  消息: {content[:50]}")

            # 每次请求临时创建 session，请求完成后自动关闭
            timeout = aiohttp.ClientTimeout(total=connection_info.get('timeout', 30))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        try:
                            result = await response.json()
                            # 防御性检查 API 响应格式
                            choices = result.get('choices', [])
                            if not choices:
                                logger.error("HTTP 响应格式异常: choices 为空")
                                return False
                            first_choice = choices[0] if choices else {}
                            message = first_choice.get('message', {})
                            reply = message.get('content', '')
                            if not reply:
                                logger.warning("HTTP 响应中 content 为空")
                                reply = "[空响应]"
                        except Exception as parse_error:
                            logger.error(f"解析 HTTP 响应失败: {parse_error}")
                            return False

                        # HTTP 接收日志
                        logger.info(f"[HTTP接收] {reply[:50]}")

                        # 触发 UI 信号（安全发送）
                        from src.frontend.signals import signals_bus
                        _safe_emit_signal(signals_bus, 'message_received', reply)

                        return True
                    else:
                        error = await response.text()
                        logger.error(f"HTTP 请求失败: {response.status} - {error}")
                        return False

        except Exception as e:
            logger.error(f"发送 HTTP 请求失败: {e}", exc_info=True)
            return False
    
    def _handle_maim_message(self, message):
        """
        处理从 Maim WebSocket 接收到的消息

        Args:
            message: MessageBase 对象
        """
        try:
            if isinstance(message, dict):
                message = MessageBase.from_dict(message)

            # 提取消息段
            message_segment = message.message_segment
            seg_type = message_segment.type
            seg_data = message_segment.data

            # 处理不同类型的消息
            if seg_type == 'text':
                # 文本消息
                reply_content = str(seg_data or '')
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

            logger.info(f"[接收消息] {seg_type} | {reply_content[:50]}")

            # 触发 UI 信号（安全发送）
            from src.frontend.signals import signals_bus
            _safe_emit_signal(signals_bus, 'message_received', reply_content)

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
        if not MAIM_MESSAGE_AVAILABLE:
            logger.error("maim_message 库未安装，无法发送 Maim 消息")
            return False

        seg = Seg(type='text', data=content)
        return await self._send_maim_segment(
            seg=seg,
            raw_message=content,
            connection_info=connection_info,
            user_id=user_id,
            user_name=user_name,
            content_format=['text']
        )

    async def _send_maim_segment(
        self,
        seg,
        raw_message: str,
        connection_info: Dict[str, Any],
        user_id: str,
        user_name: str,
        content_format: Optional[List[str]] = None
    ) -> bool:
        """发送任意 Maim Seg，确保发送发生在 Router 所在线程"""
        if not self._maim_router or not self._maim_platform:
            logger.warning("Maim WebSocket 未初始化或已失效")
            return False

        if not self._is_maim_connected():
            logger.warning("Maim WebSocket 未连接")
            return False

        if not MAIM_MESSAGE_AVAILABLE:
            logger.error("maim_message 库未安装，无法发送 Maim 消息")
            return False

        try:
            platform, actual_user_name = self._resolve_maim_identity(connection_info, user_name)
            content_format = content_format or ['text']

            user_info = UserInfo(
                platform=platform,
                user_id=user_id,
                user_nickname=actual_user_name,
                user_cardname=''
            )

            format_info = FormatInfo(
                content_format=content_format,
                accept_format=['text', 'emoji', 'image']
            )

            additional_config = {
                "maimcore_reply_probability_gain": 1
            }
            extra_params = connection_info.get('extra_params') or {}
            if isinstance(extra_params, dict):
                additional_config.update(extra_params)

            message_info = BaseMessageInfo(
                platform=platform,
                message_id=str(uuid.uuid4()),
                time=time.time(),
                user_info=user_info,
                format_info=format_info,
                additional_config=additional_config
            )

            message = MessageBase(
                message_info=message_info,
                message_segment=seg,
                raw_message=raw_message
            )

            timeout = max(5, int(connection_info.get('timeout', 30)))
            result = await self._run_on_maim_loop(
                self._maim_router.send_message(message),
                timeout=timeout
            )

            if result is False:
                logger.warning("Maim Router 返回发送失败")
                return False

            logger.debug(f"Maim 消息已发送: {raw_message[:50]}...")
            return True

        except asyncio.TimeoutError:
            logger.error("发送 Maim 消息超时")
            return False
        except Exception as e:
            logger.error(f"发送 Maim 消息失败: {e}", exc_info=True)
            return False

    def _resolve_maim_identity(self, connection_info: Dict[str, Any], fallback_user_name: str) -> Tuple[str, str]:
        """解析 Maim 平台标识与用户昵称"""
        platform = connection_info.get('platform') or self._maim_platform or 'desktop-pet'
        actual_user_name = fallback_user_name

        try:
            from config import load_config
            main_config = load_config()
            if main_config:
                user_nickname = getattr(main_config, 'userNickname', None)
                nickname = getattr(main_config, 'Nickname', None)
                actual_user_name = user_nickname or nickname or fallback_user_name
        except Exception as e:
            logger.warning(f"读取 Maim 身份配置失败，使用默认值: {e}")

        return platform, actual_user_name
    
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized

    async def send_pixmap_with_text(self, pixmap, text: str = "", user_id: str = '0', user_name: str = '麦麦') -> bool:
        """
        发送截图消息。

        Maim 协议使用 maim_message 的 seglist(text + image)；HTTP 协议则走现有 Vision 任务。
        """
        try:
            from src.util.image_util import pixmap_to_base64

            image_base64 = pixmap_to_base64(pixmap)
            if not image_base64:
                logger.warning("截图转换 base64 失败")
                return False

            connection_info = self._protocol_manager.get_task_connection_info(self._current_task)
            if connection_info and connection_info.get('protocol_type') == 'maim':
                if not MAIM_MESSAGE_AVAILABLE:
                    logger.error("maim_message 库未安装，无法发送图片消息")
                    return False

                async with self._switch_lock:
                    if not await self._prepare_connection(connection_info):
                        return False

                    segs = []
                    if text:
                        segs.append(Seg(type='text', data=text))
                    segs.append(Seg(type='image', data=image_base64))

                    seg = Seg(type='seglist', data=segs)
                    raw_message = text or '[image]'
                    return await self._send_maim_segment(
                        seg=seg,
                        raw_message=raw_message,
                        connection_info=connection_info,
                        user_id=user_id,
                        user_name=user_name,
                        content_format=['text', 'image'] if text else ['image']
                    )

            prompt = text or "请识别图片中的内容，并详细描述你看到的内容。"
            return await self.recognize_image(image_base64=image_base64, prompt=prompt)

        except Exception as e:
            logger.error(f"发送截图消息失败: {e}", exc_info=True)
            return False

    def get_protocol_type(self) -> Optional[str]:
        """获取当前聊天任务激活协议类型"""
        connection_info = self._protocol_manager.get_task_connection_info(self._current_task)
        return connection_info.get('protocol_type') if connection_info else None

    def get_current_model_name(self) -> Optional[str]:
        """获取当前聊天任务激活模型名称"""
        connection_info = self._protocol_manager.get_task_connection_info(self._current_task)
        return connection_info.get('model_name') if connection_info else None

    def get_name(self) -> str:
        """兼容旧测试/调试脚本的名称接口"""
        protocol_type = self.get_protocol_type() or 'unknown'
        model_name = self.get_current_model_name() or 'unknown'
        return f"{protocol_type}:{model_name}"

    def get_supported_message_types(self) -> List[str]:
        """获取支持的消息类型"""
        protocol_type = self.get_protocol_type()
        if protocol_type == 'maim':
            return ['text', 'image', 'emoji', 'seglist']
        if protocol_type in ['openai', 'gemini']:
            return ['text', 'image']
        return ['text']

    async def switch_model(self, model_name_or_index, task_type: Optional[str] = None) -> bool:
        """手动切换当前任务模型，可传模型名或索引"""
        task_type = task_type or self._current_task
        if not self._protocol_manager.is_initialized():
            if not await self._protocol_manager.initialize():
                return False

        if isinstance(model_name_or_index, int):
            model_index = model_name_or_index
            if not self._protocol_manager.set_active_task_model(task_type, model_index):
                return False
        else:
            if not self._protocol_manager.set_active_task_model_by_name(task_type, str(model_name_or_index)):
                return False
            model_index = self._protocol_manager.get_active_model_index(task_type)

        async with self._switch_lock:
            connection_info = self._protocol_manager.get_task_connection_info(task_type, model_index)
            if not connection_info:
                return False
            if not await self._prepare_connection(connection_info):
                return False

            self._current_task = task_type
            self._current_connection_key = self._connection_key(connection_info)
            self._initialized = True
            logger.info(f"聊天模型已切换: {connection_info.get('model_name')} ({connection_info.get('protocol_type')})")
            return True

    async def switch_to_next_model(self, task_type: Optional[str] = None) -> bool:
        """手动切换到下一个候选模型"""
        task_type = task_type or self._current_task
        connection_info = self._protocol_manager.switch_task_to_next_model(task_type)
        if not connection_info:
            return False
        return await self.switch_model(connection_info.get('model_index', 0), task_type)
    
    async def recognize_image(self, image_base64: str, prompt: str = None, callback=None) -> bool:
        """
        识图接口（独立于聊天消息）
        
        Args:
            image_base64: 图片的 base64 编码
            prompt: 自定义 prompt（可选）
            callback: 回调函数 callback(success, task_type, response)
        
        Returns:
            是否发送成功
        """
        try:
            # 获取 image_recognition 任务的连接信息
            connection_info = self._protocol_manager.get_task_connection_info('image_recognition')
            
            if not connection_info:
                logger.warning("无法获取 image_recognition 任务连接信息")
                return False
            
            protocol_type = connection_info['protocol_type']
            
            logger.info(f"[识图请求] {protocol_type}")
            
            # 默认识图 prompt
            if not prompt:
                prompt = "请识别图片中的内容，并详细描述你看到的内容。"
            
            # 根据协议类型发送
            if protocol_type in ['openai', 'gemini']:
                success = await self._send_vision_request(
                    prompt=prompt,
                    image_base64=image_base64,
                    connection_info=connection_info,
                    task_type='image_recognition',
                    callback=callback
                )
            else:
                logger.error(f"识图不支持协议类型: {protocol_type}")
                return False
            
            return success
            
        except Exception as e:
            logger.error(f"识图请求失败: {e}", exc_info=True)
            return False
    
    async def translate_image(self, image_base64: str, callback=None) -> bool:
        """
        翻译接口（独立于聊天消息）
        
        Args:
            image_base64: 图片的 base64 编码
            callback: 回调函数 callback(success, task_type, response)
        
        Returns:
            是否发送成功
        """
        try:
            # 获取 image_recognition 任务的连接信息
            connection_info = self._protocol_manager.get_task_connection_info('image_recognition')
            
            if not connection_info:
                logger.warning("无法获取 image_recognition 任务连接信息")
                return False
            
            protocol_type = connection_info['protocol_type']
            
            logger.info(f"[翻译请求] {protocol_type}")
            
            # 翻译专用 prompt
            translate_prompt = """请识别图片中的文字内容，并将其翻译成中文。
如果图片中的文字已经是中文，则翻译成英文。
只输出翻译结果，不要添加任何解释或说明。"""
            
            # 根据协议类型发送
            if protocol_type in ['openai', 'gemini']:
                success = await self._send_vision_request(
                    prompt=translate_prompt,
                    image_base64=image_base64,
                    connection_info=connection_info,
                    task_type='translation',
                    callback=callback
                )
            else:
                logger.error(f"翻译不支持协议类型: {protocol_type}")
                return False
            
            return success
            
        except Exception as e:
            logger.error(f"翻译请求失败: {e}", exc_info=True)
            return False
    
    async def _send_vision_request(
        self,
        prompt: str,
        image_base64: str,
        connection_info: Dict[str, Any],
        task_type: str,
        callback=None
    ) -> bool:
        """
        发送视觉请求（Vision API）

        Args:
            prompt: 提示词
            image_base64: 图片 base64
            connection_info: 连接信息
            task_type: 任务类型
            callback: 回调函数

        Returns:
            是否发送成功
        """
        # Vision 请求需要更长的超时时间（处理图片耗时）
        vision_timeout = connection_info.get('timeout', 60)  # 默认 60 秒

        try:
            url = f"{connection_info.get('base_url', '')}/chat/completions"
            if not url:
                logger.error("Vision 请求缺少 base_url")
                if callback:
                    callback(False, task_type, None)
                return False

            api_key = connection_info.get('api_key', '')
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # 构建 Vision API 格式的消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            model_identifier = connection_info.get('model_identifier', '')
            if not model_identifier:
                logger.error("Vision 请求缺少 model_identifier")
                if callback:
                    callback(False, task_type, None)
                return False

            # 构建请求数据
            data = {
                "model": model_identifier,
                "messages": messages,
                "stream": False
            }
            if connection_info.get('max_tokens') is not None:
                data['max_tokens'] = connection_info['max_tokens']
            extra_params = connection_info.get('extra_params') or {}
            if isinstance(extra_params, dict):
                data.update(extra_params)

            # Vision 发送日志
            logger.info(f"[Vision发送] {connection_info.get('base_url', '')}")
            logger.info(f"  模型: {model_identifier}")
            logger.info(f"  任务: {task_type}")

            timeout = aiohttp.ClientTimeout(total=vision_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        try:
                            result = await response.json()
                            # 防御性检查 API 响应格式
                            choices = result.get('choices', [])
                            if not choices:
                                logger.error("Vision 响应格式异常: choices 为空")
                                if callback:
                                    callback(False, task_type, None)
                                return False
                            first_choice = choices[0] if choices else {}
                            message = first_choice.get('message', {})
                            reply = message.get('content', '')
                            if not reply:
                                logger.warning("Vision 响应中 content 为空")
                                reply = "[空响应]"
                        except Exception as parse_error:
                            logger.error(f"解析 Vision 响应失败: {parse_error}")
                            if callback:
                                callback(False, task_type, None)
                            return False

                        # Vision 接收日志
                        logger.info(f"[Vision接收] {reply[:50]}")

                        # 有回调的 Vision 任务（OCR/翻译）由调用方决定如何展示；
                        # 没有回调的图文聊天则走统一消息信号，显示到聊天 UI。
                        if callback:
                            callback(True, task_type, reply)
                        else:
                            from src.frontend.signals import signals_bus
                            _safe_emit_signal(signals_bus, 'message_received', reply)

                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Vision 请求失败: {response.status} - {error}")

                        if callback:
                            callback(False, task_type, None)

                        return False
        
        except asyncio.TimeoutError:
            logger.error(f"Vision 请求超时（超过 {vision_timeout} 秒）")
            if callback:
                callback(False, task_type, None)
            return False
        except Exception as e:
            logger.error(f"发送 Vision 请求失败: {e}", exc_info=True)
            
            if callback:
                callback(False, task_type, None)
            
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self._cleanup_maim()
            self._initialized = False
            self._current_connection_key = None
            logger.info("聊天管理器已清理")

        except Exception as e:
            logger.error(f"清理资源失败: {e}", exc_info=True)


# 全局单例
chat_manager = ChatManager()
