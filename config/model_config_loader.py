"""
兼容旧版消息层配置加载入口。

新的加载实现集中在 config.loader 中；保留这些轻量 helper，方便旧测试和
调试脚本继续读取 model_config.toml。
"""

from typing import Optional

from .loader import ensure_model_config_exists, load_model_config, save_model_config
from .schema import APIProviderConfig, ModelConfig, TaskConfig


def get_chat_task_config() -> Optional[TaskConfig]:
    """获取聊天任务配置。"""
    config = load_model_config()
    return config.model_task_config.chat


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """按模型名称获取模型配置。"""
    config = load_model_config()
    for model in config.models:
        if model.name == model_name:
            return model
    return None


def get_provider_config(provider_name: str) -> Optional[APIProviderConfig]:
    """按供应商名称获取供应商配置。"""
    config = load_model_config()
    for provider in config.api_providers:
        if provider.name == provider_name:
            return provider
    return None


__all__ = [
    "ensure_model_config_exists",
    "load_model_config",
    "save_model_config",
    "get_chat_task_config",
    "get_model_config",
    "get_provider_config",
]
