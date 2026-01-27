"""
聊天管理器
根据 model_config.toml 中的配置，自动选择对应的聊天实现
"""

from typing import Optional, Dict, Any, List
import asyncio
from src.core.chats.interfaces import IChat
from src.core.chats.maim_chat import MaimChat
from src.core.chats.openai_chat import OpenAIChat
from src.core.protocol_manager import protocol_manager
from src.util.logger import logger
from config.model_config_loader import (
    load_model_config,
    get_chat_task_config,
    get_model_config,
    get_provider_config
)


class ChatManager:
    """聊天管理器 - 单例模式，根据协议类型管理聊天实例"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化聊天管理器"""
        if self._initialized:
            return
        
        self._chat: Optional[IChat] = None
        self._protocol_type: Optional[str] = None
        self._initialized = True
        
        logger.info("聊天管理器初始化")
    
    async def initialize(self, protocol_type: Optional[str] = None) -> bool:
        """
        初始化聊天管理器
        
        Args:
            protocol_type: 协议类型（'maim' 或 'openai'），如果为 None 则从配置文件读取
        
        Returns:
            是否初始化成功
        """
        try:
            # 如果没有指定协议类型，从 model_config.toml 读取
            if protocol_type is None:
                protocol_type = self._get_protocol_type_from_config()
                if protocol_type is None:
                    logger.error("无法从配置文件确定协议类型")
                    return False
            
            protocol_type_lower = protocol_type.lower()
            
            # 初始化协议管理器（从 model_config.toml）
            logger.info("初始化协议管理器...")
            await protocol_manager.initialize_from_model_config()
            
            # 获取模型配置（用于获取提供商信息）
            chat_task_config = get_chat_task_config()
            if not chat_task_config or not chat_task_config.model_list:
                logger.error("聊天任务配置未找到或模型列表为空")
                return False
            
            first_model_name = chat_task_config.model_list[0]
            model_config = get_model_config(first_model_name)
            if not model_config:
                logger.error(f"模型配置未找到: {first_model_name}")
                return False
            
            # 获取模型的 API 提供商配置，用于确定要激活的协议
            provider_config = get_provider_config(model_config.api_provider)
            if not provider_config:
                logger.error(f"无法找到提供商配置: {model_config.api_provider}")
                return False
            
            # 将模型名称添加到协议配置中（用于 OpenAI 协议）
            if protocol_type_lower == 'openai':
                protocol_name = f"OpenAI-{provider_config.base_url}"
                protocol = protocol_manager.get_protocol(protocol_name)
                if protocol:
                    # 更新协议配置中的模型名称
                    from src.core.protocols.openai_protocol import OpenAIProtocol
                    if isinstance(protocol, OpenAIProtocol):
                        # 使用模型配置中的 name 字段作为实际模型名称
                        model_name = model_config.name or model_config.id or 'gpt-3.5-turbo'
                        logger.info(f"设置 OpenAI 协议模型名称: {model_name}")
                        # 需要重新初始化协议以应用新的模型名称
                        await protocol.initialize({
                            'type': 'openai',
                            'api_key': provider_config.api_key,
                            'base_url': provider_config.base_url,
                            'model': model_name
                        })
            
            # 构建协议名称（与 protocol_manager.initialize 中的命名规则一致）
            if protocol_type_lower == 'maim':
                protocol_name = f"Maim-{provider_config.name}"
                success = await protocol_manager.set_active_protocol(protocol_name)
                # 对于 Maim 协议，连接失败应该阻止初始化（因为它是长连接）
                if not success:
                    logger.error(f"设置 Maim 协议为激活协议失败: {protocol_name}")
                    return False
                self._chat = MaimChat()
                logger.info(f"聊天管理器已初始化为 Maim 协议: {protocol_name}")
            elif protocol_type_lower == 'openai':
                # 对于 OpenAI 协议，使用 base_url 作为唯一标识
                protocol_name = f"OpenAI-{provider_config.base_url}"
                success = await protocol_manager.set_active_protocol(protocol_name)
                if success:
                    logger.info(f"聊天管理器已初始化为 OpenAI 协议: {protocol_name}")
                else:
                    # 协议不存在的情况才返回 False
                    logger.error(f"OpenAI 协议不存在: {protocol_name}，请检查 model_config.toml 配置")
                    return False
                self._chat = OpenAIChat()
            else:
                logger.error(f"不支持的协议类型: {protocol_type}")
                return False
            
            self._protocol_type = protocol_type_lower
            return True
            
        except Exception as e:
            logger.error(f"聊天管理器初始化失败: {e}", exc_info=True)
            return False
    
    def _get_protocol_type_from_config(self) -> Optional[str]:
        """
        从 model_config.toml 读取协议类型
        
        Returns:
            协议类型字符串（'maim' 或 'openai'），如果无法确定返回 None
        """
        try:
            # 获取对话任务配置
            chat_task_config = get_chat_task_config()
            if not chat_task_config or not chat_task_config.model_list:
                logger.warning("聊天任务配置未找到或模型列表为空")
                return None
            
            # 获取第一个模型（优先级最高）
            first_model_name = chat_task_config.model_list[0]
            logger.info(f"从配置读取到聊天模型: {first_model_name}")
            
            # 获取模型配置
            model_config = get_model_config(first_model_name)
            if not model_config:
                logger.warning(f"模型配置未找到: {first_model_name}")
                return None
            
            # 获取 API 提供商配置
            provider_config = get_provider_config(model_config.api_provider)
            if not provider_config:
                logger.warning(f"API 提供商配置未找到: {model_config.api_provider}")
                return None
            
            # 返回客户端类型（协议类型）
            protocol_type = provider_config.client_type.lower()
            logger.info(f"根据配置确定协议类型: {protocol_type}")
            
            return protocol_type
            
        except Exception as e:
            logger.error(f"从配置读取协议类型失败: {e}", exc_info=True)
            return None
    
    def get_protocol_type(self) -> Optional[str]:
        """
        获取当前协议类型
        
        Returns:
            当前协议类型
        """
        return self._protocol_type
    
    async def send(
        self,
        text: str,
        msg_type: str = "text",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """
        发送消息（统一接口）
        
        Args:
            text: 消息文本
            msg_type: 消息类型（'text', 'image', 'emoji' 等）
            user_id: 用户 ID（Maim 协议需要）
            user_nickname: 用户昵称（Maim 协议需要）
            user_cardname: 用户群名片（Maim 协议需要）
            additional_config: 额外配置
        
        Returns:
            是否发送成功
        """
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        
        return await self._chat.send(
            text=text,
            msg_type=msg_type,
            user_id=user_id,
            user_nickname=user_nickname,
            user_cardname=user_cardname,
            additional_config=additional_config
        )
    
    async def send_text(self, text: str, additional_config: Optional[dict] = None) -> bool:
        """
        发送文本消息
        
        Args:
            text: 消息文本
            additional_config: 额外配置（如 Maim 协议的回复概率增益等）
        
        Returns:
            是否发送成功
        """
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        return await self._chat.send_text(text, additional_config=additional_config)
    
    async def send_image(self, image_data: str) -> bool:
        """发送图片消息"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        return await self._chat.send_image(image_data)
    
    async def send_emoji(self, emoji: str) -> bool:
        """发送表情消息"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        return await self._chat.send_emoji(emoji)
    
    async def send_seglist(
        self,
        segments: List,
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """发送复合消息"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        return await self._chat.send_seglist(
            segments=segments,
            user_id=user_id,
            user_nickname=user_nickname,
            user_cardname=user_cardname,
            additional_config=additional_config
        )
    
    async def send_text_and_image(
        self,
        text: str,
        image_data: str,
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """发送文本+图片的复合消息"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        return await self._chat.send_text_and_image(
            text=text,
            image_data=image_data,
            user_id=user_id,
            user_nickname=user_nickname,
            user_cardname=user_cardname,
            additional_config=additional_config
        )
    
    async def send_pixmap_with_text(
        self,
        pixmap,
        text: str = "",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """发送 QPixmap 图片（带可选文本）"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        return await self._chat.send_pixmap_with_text(
            pixmap=pixmap,
            text=text,
            user_id=user_id,
            user_nickname=user_nickname,
            user_cardname=user_cardname,
            additional_config=additional_config
        )
    
    def get_name(self) -> str:
        """获取当前聊天实现名称"""
        if not self._chat:
            return "未初始化"
        return self._chat.get_name()
    
    def is_supported_message_type(self, msg_type: str) -> bool:
        """检查是否支持指定的消息类型"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return False
        return self._chat.is_supported_message_type(msg_type)
    
    def get_supported_message_types(self) -> List[str]:
        """获取支持的消息类型列表"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return []
        return self._chat.get_supported_message_types()
    
    def clear_history(self):
        """清除对话历史"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return
        self._chat.clear_history()
    
    def get_history(self) -> List:
        """获取对话历史"""
        if not self._chat:
            logger.error("聊天管理器未初始化")
            return []
        return self._chat.get_history()
    
    async def send_by_task(
        self,
        task_type: str,
        text: str = None,
        image_data: str = None,
        callback=None,
        **kwargs
    ) -> bool:
        """
        根据任务类型发送消息
        
        Args:
            task_type: 任务类型（'chat', 'image_recognition', 'expression' 等）
            text: 文本内容
            image_data: 图片数据（base64）
            callback: 回调函数，签名为：
                     - 同步回调: def callback(success: bool, task_type: str, response: str = None)
                     - 异步回调: async def callback(success: bool, task_type: str, response: str = None)
                     默认为 None（不调用回调）
            **kwargs: 其他参数（如 user_id, user_nickname 等）
        
        Returns:
            是否发送成功
        """
        try:
            # 1. 获取任务配置
            from config.model_config_loader import (
                get_task_config,
                get_model_config,
                get_provider_config
            )
            
            task_config = get_task_config(task_type)
            if not task_config or not task_config.model_list:
                logger.error(f"任务配置未找到或模型列表为空: {task_type}")
                return False
            
            # 2. 获取第一个可用模型
            model_name = task_config.model_list[0]  # 这是 name 字段
            model_config = get_model_config(model_name)
            if not model_config:
                logger.error(f"模型配置未找到: {model_name}")
                return False
            
            # 使用 model_identifier 作为 API 调用的模型名称
            api_model_name = model_config.model_identifier
            logger.info(f"任务 {task_type} 使用模型: name={model_name}, model_identifier={api_model_name}")
            
            # 3. 获取提供商配置
            provider_config = get_provider_config(model_config.api_provider)
            if not provider_config:
                logger.error(f"提供商配置未找到: {model_config.api_provider}")
                return False
            
            # 4. 确定协议类型
            protocol_type = provider_config.client_type.lower()
            
            # 5. 创建或获取协议实例
            if protocol_type == 'openai':
                protocol_name = f"OpenAI-{provider_config.base_url}"
                protocol = protocol_manager.get_protocol(protocol_name)
                
                if not protocol:
                    # 创建临时协议实例
                    from src.core.protocols.openai_protocol import OpenAIProtocol
                    protocol = OpenAIProtocol()
                    
                    # 构建初始化配置（使用 model_identifier）
                    init_config = {
                        'type': 'openai',
                        'api_key': provider_config.api_key,
                        'base_url': provider_config.base_url,
                        'model': api_model_name
                    }
                    
                    # 添加任务配置中的参数
                    if task_config.temperature is not None:
                        init_config['temperature'] = task_config.temperature
                    if task_config.max_tokens is not None:
                        init_config['max_tokens'] = task_config.max_tokens
                    
                    await protocol.initialize(init_config)
                else:
                    # 如果协议已存在，更新模型配置（使用 model_identifier）
                    from src.core.protocols.openai_protocol import OpenAIProtocol
                    if isinstance(protocol, OpenAIProtocol):
                        init_config = {
                            'type': 'openai',
                            'api_key': provider_config.api_key,
                            'base_url': provider_config.base_url,
                            'model': api_model_name
                        }
                        
                        if task_config.temperature is not None:
                            init_config['temperature'] = task_config.temperature
                        if task_config.max_tokens is not None:
                            init_config['max_tokens'] = task_config.max_tokens
                        
                        await protocol.initialize(init_config)
                
            elif protocol_type == 'maim':
                protocol_name = f"Maim-{provider_config.name}"
                protocol = protocol_manager.get_protocol(protocol_name)
            else:
                logger.error(f"不支持的协议类型: {protocol_type}")
                return False
            
            # 6. 发送消息
            if not protocol:
                logger.error("协议实例为空")
                return False
            
            # 构建消息
            if text and image_data:
                message = {
                    'message_segment': {
                        'type': 'seglist',
                        'data': [
                            {'type': 'text', 'data': text},
                            {'type': 'image', 'data': image_data}
                        ]
                    }
                }
            elif text:
                message = {
                    'message_segment': {
                        'type': 'text',
                        'data': text
                    }
                }
            elif image_data:
                message = {
                    'message_segment': {
                        'type': 'image',
                        'data': image_data
                    }
                }
            else:
                logger.error("text 和 image_data 至少需要提供一个")
                return False
            
            # 如果提供了自定义回调，临时禁用协议的 message_handler
            # 避免重复处理：既调用自定义回调，又触发 message_handler
            original_handler = None
            if callback and hasattr(protocol, '_message_handler'):
                original_handler = protocol._message_handler
                protocol._message_handler = None
                logger.debug(f"临时禁用 message_handler 以使用自定义回调: {callback.__name__}")
            
            try:
                # 发送消息
                success = await protocol.send_message(message)
                
                # 准备回调参数
                callback_args = {
                    'success': success,
                    'task_type': task_type,
                    'response': None
                }
                
                # 如果是 OpenAI 协议，尝试获取响应
                if success and protocol_type == 'openai':
                    # OpenAI 协议的 send_message 返回 LLM 响应文本
                    # 如果返回的是 str，说明是响应文本
                    if isinstance(success, str):
                        callback_args['response'] = success
                        callback_args['success'] = True  # 成功发送且收到响应
                    elif success:
                        # 如果返回的是 True，说明发送成功但可能响应是通过其他方式返回的
                        pass
                
                if success:
                    logger.info(f"任务 {task_type} 消息发送成功，使用模型: {model_name}")
                else:
                    logger.error(f"任务 {task_type} 消息发送失败")
                
                # 调用回调函数（如果提供）
                if callback:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            # 异步回调
                            await callback(**callback_args)
                        else:
                            # 同步回调
                            callback(**callback_args)
                    except Exception as e:
                        logger.error(f"回调函数执行失败: {e}", exc_info=True)
                
                return callback_args['success']
                
            finally:
                # 恢复原来的 message_handler
                if original_handler is not None and hasattr(protocol, '_message_handler'):
                    protocol._message_handler = original_handler
                    logger.debug("已恢复 message_handler")
            
        except Exception as e:
            logger.error(f"发送任务消息失败: {e}", exc_info=True)
            return False
    
    def print_status(self):
        """打印当前状态"""
        print("\n" + "=" * 60)
        print("聊天管理器状态")
        print("=" * 60)
        print(f"当前协议类型: {self._protocol_type or '未初始化'}")
        print(f"当前聊天实现: {self.get_name()}")
        print(f"支持的消息类型: {', '.join(self.get_supported_message_types())}")
        print("=" * 60 + "\n")


# 创建全局单例实例
chat_manager = ChatManager()
