"""
配置系统
提供配置文件的加载和管理功能
"""

from .loader import (
    load_config, 
    ensure_config_exists, 
    get_scale_factor,
    load_model_config,
    ensure_model_config_exists,
    save_model_config
)

from .schema import (
    Config,
    ModelConfigFile,
    APIProviderConfig,
    ModelConfig,
    TaskConfig,
    ModelTaskConfig
)

__all__ = [
    # 主配置
    'Config', 
    'load_config', 
    'ensure_config_exists', 
    'get_scale_factor',
    
    # 模型配置
    'ModelConfigFile',
    'load_model_config',
    'ensure_model_config_exists',
    'save_model_config',
    
    # 配置模式
    'APIProviderConfig',
    'ModelConfig',
    'TaskConfig',
    'ModelTaskConfig'
]