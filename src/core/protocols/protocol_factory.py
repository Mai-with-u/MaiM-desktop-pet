"""
协议工厂类
根据配置创建不同的协议实例
"""

from typing import Dict, Any
from src.core.protocols.interfaces import IProtocol, ProtocolConfig
from src.core.protocols.maim_protocol import MaimProtocol
from src.core.protocols.openai_protocol import OpenAIProtocol
from src.util.logger import logger


class ProtocolFactory:
    """协议工厂 - 根据配置创建协议实例"""
    
    # 注册的协议类型
    _protocol_registry = {
        'maim': MaimProtocol,
        'openai': OpenAIProtocol,
    }
    
    @classmethod
    def register_protocol(cls, protocol_type: str, protocol_class: type):
        """
        注册新的协议类型
        
        Args:
            protocol_type: 协议类型标识符（如 'maim', 'openai'）
            protocol_class: 协议类，必须实现 IProtocol 接口
        """
        if not issubclass(protocol_class, IProtocol):
            raise ValueError(f"{protocol_class} 必须实现 IProtocol 接口")
        
        cls._protocol_registry[protocol_type] = protocol_class
        logger.info(f"协议已注册: {protocol_type} -> {protocol_class.__name__}")
    
    @classmethod
    def create_protocol(cls, protocol_config: ProtocolConfig) -> IProtocol:
        """
        创建协议实例
        
        Args:
            protocol_config: 协议配置对象
        
        Returns:
            协议实例
        
        Raises:
            ValueError: 如果协议类型不支持
        """
        protocol_type = protocol_config.protocol_type
        
        if protocol_type not in cls._protocol_registry:
            supported = ', '.join(cls._protocol_registry.keys())
            raise ValueError(
                f"不支持的协议类型: {protocol_type}。"
                f"支持的类型: {supported}"
            )
        
        protocol_class = cls._protocol_registry[protocol_type]
        protocol = protocol_class()
        
        logger.info(f"创建协议实例: {protocol_type} ({protocol_class.__name__})")
        return protocol
    
    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> IProtocol:
        """
        从字典创建协议实例
        
        Args:
            config_dict: 配置字典，包含 'type' 字段和其他配置项
        
        Returns:
            协议实例
        """
        protocol_config = ProtocolConfig.from_dict(config_dict)
        return cls.create_protocol(protocol_config)
    
    @classmethod
    def get_supported_protocols(cls) -> list:
        """
        获取所有支持的协议类型
        
        Returns:
            协议类型列表
        """
        return list(cls._protocol_registry.keys())
    
    @classmethod
    def is_protocol_supported(cls, protocol_type: str) -> bool:
        """
        检查协议类型是否支持
        
        Args:
            protocol_type: 协议类型标识符
        
        Returns:
            是否支持
        """
        return protocol_type in cls._protocol_registry


# 使用示例：
"""
# 创建 Maim 协议
config = {
    'type': 'maim',
    'url': 'ws://127.0.0.1:19000/ws',
    'platform': 'default',
    'token': None
}
protocol = ProtocolFactory.create_from_dict(config)

# 创建 OpenAI 协议
config = {
    'type': 'openai',
    'api_key': 'sk-xxx',
    'model': 'gpt-3.5-turbo',
    'system_prompt': '你是一个友好的助手'
}
protocol = ProtocolFactory.create_from_dict(config)

# 注册自定义协议
from src.core.protocols.interfaces import IProtocol

class MyCustomProtocol(IProtocol):
    async def initialize(self, config: Dict[str, Any]) -> bool:
        pass
    async def connect(self) -> bool:
        pass
    async def disconnect(self):
        pass
    async def send_message(self, message: Dict[str, Any]) -> bool:
        pass
    def register_message_handler(self, handler: Callable):
        pass
    def is_connected(self) -> bool:
        pass
    def get_name(self) -> str:
        return "MyCustom"
    async def cleanup(self):
        pass

ProtocolFactory.register_protocol('custom', MyCustomProtocol)
"""
