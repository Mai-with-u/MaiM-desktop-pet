"""
配置系统
提供配置文件的加载、验证和管理功能
"""

from .loader import load_config, ensure_config_exists, get_scale_factor
from .schema import Config

__all__ = ['Config', 'load_config', 'ensure_config_exists', 'get_scale_factor']
