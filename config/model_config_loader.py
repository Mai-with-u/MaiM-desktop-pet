"""
模型配置加载器
用于加载 model_config.toml 中的配置
"""

import os
import sys
import shutil
import tomli
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.util.logger import logger


# 配置文件路径
MODEL_CONFIG_FILE = "model_config.toml"
MODEL_CONFIG_TEMPLATE = "config/templates/model_config.toml.template"


class APIProviderConfig(BaseModel):
    """API 提供商配置"""
    name: str
    base_url: str
    client_type: str
    api_key: Optional[str] = ""
    max_retry: int = 2
    timeout: int = 30
    retry_interval: int = 5


class ModelConfig(BaseModel):
    """模型配置"""
    model_identifier: str
    name: str
    api_provider: str
    price_in: float = 0.0
    price_out: float = 0.0
    force_stream_mode: Optional[bool] = None
    extra_params: Optional[Dict[str, Any]] = None


class TaskConfig(BaseModel):
    """任务配置"""
    model_list: List[str]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 800


class ModelTaskConfig(BaseModel):
    """模型任务配置"""
    chat: Optional[TaskConfig] = None
    image_recognition: Optional[TaskConfig] = None
    tool_use: Optional[TaskConfig] = None
    voice: Optional[TaskConfig] = None
    embedding: Optional[TaskConfig] = None
    expression: Optional[TaskConfig] = None
    emotion: Optional[TaskConfig] = None
    naming: Optional[TaskConfig] = None
    relation: Optional[TaskConfig] = None
    planner: Optional[TaskConfig] = None


class InnerConfig(BaseModel):
    """内部配置"""
    version: str = "1.0.0"


class ModelConfig(BaseModel):
    """模型配置总览"""
    inner: Optional[InnerConfig] = None
    api_providers: Optional[List[APIProviderConfig]] = None
    models: Optional[List[ModelConfig]] = None
    model_task_config: Optional[ModelTaskConfig] = None


def ensure_model_config_exists() -> bool:
    """
    确保模型配置文件存在
    
    Returns:
        bool: 配置文件是否已经存在（无需修改）
    """
    if os.path.exists(MODEL_CONFIG_FILE):
        logger.info(f"模型配置文件已存在: {MODEL_CONFIG_FILE}")
        return True
    
    # 配置文件不存在，复制模板
    logger.warning(f"模型配置文件不存在: {MODEL_CONFIG_FILE}")
    logger.info("正在从模板创建模型配置文件...")
    
    try:
        # 检查模板文件是否存在
        if not os.path.exists(MODEL_CONFIG_TEMPLATE):
            logger.error(f"模型配置模板文件不存在: {MODEL_CONFIG_TEMPLATE}")
            logger.error("请确保程序文件完整，或从 GitHub 重新下载")
            sys.exit(1)
        
        # 复制模板文件
        shutil.copy(MODEL_CONFIG_TEMPLATE, MODEL_CONFIG_FILE)
        logger.info(f"✓ 已从模板创建模型配置文件: {MODEL_CONFIG_FILE}")
        
        # 显示提示信息
        print("\n" + "=" * 60)
        print("⚠️  模型配置文件已自动创建")
        print("=" * 60)
        print(f"\n模型配置文件位置: {os.path.abspath(MODEL_CONFIG_FILE)}")
        print("\n请根据你的需求修改配置文件，然后重新运行程序。\n")
        print("主要配置项说明：")
        print("  • api_providers: API 服务提供商配置")
        print("  • models: 模型定义")
        print("  • model_task_config.chat: 对话任务模型配置")
        print("\n如需了解更多配置选项，请查看配置文件中的详细注释。\n")
        print("=" * 60 + "\n")
        
        input("按回车键继续...")
        
        # 退出程序，等待用户修改配置
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"创建模型配置文件失败: {e}", exc_info=True)
        logger.error(f"请手动复制 {MODEL_CONFIG_TEMPLATE} 为 {MODEL_CONFIG_FILE} 并修改配置")
        sys.exit(1)


def load_model_config() -> ModelConfig:
    """
    加载模型配置文件
    
    Returns:
        ModelConfig: 模型配置对象
    """
    # 确保配置文件存在
    ensure_model_config_exists()
    
    try:
        # 加载 TOML 配置文件
        with open(MODEL_CONFIG_FILE, "rb") as f:
            config_data = tomli.load(f)
        
        # 验证并创建配置对象
        config = ModelConfig(**config_data)
        
        logger.info("模型配置文件加载成功")
        
        return config
        
    except Exception as e:
        logger.error(f"模型配置文件加载失败: {e}", exc_info=True)
        logger.error(f"请检查 {MODEL_CONFIG_FILE} 文件格式是否正确")
        sys.exit(1)


def get_chat_task_config() -> Optional[TaskConfig]:
    """
    获取对话任务配置
    
    Returns:
        TaskConfig: 对话任务配置，如果配置不存在返回 None
    """
    config = load_model_config()
    return config.model_task_config.chat if config.model_task_config else None


def get_task_config(task_name: str) -> Optional[TaskConfig]:
    """
    获取指定任务的配置
    
    Args:
        task_name: 任务名称（如 'chat', 'image_recognition' 等）
    
    Returns:
        TaskConfig: 任务配置，如果配置不存在返回 None
    """
    config = load_model_config()
    if not config.model_task_config:
        return None
    
    task_config_map = {
        'chat': config.model_task_config.chat,
        'image_recognition': config.model_task_config.image_recognition,
        'tool_use': config.model_task_config.tool_use,
        'voice': config.model_task_config.voice,
        'embedding': config.model_task_config.embedding,
        'expression': config.model_task_config.expression,
        'emotion': config.model_task_config.emotion,
        'naming': config.model_task_config.naming,
        'relation': config.model_task_config.relation,
        'planner': config.model_task_config.planner,
    }
    
    return task_config_map.get(task_name)


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """
    获取指定模型的配置
    
    Args:
        model_name: 模型名称（name 字段）
    
    Returns:
        ModelConfig: 模型配置，如果模型不存在返回 None
    """
    config = load_model_config()
    if not config.models:
        return None
    
    for model in config.models:
        if model.name == model_name:
            return model
    
    return None


def get_provider_config(provider_name: str) -> Optional[APIProviderConfig]:
    """
    获取指定 API 提供商的配置
    
    Args:
        provider_name: 提供商名称（name 字段）
    
    Returns:
        APIProviderConfig: 提供商配置，如果提供商不存在返回 None
    """
    config = load_model_config()
    if not config.api_providers:
        return None
    
    for provider in config.api_providers:
        if provider.name == provider_name:
            return provider
    
    return None
