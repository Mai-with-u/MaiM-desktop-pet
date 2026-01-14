"""
协议配置加载器
从 model_config.toml 加载协议配置并转换为协议可以使用的格式
"""

from typing import List, Dict, Any, Optional
from src.util.logger import logger


def load_protocol_configs(model_config) -> List[Dict[str, Any]]:
    """
    从 ModelConfigFile 加载协议配置列表
    
    Args:
        model_config: ModelConfigFile 对象
    
    Returns:
        协议配置列表，每个配置是一个字典
    
    Raises:
        ValueError: 如果没有配置任何 API 提供商
    """
    if not model_config or not model_config.api_providers:
        logger.warning("没有配置任何 API 提供商")
        return []
    
    protocol_configs = []
    
    # 遍历所有 API 提供商，转换为协议配置格式
    for provider_config in model_config.api_providers:
        try:
            # 根据 client_type 创建不同的协议配置
            client_type = provider_config.client_type.lower()
            
            if client_type == 'maim':
                protocol_config = _convert_maim_provider_config(provider_config)
            elif client_type in ['openai', 'deepseek', 'gemini', 'bailian', 'siliconflow']:
                protocol_config = _convert_openai_provider_config(provider_config)
            else:
                logger.warning(f"不支持的客户端类型: {client_type}")
                continue
            
            if protocol_config:
                protocol_configs.append(protocol_config)
                logger.info(f"已加载协议配置: {protocol_config.get('type')} - {provider_config.name}")
                
        except Exception as e:
            logger.error(f"转换协议配置失败 {provider_config.name}: {e}", exc_info=True)
    
    logger.info(f"共加载 {len(protocol_configs)} 个协议配置")
    return protocol_configs


def _convert_maim_provider_config(provider_config) -> Optional[Dict[str, Any]]:
    """
    将 Maim 提供商配置转换为 Maim 协议配置格式
    
    Args:
        provider_config: APIProviderConfig 对象
    
    Returns:
        Maim 协议配置字典
    """
    config = {
        'type': 'maim',
        'url': provider_config.base_url,
        'platform': provider_config.name or 'default',
    }
    
    # 可选的 token
    if provider_config.api_key:
        config['token'] = provider_config.api_key
    
    # 额外参数
    if hasattr(provider_config, 'extra_params') and provider_config.extra_params:
        config.update(provider_config.extra_params)
    
    return config


def _convert_openai_provider_config(provider_config) -> Optional[Dict[str, Any]]:
    """
    将 OpenAI 兼容提供商配置转换为 OpenAI 协议配置格式
    
    Args:
        provider_config: APIProviderConfig 对象
    
    Returns:
        OpenAI 协议配置字典
    """
    config = {
        'type': 'openai',
        'api_key': provider_config.api_key,
        'base_url': provider_config.base_url,
    }
    
    # 额外参数
    if hasattr(provider_config, 'extra_params') and provider_config.extra_params:
        config.update(provider_config.extra_params)
    
    return config


def get_model_config_by_task(model_config, task_name: str) -> Optional[Dict[str, Any]]:
    """
    根据任务名称获取模型配置
    
    Args:
        model_config: ModelConfigFile 对象
        task_name: 任务名称（如 'chat', 'image_recognition' 等）
    
    Returns:
        模型任务配置字典，如果任务不存在则返回 None
    """
    if not model_config or not model_config.model_task_config:
        logger.warning(f"模型任务配置不存在")
        return None
    
    task_config = getattr(model_config.model_task_config, task_name, None)
    
    if not task_config:
        logger.warning(f"任务配置不存在: {task_name}")
        return None
    
    # 转换为字典格式
    config_dict = task_config.dict()
    config_dict['task_name'] = task_name
    
    return config_dict


def get_models_by_provider(model_config, provider_type: str) -> List[Dict[str, Any]]:
    """
    获取指定提供商的所有模型配置
    
    Args:
        model_config: ModelConfigFile 对象
        provider_type: 提供商类型（如 'maim', 'openai', 'deepseek'）
    
    Returns:
        模型配置列表
    """
    if not model_config or not model_config.models:
        logger.warning(f"模型配置不存在")
        return []
    
    provider_type = provider_type.lower()
    models = []
    
    for model_config_obj in model_config.models:
        if model_config_obj.provider and model_config_obj.provider.lower() == provider_type:
            model_dict = model_config_obj.dict()
            models.append(model_dict)
    
    logger.info(f"提供商 {provider_type} 共有 {len(models)} 个模型")
    return models


def get_model_config(model_config, model_id: str) -> Optional[Dict[str, Any]]:
    """
    根据模型 ID 获取模型配置
    
    Args:
        model_config: ModelConfigFile 对象
        model_id: 模型标识符
    
    Returns:
        模型配置字典，如果模型不存在则返回 None
    """
    if not model_config or not model_config.models:
        logger.warning(f"模型配置不存在")
        return None
    
    for model_config_obj in model_config.models:
        if model_config_obj.id == model_id:
            return model_config_obj.dict()
    
    logger.warning(f"模型不存在: {model_id}")
    return None


def validate_protocol_configs(protocol_configs: List[Dict[str, Any]]) -> bool:
    """
    验证协议配置列表
    
    Args:
        protocol_configs: 协议配置列表
    
    Returns:
        是否验证通过
    """
    if not protocol_configs:
        logger.error("协议配置列表为空")
        return False
    
    required_fields = ['type']
    
    for i, config in enumerate(protocol_configs):
        # 检查必需字段
        for field in required_fields:
            if field not in config:
                logger.error(f"协议配置 [{i}] 缺少必需字段: {field}")
                return False
        
        # 检查协议类型
        protocol_type = config.get('type', '').lower()
        if protocol_type == 'maim':
            if 'url' not in config:
                logger.error(f"Maim 协议配置 [{i}] 缺少 url 字段")
                return False
        elif protocol_type == 'openai':
            if 'api_key' not in config:
                logger.error(f"OpenAI 协议配置 [{i}] 缺少 api_key 字段")
                return False
        else:
            logger.warning(f"未知的协议类型: {protocol_type}")
    
    logger.info("协议配置验证通过")
    return True
