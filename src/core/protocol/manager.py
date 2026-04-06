"""
协议管理器
负责协议识别、配置管理和连接信息提供

核心职责：
1. 确认聊天协议类型（openai 兼容 / maim）
2. 返回正确的 base_url 和 api_key
3. 如果是 maim (WebSocket)，初始化连接
"""

from typing import Optional, Dict, Any
from config import load_model_config
from config.schema import ModelConfigFile, APIProviderConfig, ModelConfig
from src.util.logger import logger


class ProtocolManager:
    """协议管理器"""
    
    def __init__(self):
        self._config: Optional[ModelConfigFile] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化协议管理器
        
        Returns:
            是否初始化成功
        """
        try:
            # 加载配置
            self._config = load_model_config()
            self._initialized = True
            
            logger.info("协议管理器初始化成功")
            logger.info(f"  - 供应商数量: {len(self._config.api_providers)}")
            logger.info(f"  - 模型数量: {len(self._config.models)}")
            
            return True
            
        except Exception as e:
            logger.error(f"协议管理器初始化失败: {e}", exc_info=True)
            return False
    
    # ===================================================================
    # 核心方法：获取连接信息
    # ===================================================================
    
    def get_protocol_type(self, model_name: str) -> Optional[str]:
        """
        根据 model_name 获取协议类型
        
        Args:
            model_name: 模型名称，如 'maim-local', 'deepseek-chat'
        
        Returns:
            协议类型: 'maim' / 'openai' / 'gemini'，如果未找到返回 None
        """
        if not self._initialized:
            logger.warning("协议管理器未初始化")
            return None
        
        # 1. 查找模型配置
        model_config = self._find_model(model_name)
        if not model_config:
            return None
        
        # 2. 查找供应商配置
        provider_config = self._find_provider(model_config.api_provider)
        if not provider_config:
            return None
        
        # 3. 返回协议类型
        return provider_config.client_type
    
    def get_connection_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        根据 model_name 获取连接信息
        
        这是协议管理器的核心方法，提供给聊天管理器使用
        
        Args:
            model_name: 模型名称
        
        Returns:
            连接信息字典，包含：
            - protocol_type: 协议类型 (maim/openai/gemini)
            - base_url: API 地址
            - api_key: API 密钥
            - model_identifier: 模型标识符
            - max_retry: 最大重试次数
            - timeout: 超时时间
            - retry_interval: 重试间隔
        """
        if not self._initialized:
            logger.warning("协议管理器未初始化")
            return None
        
        # 1. 查找模型配置
        model_config = self._find_model(model_name)
        if not model_config:
            logger.warning(f"未找到模型: {model_name}")
            return None
        
        # 2. 查找供应商配置
        provider_config = self._find_provider(model_config.api_provider)
        if not provider_config:
            logger.warning(f"未找到供应商: {model_config.api_provider}")
            return None
        
        # 3. 组合连接信息
        connection_info = {
            'protocol_type': provider_config.client_type,
            'base_url': provider_config.base_url,
            'api_key': provider_config.api_key,
            'model_identifier': model_config.model_identifier,
            'model_name': model_config.name,
            'provider_name': provider_config.name,
            'max_retry': provider_config.max_retry,
            'timeout': provider_config.timeout,
            'retry_interval': provider_config.retry_interval,
        }

        # 4. 如果是 maim 协议，添加 platform 信息
        if provider_config.client_type == 'maim':
            # 从主配置获取 platform
            from config import load_config
            main_config = load_config()
            connection_info['platform'] = main_config.platform
        
        logger.debug(f"获取连接信息: {model_name} -> {provider_config.client_type}")
        
        return connection_info
    
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
        
        # 1. 获取任务配置
        task_config = getattr(self._config.model_task_config, task_type, None)
        if not task_config:
            logger.warning(f"任务类型 '{task_type}' 未配置")
            return None
        
        # 2. 获取模型列表
        model_list = task_config.model_list
        if not model_list:
            logger.warning(f"任务 '{task_type}' 没有配置可用模型")
            return None
        
        # 3. 选择指定索引的模型
        if model_index >= len(model_list):
            logger.warning(f"任务 '{task_type}' 的模型索引 {model_index} 超出范围，使用第一个模型")
            model_index = 0
        
        model_name = model_list[model_index]
        
        # 4. 获取连接信息
        return self.get_connection_info(model_name)
    
    # ===================================================================
    # 内部方法：查找配置
    # ===================================================================
    
    def _find_model(self, model_name: str) -> Optional[ModelConfig]:
        """查找模型配置"""
        for model in self._config.models:
            if model.name == model_name:
                return model
        return None
    
    def _find_provider(self, provider_name: str) -> Optional[APIProviderConfig]:
        """查找供应商配置"""
        for provider in self._config.api_providers:
            if provider.name == provider_name:
                return provider
        return None
    
    # ===================================================================
    # 辅助方法
    # ===================================================================
    
    def is_maim_protocol(self, model_name: str) -> bool:
        """
        判断是否是 Maim 协议
        
        Args:
            model_name: 模型名称
        
        Returns:
            是否是 Maim 协议
        """
        protocol_type = self.get_protocol_type(model_name)
        return protocol_type == 'maim'
    
    def is_openai_compatible(self, model_name: str) -> bool:
        """
        判断是否是 OpenAI 兼容协议
        
        Args:
            model_name: 模型名称
        
        Returns:
            是否是 OpenAI 兼容协议
        """
        protocol_type = self.get_protocol_type(model_name)
        return protocol_type == 'openai'
    
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized
    
    def print_status(self):
        """打印状态"""
        if not self._initialized:
            logger.info("协议管理器未初始化")
            return
        
        logger.info("=" * 60)
        logger.info("协议管理器状态")
        logger.info("=" * 60)
        logger.info(f"供应商数量: {len(self._config.api_providers)}")
        logger.info(f"模型数量: {len(self._config.models)}")
        logger.info("-" * 60)
        
        for provider in self._config.api_providers:
            logger.info(f"  - {provider.name}: {provider.client_type} - {provider.base_url}")
        
        logger.info("=" * 60)


# 全局单例
protocol_manager = ProtocolManager()