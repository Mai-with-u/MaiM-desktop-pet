"""
OpenAI 协议实现
基于 OpenAI API 的 HTTP 通信协议
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
        self._conversation_history: List[Dict[str, str]] = []
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化 OpenAI 协议
        
        Args:
            config: 协议配置，包含：
                - api_key: OpenAI API 密钥
                - base_url: API 基础 URL（可选，默认官方地址）
                - model: 模型名称（可选，默认 gpt-3.5-turbo）
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
            
            # 创建会话
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
            
            logger.info(f"OpenAI 协议初始化成功: {self._model}")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI 协议初始化失败: {e}", exc_info=True)
            return False
    
    async def connect(self) -> bool:
        """
        建立连接（HTTP 协议无需持久连接）
        
        Returns:
            是否连接成功
        """
        try:
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
        
        Args:
            message: 消息字典，格式：
                {
                    "message_segment": {
                        "type": "text",
                        "data": "用户消息内容"
                    }
                }
        
        Returns:
            是否发送成功
        """
        if not self._is_connected:
            logger.warning("OpenAI 协议未连接，无法发送消息")
            return False
        
        try:
            # 解析消息
            message_segment = message.get('message_segment', {})
            message_type = message_segment.get('type')
            
            if message_type == 'text':
                user_message = str(message_segment.get('data', ''))
                
                # 添加到对话历史
                self._conversation_history.append({
                    "role": "user",
                    "content": user_message
                })
                
                # 调用 OpenAI API
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
            
            elif message_type == 'seglist':
                # 处理多段消息
                seg_list = message_segment.get('data', [])
                for seg in seg_list:
                    if seg.get('type') == 'text':
                        user_message = str(seg.get('data'))
                        # 发送第一个文本消息
                        await self.send_message({
                            'message_segment': {
                                'type': 'text',
                                'data': user_message
                            }
                        })
                        break
            
            else:
                logger.warning(f"不支持的消息类型: {message_type}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
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
    
    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self._conversation_history.copy()
