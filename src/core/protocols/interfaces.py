"""
通信协议接口定义
定义所有通信协议必须实现的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional


class IProtocol(ABC):
    """通信协议接口 - 定义所有协议的通用行为"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化协议
        
        Args:
            config: 协议配置字典
        
        Returns:
            是否初始化成功
        """
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        建立连接
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息
        
        Args:
            message: 消息字典
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    def register_message_handler(self, handler: Callable):
        """
        注册消息处理器
        
        Args:
            handler: 消息处理函数，签名: async handler(message: Dict[str, Any])
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """是否已连接"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取协议名称"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass


class ProtocolConfig:
    """协议配置基类"""
    
    def __init__(self, protocol_type: str, **kwargs):
        self.protocol_type = protocol_type
        self.config = kwargs
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ProtocolConfig':
        """从字典创建配置"""
        protocol_type = config_dict.get('type', 'maim')
        return cls(protocol_type=protocol_type, **config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'type': self.protocol_type,
            **self.config
        }
