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
            protocol_type = connection_info.get('protocol_type')
            if not protocol_type:
                logger.error("连接信息中缺少 protocol_type")
                return False

            # 协议选择日志
            logger.info("=" * 60)
            logger.info(f"协议选择: {protocol_type}")
            logger.info(f"  模型: {connection_info.get('model_name', '未知')}")
            logger.info(f"  供应商: {connection_info.get('provider_name', '未知')}")
            logger.info("=" * 60)
            
            if protocol_type == 'maim':
                success = await self._initialize_maim(connection_info)
            elif protocol_type in ['openai', 'gemini']:
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
            ws_url = connection_info.get('base_url')
            if not ws_url:
                logger.error("连接信息中缺少 base_url")
                return False

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

            # 线程启动状态跟踪
            self._maim_startup_error = None
            self._maim_startup_success = False

            # 在后台线程中启动 Router（run() 是阻塞方法）
            def run_router():
                """在后台线程中运行 Router"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._maim_router.run())
                    self._maim_startup_success = True
                except Exception as e:
                    self._maim_startup_error = str(e)
                    logger.error(f"Router 运行失败: {e}", exc_info=True)

            self._maim_thread = threading.Thread(target=run_router, daemon=True, name="MaimRouter")
            self._maim_thread.start()

            # 等待连接建立（使用 asyncio.sleep 保持异步特性）
            max_wait = 5  # 最多等待 5 秒
            for i in range(max_wait * 10):
                if self._maim_startup_error:
                    logger.error(f"Maim WebSocket 启动失败: {self._maim_startup_error}")
                    return False
                if self._maim_router.check_connection(platform):
                    logger.info("Maim WebSocket 连接已建立")
                    logger.info(f"  - 平台: {platform}")
                    logger.info(f"  - 地址: {ws_url}")
                    return True
                await asyncio.sleep(0.1)

            if self._maim_startup_error:
                logger.error(f"Maim WebSocket 启动失败: {self._maim_startup_error}")
                return False

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

            logger.info(f"[发送消息] {protocol_type} | {content[:50]}")

            # 根据协议类型发送
            if protocol_type == 'maim':
                success = await self._send_maim(content, connection_info, user_id, user_name)
            elif protocol_type in ['openai', 'gemini']:
                success = await self._send_http(content, connection_info, user_id, user_name)
            else:
                logger.error(f"不支持的协议类型: {protocol_type}")
                return False

            if success:
                logger.info(f"[发送成功] {content[:30]}...")
            else:
                logger.warning(f"[发送失败] {content[:30]}...")

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
            
            # 使用完整的 API key 进行认证（不要截断！）
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

            # HTTP 发送日志（只显示 API key 前10位用于安全）
            logger.info(f"[HTTP发送] {connection_info['base_url']}")
            logger.info(f"  模型: {connection_info['model_identifier']}")
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
        if not self._maim_router or not self._maim_platform:
            logger.warning("Maim WebSocket 未初始化或已失效")
            return False

        if not MAIM_MESSAGE_AVAILABLE:
            logger.error("maim_message 库未安装，无法发送 Maim 消息")
            return False

        try:
            # 从主配置读取平台标识和用户名
            from config import load_config
            main_config = load_config()
            if not main_config:
                logger.warning("主配置加载失败，使用默认值")
                platform = 'desktop-pet'
                actual_user_name = user_name
            else:
                platform = getattr(main_config, 'platform', 'desktop-pet')
                # 优先使用 userNickname，如果为空则使用 Nickname
                userNickname = getattr(main_config, 'userNickname', None)
                Nickname = getattr(main_config, 'Nickname', None)
                actual_user_name = userNickname if userNickname else (Nickname if Nickname else user_name)

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

                        # 调用回调函数
                        if callback:
                            callback(True, task_type, reply)

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