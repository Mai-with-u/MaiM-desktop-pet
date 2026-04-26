"""
兼容旧版导入路径。

当前聊天管理器实现位于 src.core.chat 包内；保留这个模块可以让旧测试、
调试脚本和第三方扩展继续通过 src.core.chat_manager 导入。
"""

from src.core.chat import ChatManager, chat_manager

__all__ = ["ChatManager", "chat_manager"]
