"""
OpenAI 协议实现
基于 OpenAI API 的 HTTP 通信协议

支持功能：
- 文本对话（所有 OpenAI 模型）
- 视觉理解（GPT-4 Vision、GPT-4o 等支持视觉的模型）
"""

import asyncio
import aiohttp
from typing import Dict, Any, Callable, Optional, List
from src.core.protocols.interfaces import IProtocol
from src.util.logger import logger


class OpenAIProtocol(IProtocol):
    """OpenAI 协议实现"""
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._base_url: str = "https://api.openai.com/v1"
        self._model: str = "gpt-3.5-turbo"
        self._session: Optional[aiohttp.ClientSession] = None
        self._message_handler: Optional[Callable] = None
        self._is_connected = False
        self._conversation_history: List[Dict[str, Any]] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化 OpenAI 协议
        
        Args:
            config: 协议配置，包含：
                - api_key: OpenAI API 密钥
                - base_url: API 基础 URL（可选，默认官方地址）
                - model: 模型名称（可选，默认 gpt-3.5-turbo）
                  支持视觉模型：gpt-4-vision-preview, gpt-4o, gpt-4o-mini 等
                - system_prompt: 系统提示词（可选）
        
        Returns:
            是否初始化成功
        """
        try:
            self._api_key = config.get('api_key')
            self._base_url = config.get('base_url', 'https://api.openai.com/v1')
            self._model = config.get('model', 'gpt-3.5-turbo')
            
            # 初始化系统提示词
            system_prompt = config.get('system_prompt', 
                '你是一个友好的桌面宠物助手，名字叫 MaMai。请用活泼、可爱的语气回复。')
            
            if system_prompt:
                self._conversation_history = [{
                    "role": "system",
                    "content": system_prompt
                }]
            
            # 验证 API 密钥
            if not self._api_key:
                logger.error("OpenAI 协议初始化失败: 缺少 api_key")
                return False
            
            # 不在这里创建 session，延迟到第一次使用时创建
            # 这样可以确保 session 在正确的 event loop 中创建
            logger.info(f"OpenAI 协议初始化成功: {self._model}")
            logger.info("注意：视觉功能需要模型支持 OpenAI Vision API 格式")
            
            return True
            
        except Exception as e:
            logger.error(f"OpenAI 协议初始化失败: {e}", exc_info=True)
            return False
    
    async def _ensure_session(self):
        """确保 HTTP 会话已创建（在正确的 event loop 中）"""
        try:
            # 检查 session 是否可用
            if self._session is None:
                timeout = aiohttp.ClientTimeout(total=30)
                self._session = aiohttp.ClientSession(timeout=timeout)
                logger.debug("OpenAI HTTP 会话已创建")
            elif self._session.closed:
                timeout = aiohttp.ClientTimeout(total=30)
                self._session = aiohttp.ClientSession(timeout=timeout)
                logger.debug("OpenAI HTTP 会话已重新创建")
            else:
                # 检查 event loop 是否匹配
                current_loop = asyncio.get_running_loop()
                if hasattr(self._session, '_loop') and self._session._loop != current_loop:
                    # loop 不匹配，需要重新创建
                    try:
                        await self._session.close()
                    except:
                        pass
                    timeout = aiohttp.ClientTimeout(total=30)
                    self._session = aiohttp.ClientSession(timeout=timeout)
                    logger.debug("OpenAI HTTP 会话已重新创建（event loop 不匹配）")
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                # event loop 已关闭，无法创建新 session
                logger.warning("无法创建 HTTP 会话：event loop 已关闭")
                raise
            raise
    
    async def connect(self) -> bool:
        """
        建立连接（HTTP 协议无需持久连接）
        
        Returns:
            是否连接成功
        """
        try:
            # 确保 session 已创建
            await self._ensure_session()
            
            # 测试连接
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            
            async with self._session.get(
                f"{self._base_url}/models",
                headers=headers
            ) as response:
                if response.status == 200:
                    self._is_connected = True
                    logger.info("OpenAI 协议连接成功")
                    return True
                else:
                    logger.error(f"OpenAI API 认证失败: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"OpenAI 协议连接失败: {e}", exc_info=True)
            return False
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self._session:
                await self._session.close()
            
            self._is_connected = False
            logger.info("OpenAI 协议已断开连接")
            
        except Exception as e:
            logger.error(f"断开连接时出错: {e}", exc_info=True)
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息（发送给 OpenAI 并获取回复）
        
        注意：OpenAI 协议是无状态的 HTTP 请求，即使初始连接测试失败，
        也会尝试发送消息。只有在实际 API 调用失败时才返回 False。
        
        Args:
            message: 消息字典，格式：
                纯文本消息：
                {
                    "message_segment": {
                        "type": "text",
                        "data": "用户消息内容"
                    }
                }
                
                视觉消息（仅支持视觉模型）：
                {
                    "message_segment": {
                        "type": "seglist",
                        "data": [
                            {"type": "text", "data": "描述这张图片"},
                            {"type": "image", "data": "base64..."}
                        ]
                    }
                }
        
        Returns:
            是否发送成功
        """
        # 对于无状态的 HTTP 协议，不检查连接状态
        # 即使初始连接测试失败，也会尝试发送消息
        if not self._is_connected:
            logger.debug("OpenAI 协议未连接（将尝试发送消息）")
        
        try:
            # 解析消息
            message_segment = message.get('message_segment', {})
            message_type = message_segment.get('type')
            
            if message_type == 'text':
                # 处理纯文本消息
                user_message = str(message_segment.get('data', ''))
                
                # 添加到对话历史
                self._conversation_history.append({
                    "role": "user",
                    "content": user_message
                })
                
                return await self._call_openai_api()
            
            elif message_type == 'seglist':
                # 处理多段消息（支持文本+图片的视觉模型）
                seg_list = message_segment.get('data', [])
                
                # 构建 OpenAI Vision 格式的消息
                content = []
                has_image = False
                
                for seg in seg_list:
                    seg_type = seg.get('type')
                    seg_data = seg.get('data')
                    
                    if seg_type == 'text':
                        content.append({
                            "type": "text",
                            "text": str(seg_data)
                        })
                    elif seg_type == 'image':
                        has_image = True
                        # 将 base64 图片数据转换为 OpenAI Vision 格式
                        if seg_data:
                            image_url = f"data:image/jpeg;base64,{seg_data}" if not seg_data.startswith('data:') else seg_data
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            })
                
                if content:
                    # 添加到对话历史
                    self._conversation_history.append({
                        "role": "user",
                        "content": content
                    })
                    
                    if has_image:
                        logger.info(f"发送包含图片的消息（模型需要支持视觉 API），段数: {len(content)}")
                    else:
                        logger.info(f"发送多段文本消息，段数: {len(content)}")
                    
                    return await self._call_openai_api()
                else:
                    logger.warning("seglist 中没有有效的内容")
                    return False
            
            else:
                logger.warning(f"不支持的消息类型: {message_type}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            return False
    
    async def _call_openai_api(self) -> bool:
        """
        调用 OpenAI API（内部方法）
        
        Returns:
            是否调用成功
        """
        try:
            # 检查 event loop 是否已关闭
            try:
                current_loop = asyncio.get_running_loop()
                if current_loop.is_closed():
                    logger.warning("Event loop 已关闭，无法调用 OpenAI API")
                    return False
            except RuntimeError:
                logger.warning("无法获取 event loop，无法调用 OpenAI API")
                return False
            
            # 确保 session 已创建
            await self._ensure_session()
            
            # 调试日志：显示 API key（部分遮蔽）
            masked_key = self._api_key[:8] + "..." if self._api_key and len(self._api_key) > 8 else "***"
            logger.debug(f"调用 OpenAI API - API Key: {masked_key}, Base URL: {self._base_url}, Model: {self._model}")
            
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self._model,
                "messages": self._conversation_history
            }
            
            async with self._session.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    assistant_message = data['choices'][0]['message']['content']
                    
                    # 添加到对话历史
                    self._conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    # 触发消息处理器（模拟接收消息）
                    if self._message_handler:
                        simulated_message = {
                            'message_segment': {
                                'type': 'text',
                                'data': assistant_message
                            }
                        }
                        await self._message_handler(simulated_message)
                    
                    logger.debug(f"OpenAI 回复: {assistant_message}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API 请求失败: {response.status} - {error_text}")
                    return False
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.warning("Event loop 已关闭，无法调用 OpenAI API")
                return False
            logger.error(f"调用 OpenAI API 失败: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"调用 OpenAI API 失败: {e}", exc_info=True)
            return False
    
    def register_message_handler(self, handler: Callable):
        """
        注册消息处理器
        
        Args:
            handler: 消息处理函数，签名: async handler(message: Dict[str, Any])
        """
        self._message_handler = handler
        logger.info("OpenAI 协议消息处理器已注册")
    
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected
    
    def get_name(self) -> str:
        """获取协议名称"""
        return "OpenAI"
    
    async def cleanup(self):
        """清理资源"""
        await self.disconnect()
        self._session = None
        self._message_handler = None
        self._conversation_history = []
        logger.info("OpenAI 协议资源已清理")
    
    def clear_history(self):
        """清除对话历史（保留系统提示词）"""
        if self._conversation_history:
            system_prompt = self._conversation_history[0] if self._conversation_history[0]['role'] == 'system' else None
            self._conversation_history = [system_prompt] if system_prompt else []
            logger.info("对话历史已清除")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self._conversation_history.copy()
