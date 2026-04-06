"""
模型管理器
负责查询可用模型、获取配置、选择模型

三层架构：
1. 供应商 (api_providers) - 提供服务的基础设施
2. 模型 (models) - 可用的 AI 模型
3. 任务配置 (model_task_config) - 不同任务使用的模型列表
"""

from typing import Optional, List, Dict, Any
from config import load_model_config
from config.schema import ModelConfigFile, APIProviderConfig, ModelConfig, TaskConfig
from src.util.logger import logger


class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self._config: Optional[ModelConfigFile] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化模型管理器
        
        Returns:
            是否初始化成功
        """
        try:
            # 加载配置
            self._config = load_model_config()
            self._initialized = True
            
            logger.info(f"模型管理器初始化成功")
            logger.info(f"  - 供应商数量: {len(self._config.api_providers)}")
            logger.info(f"  - 模型数量: {len(self._config.models)}")
            
            return True
            
        except Exception as e:
            logger.error(f"模型管理器初始化失败: {e}", exc_info=True)
            return False
    
    # ===================================================================
    # 查询可用模型类型
    # ===================================================================
    
    def get_available_task_types(self) -> List[str]:
        """
        获取所有可用的任务类型
        
        Returns:
            任务类型列表，如 ['chat', 'image_recognition', 'tool_use', ...]
        """
        if not self._initialized:
            logger.warning("模型管理器未初始化")
            return []
        
        task_types = []
        task_config = self._config.model_task_config
        
        # 检查每个任务类型是否配置
        for attr_name in dir(task_config):
            if not attr_name.startswith('_'):
                attr_value = getattr(task_config, attr_name, None)
                if isinstance(attr_value, TaskConfig):
                    task_types.append(attr_name)
        
        return task_types
    
    def get_available_models_for_task(self, task_type: str) -> List[str]:
        """
        获取指定任务类型可用的模型列表
        
        Args:
            task_type: 任务类型，如 'chat', 'image_recognition'
        
        Returns:
            模型名称列表（按优先级排序）
        """
        if not self._initialized:
            logger.warning("模型管理器未初始化")
            return []
        
        task_config = getattr(self._config.model_task_config, task_type, None)
        
        if not task_config or not isinstance(task_config, TaskConfig):
            logger.warning(f"任务类型 '{task_type}' 未配置")
            return []
        
        return task_config.model_list
    
    def get_all_models(self) -> List[ModelConfig]:
        """
        获取所有可用模型
        
        Returns:
            模型配置列表
        """
        if not self._initialized:
            return []
        
        return self._config.models
    
    # ===================================================================
    # 根据 类型/模型名 查询配置
    # ===================================================================
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """
        根据模型名称获取模型配置
        
        Args:
            model_name: 模型名称，如 'deepseek-chat', 'gpt-4o'
        
        Returns:
            模型配置，如果未找到返回 None
        """
        if not self._initialized:
            return None
        
        for model in self._config.models:
            if model.name == model_name:
                return model
        
        logger.warning(f"未找到模型: {model_name}")
        return None
    
    def get_provider_config(self, provider_name: str) -> Optional[APIProviderConfig]:
        """
        根据供应商名称获取供应商配置
        
        Args:
            provider_name: 供应商名称，如 'OpenAI', 'DeepSeek'
        
        Returns:
            供应商配置，如果未找到返回 None
        """
        if not self._initialized:
            return None
        
        for provider in self._config.api_providers:
            if provider.name == provider_name:
                return provider
        
        logger.warning(f"未找到供应商: {provider_name}")
        return None
    
    def get_model_connection_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        根据模型名称获取连接信息（base_url, api_key, client_type）
        
        这是协议管理器需要的关键方法
        
        Args:
            model_name: 模型名称
        
        Returns:
            连接信息字典，包含：
            - base_url: API 地址
            - api_key: API 密钥
            - client_type: 客户端类型 (maim/openai/gemini)
            - model_identifier: 模型标识符
            - max_retry: 最大重试次数
            - timeout: 超时时间
            - retry_interval: 重试间隔
        """
        if not self._initialized:
            return None
        
        # 1. 查找模型配置
        model_config = self.get_model_config(model_name)
        if not model_config:
            return None
        
        # 2. 查找供应商配置
        provider_config = self.get_provider_config(model_config.api_provider)
        if not provider_config:
            return None
        
        # 3. 组合返回信息
        return {
            'base_url': provider_config.base_url,
            'api_key': provider_config.api_key,
            'client_type': provider_config.client_type,
            'model_identifier': model_config.model_identifier,
            'model_name': model_config.name,
            'provider_name': provider_config.name,
            'max_retry': provider_config.max_retry,
            'timeout': provider_config.timeout,
            'retry_interval': provider_config.retry_interval,
        }
    
    def get_task_connection_info(self, task_type: str, model_index: int = 0) -> Optional[Dict[str, Any]]:
        """
        根据任务类型获取连接信息
        
        Args:
            task_type: 任务类型，如 'chat', 'image_recognition'
            model_index: 使用模型列表中的第几个模型（默认第一个）
        
        Returns:
            连接信息字典
        """
        if not self._initialized:
            return None
        
        # 1. 获取任务的模型列表
        model_list = self.get_available_models_for_task(task_type)
        
        if not model_list:
            logger.warning(f"任务 '{task_type}' 没有配置可用模型")
            return None
        
        # 2. 选择指定索引的模型
        if model_index >= len(model_list):
            logger.warning(f"任务 '{task_type}' 的模型索引 {model_index} 超出范围")
            model_index = 0
        
        model_name = model_list[model_index]
        
        # 3. 获取连接信息
        return self.get_model_connection_info(model_name)
    
    def get_task_config(self, task_type: str) -> Optional[TaskConfig]:
        """
        获取任务配置（包含 temperature, max_tokens 等）
        
        Args:
            task_type: 任务类型
        
        Returns:
            任务配置
        """
        if not self._initialized:
            return None
        
        return getattr(self._config.model_task_config, task_type, None)
    
    # ===================================================================
    # 工具方法
    # ===================================================================
    
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized
    
    def print_status(self):
        """打印状态信息"""
        if not self._initialized:
            logger.info("模型管理器未初始化")
            return
        
        logger.info("=" * 60)
        logger.info("模型管理器状态")
        logger.info("=" * 60)
        logger.info(f"供应商数量: {len(self._config.api_providers)}")
        logger.info(f"模型数量: {len(self._config.models)}")
        logger.info(f"可用任务类型: {', '.join(self.get_available_task_types())}")
        logger.info("=" * 60)


# 全局单例
model_manager = ModelManager()