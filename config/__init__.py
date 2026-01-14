"""
配置系统
提供配置文件的加载、验证和管理功能
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
    ModelTaskConfig,
    ModelTaskConfigGroup
)
from .protocol_config_loader import (
    load_protocol_configs,
    get_model_config_by_task,
    get_models_by_provider,
    get_model_config,
    validate_protocol_configs
)

__all__ = [
    # 主配置相关
    'Config', 
    'load_config', 
    'ensure_config_exists', 
    'get_scale_factor',
    # 消息层配置相关
    'ModelConfigFile',
    'load_model_config',
    'ensure_model_config_exists',
    'save_model_config',
    # 消息层配置模型
    'APIProviderConfig',
    'ModelConfig',
    'ModelTaskConfig',
    'ModelTaskConfigGroup',
    # 协议配置加载器
    'load_protocol_configs',
    'get_model_config_by_task',
    'get_models_by_provider',
    'get_model_config',
    'validate_protocol_configs'
]
