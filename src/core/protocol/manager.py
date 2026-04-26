"""
协议管理器
负责协议识别、配置管理和连接信息提供

核心职责：
1. 确认聊天协议类型（openai 兼容 / maim）
2. 返回正确的 base_url 和 api_key
3. 如果是 maim (WebSocket)，初始化连接
"""

from typing import Optional, Dict, Any, List
from config import load_model_config
from config.schema import ModelConfigFile, APIProviderConfig, ModelConfig, TaskConfig
from src.util.logger import logger


class ProtocolManager:
    """协议管理器"""
    
    def __init__(self):
        self._config: Optional[ModelConfigFile] = None
        self._initialized = False
        self._active_model_indices: Dict[str, int] = {}
    
    async def initialize(self, force_reload: bool = False) -> bool:
        """
        初始化协议管理器
        
        Returns:
            是否初始化成功
        """
        try:
            if self._initialized and self._config is not None and not force_reload:
                return True

            # 加载配置
            self._config = load_model_config()
            self._initialized = True
            self._active_model_indices = {
                task_type: index
                for task_type, index in self._active_model_indices.items()
                if self._is_valid_task_model_index(task_type, index)
            }
            
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
        return provider_config.client_type.lower()
    
    def get_connection_info(self, model_name: str, task_config: Optional[TaskConfig] = None) -> Optional[Dict[str, Any]]:
        """
        根据 model_name 获取连接信息
        
        这是协议管理器的核心方法，提供给聊天管理器使用
        
        Args:
            model_name: 模型名称
            task_config: 任务配置（可选，用于任务级 timeout）
        
        Returns:
            连接信息字典，包含：
            - protocol_type: 协议类型 (maim/openai/gemini)
            - base_url: API 地址
            - api_key: API 密钥
            - model_identifier: 模型标识符
            - max_retry: 最大重试次数
            - timeout: 超时时间（任务级优先）
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
            'protocol_type': provider_config.client_type.lower(),
            'base_url': provider_config.base_url,
            'api_key': provider_config.api_key,
            'model_identifier': model_config.model_identifier,
            'model_name': model_config.name,
            'provider_name': provider_config.name,
            'max_retry': provider_config.max_retry,
            'timeout': provider_config.timeout,  # 默认使用供应商的 timeout
            'retry_interval': provider_config.retry_interval,
            'extra_params': model_config.extra_params or {},
        }
        
        # 如果有任务配置且设置了 timeout，则覆盖供应商的 timeout
        if task_config and hasattr(task_config, 'timeout') and task_config.timeout:
            connection_info['timeout'] = task_config.timeout
            logger.debug(f"使用任务级超时: {task_config.timeout}秒")
        if task_config:
            connection_info['temperature'] = task_config.temperature
            connection_info['max_tokens'] = task_config.max_tokens

        # 4. 如果是 maim 协议，添加 platform 信息
        if provider_config.client_type.lower() == 'maim':
            # 从主配置获取 platform
            from config import load_config
            main_config = load_config()
            connection_info['platform'] = main_config.platform
        
        logger.debug(f"获取连接信息: {model_name} -> {provider_config.client_type}")
        
        return connection_info
    
    def get_task_connection_info(self, task_type: str, model_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        根据任务类型获取连接信息
        
        Args:
            task_type: 任务类型，如 'chat', 'image_recognition'
            model_index: 使用模型列表中的第几个模型；None 表示使用当前激活模型
        
        Returns:
            连接信息字典
        """
        if not self._initialized:
            return None
        
        # 1. 获取任务配置
        task_config = self._get_task_config(task_type)
        if not task_config:
            logger.warning(f"任务类型 '{task_type}' 未配置")
            return None
        
        # 2. 获取模型列表
        model_list = task_config.model_list
        if not model_list:
            logger.warning(f"任务 '{task_type}' 没有配置可用模型")
            return None
        
        # 3. 选择指定索引的模型
        if model_index is None:
            model_index = self._active_model_indices.get(task_type, 0)

        if model_index >= len(model_list):
            logger.warning(f"任务 '{task_type}' 的模型索引 {model_index} 超出范围，使用第一个模型")
            model_index = 0
        if model_index < 0:
            logger.warning(f"任务 '{task_type}' 的模型索引 {model_index} 小于 0，使用第一个模型")
            model_index = 0
        
        model_name = model_list[model_index]
        
        # 4. 获取连接信息（传入 task_config 以支持任务级 timeout）
        connection_info = self.get_connection_info(model_name, task_config)
        if connection_info is not None:
            connection_info['task_type'] = task_type
            connection_info['model_index'] = model_index
            connection_info['candidate_count'] = len(model_list)
        return connection_info

    def get_task_model_names(self, task_type: str) -> List[str]:
        """获取任务配置中的模型名称列表"""
        if not self._initialized or not self._config:
            return []

        task_config = self._get_task_config(task_type)
        if not task_config or not task_config.model_list:
            return []
        return list(task_config.model_list)

    def get_task_connection_candidates(self, task_type: str) -> List[Dict[str, Any]]:
        """获取任务的所有可用连接候选，顺序与 model_list 一致"""
        candidates: List[Dict[str, Any]] = []
        for index, _ in enumerate(self.get_task_model_names(task_type)):
            connection_info = self.get_task_connection_info(task_type, index)
            if connection_info:
                candidates.append(connection_info)
        return candidates

    def get_active_model_index(self, task_type: str) -> int:
        """获取任务当前激活模型索引"""
        index = self._active_model_indices.get(task_type, 0)
        if not self._is_valid_task_model_index(task_type, index):
            return 0
        return index

    def set_active_task_model(self, task_type: str, model_index: int) -> bool:
        """设置任务当前激活模型索引"""
        if not self._is_valid_task_model_index(task_type, model_index):
            logger.warning(f"任务 '{task_type}' 的模型索引无效: {model_index}")
            return False

        self._active_model_indices[task_type] = model_index
        model_names = self.get_task_model_names(task_type)
        logger.info(f"任务 '{task_type}' 已切换到模型[{model_index}]: {model_names[model_index]}")
        return True

    def set_active_task_model_by_name(self, task_type: str, model_name: str) -> bool:
        """按模型名称设置任务当前激活模型"""
        model_names = self.get_task_model_names(task_type)
        if model_name not in model_names:
            logger.warning(f"任务 '{task_type}' 未配置模型: {model_name}")
            return False
        return self.set_active_task_model(task_type, model_names.index(model_name))

    def switch_task_to_next_model(self, task_type: str) -> Optional[Dict[str, Any]]:
        """切换到任务的下一个模型，并返回新的连接信息"""
        model_names = self.get_task_model_names(task_type)
        if not model_names:
            logger.warning(f"任务 '{task_type}' 没有可切换的模型")
            return None

        next_index = (self.get_active_model_index(task_type) + 1) % len(model_names)
        if not self.set_active_task_model(task_type, next_index):
            return None
        return self.get_task_connection_info(task_type, next_index)
    
    # ===================================================================
    # 内部方法：查找配置
    # ===================================================================
    
    def _find_model(self, model_name: str) -> Optional[ModelConfig]:
        """查找模型配置"""
        if not self._config:
            return None
        for model in self._config.models:
            if model.name == model_name:
                return model
        return None
    
    def _find_provider(self, provider_name: str) -> Optional[APIProviderConfig]:
        """查找供应商配置"""
        if not self._config:
            return None
        for provider in self._config.api_providers:
            if provider.name == provider_name:
                return provider
        return None

    def _get_task_config(self, task_type: str) -> Optional[TaskConfig]:
        """获取任务配置"""
        if not self._config or not self._config.model_task_config:
            return None
        return getattr(self._config.model_task_config, task_type, None)

    def _is_valid_task_model_index(self, task_type: str, model_index: int) -> bool:
        """检查任务模型索引是否有效"""
        model_names = self.get_task_model_names(task_type)
        return 0 <= model_index < len(model_names)
    
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
