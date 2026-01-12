"""
通信协议包
提供多种通信协议的统一抽象层
"""

from .interfaces import IProtocol, ProtocolConfig
from .maim_protocol import MaimProtocol
from .openai_protocol import OpenAIProtocol
from .protocol_factory import ProtocolFactory

__all__ = [
    'IProtocol',
    'ProtocolConfig',
    'MaimProtocol',
    'OpenAIProtocol',
    'ProtocolFactory'
]
