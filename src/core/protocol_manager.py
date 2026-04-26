"""
兼容旧版导入路径。

当前协议管理器实现位于 src.core.protocol 包内；保留这个模块可以让旧测试、
调试脚本和第三方扩展继续通过 src.core.protocol_manager 导入。
"""

from src.core.protocol import ProtocolManager, protocol_manager

__all__ = ["ProtocolManager", "protocol_manager"]
