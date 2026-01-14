"""
聊天层包
提供统一的聊天接口，支持多种协议的聊天功能
"""

from .interfaces import IChat
from .maim_chat import MaimChat, maim_chat_util
from .openai_chat import OpenAIChat, openai_chat_util

__all__ = [
    'IChat',
    'MaimChat',
    'maim_chat_util',
    'OpenAIChat',
    'openai_chat_util'
]
