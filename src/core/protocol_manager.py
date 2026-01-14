"""
协议管理器
统一管理所有通信协议
"""

import asyncio
from typing import Dict, Any, Optional, List
from src.core.protocols.interfaces import IProtocol, ProtocolConfig
from src.core.protocols.protocol_factory import ProtocolFactory
from src.util.logger import logger


# 导入协议配置加载器（可选，用于从 model_config.toml 加载配置）
try:
    from config import (
        load_model_config,
        load_protocol_configs,
        validate_protocol_configs
    )
    _HAS_MODEL_CONFIG = True
except ImportError:
    _HAS_MODEL_CONFIG = False
    logger.warning("无法导入模型配置加载器，将使用旧的配置方式")


class ProtocolManager:
    """协议管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._protocols: Dict[str, IProtocol] = {}
        self._active_protocol: Optional[IProtocol] = None
        self._message_handler = None
        self._is_initialized = False
        
        logger.info("协议管理器初始化完成")
    
    async def initialize(self, protocol_configs: List[Dict[str, Any]]):
        """
        初始化协议管理器
        
        Args:
            protocol_configs: 协议配置列表，每个配置是一个字典
        """
        if self._is_initialized:
            logger.warning("协议管理器已经初始化，跳过")
            return
        
        logger.info(f"初始化协议管理器，配置了 {len(protocol_configs)} 个协议")
        
        for config_dict in protocol_configs:
            try:
                protocol_config = ProtocolConfig.from_dict(config_dict)
                protocol = ProtocolFactory.create_protocol(protocol_config)
                
                # 为每个协议配置生成唯一的名称
                # 对于 OpenAI 协议，使用提供商名称作为区分
                protocol_type = config_dict.get('type', '').lower()
                if protocol_type == 'openai':
                    # 使用 base_url 作为唯一标识
                    base_url = config_dict.get('base_url', 'default')
                    protocol_name = f"OpenAI-{base_url}"
                elif protocol_type == 'maim':
                    # 使用 platform 作为唯一标识
                    platform = config_dict.get('platform', 'default')
                    protocol_name = f"Maim-{platform}"
                else:
                    # 其他协议类型
                    protocol_name = protocol.get_name()
                
                self._protocols[protocol_name] = protocol
                
                # 初始化协议
                init_success = await protocol.initialize(config_dict)
                if not init_success:
                    logger.error(f"协议初始化失败: {protocol_name}")
                    continue
                
                # 注册消息处理器
                if self._message_handler:
                    protocol.register_message_handler(self._message_handler)
                
                logger.info(f"协议已添加: {protocol_name}")
                
            except Exception as e:
                logger.error(f"添加协议失败: {e}", exc_info=True)
        
        # 默认激活第一个协议
        if self._protocols:
            first_protocol_name = list(self._protocols.keys())[0]
            await self.set_active_protocol(first_protocol_name)
        
        self._is_initialized = True
        logger.info(f"协议管理器初始化完成，共 {len(self._protocols)} 个协议")
    
    async def initialize_from_model_config(self):
        """
        从 model_config.toml 初始化协议管理器（新方法）
        
        这个方法会自动加载 model_config.toml 文件，并从中提取协议配置
        
        注意：即使部分协议加载失败，也不会阻止初始化完成
        对于无状态协议（如 OpenAI），连接失败也不应该阻止初始化
        """
        if not _HAS_MODEL_CONFIG:
            raise ImportError(
                "无法从 model_config.toml 初始化：缺少配置加载器模块。"
                "请使用 initialize() 方法代替。"
            )
        
        if self._is_initialized:
            logger.warning("协议管理器已经初始化，跳过")
            return
        
        logger.info("从 model_config.toml 初始化协议管理器...")
        
        try:
            # 加载模型配置
            model_config = load_model_config()
            
            # 转换为协议配置
            protocol_configs = load_protocol_configs(model_config)
            
            # 检查协议配置列表
            if not protocol_configs:
                logger.error("协议配置列表为空，请检查 model_config.toml 配置")
                # 不抛出异常，允许系统继续运行（可能使用旧配置）
                return
            
            # 验证协议配置（但不强制要求验证通过）
            if not validate_protocol_configs(protocol_configs):
                logger.warning("协议配置验证未通过，部分协议可能无法正常工作")
            
            # 使用协议配置初始化
            await self.initialize(protocol_configs)
            
        except Exception as e:
            logger.error(f"从 model_config.toml 初始化失败: {e}", exc_info=True)
            # 不抛出异常，允许系统继续运行
    
    async def set_active_protocol(self, protocol_name: str) -> bool:
        """
        设置当前激活的协议
        
        Args:
            protocol_name: 协议名称
        
        Returns:
            是否设置成功
        """
        if protocol_name not in self._protocols:
            logger.error(f"协议不存在: {protocol_name}")
            return False
        
        # 断开当前激活的协议
        if self._active_protocol and self._active_protocol.is_connected():
            await self._active_protocol.disconnect()
            logger.info(f"已断开协议: {self._active_protocol.get_name()}")
        
        # 设置新的激活协议
        self._active_protocol = self._protocols[protocol_name]
        
        # 连接新协议
        connect_success = await self._active_protocol.connect()
        if connect_success:
            logger.info(f"当前激活协议: {protocol_name}")
        else:
            # 对于无状态协议（如 OpenAI），连接失败不应该阻止初始化
            # 只记录警告，不返回 False
            logger.warning(f"协议连接失败（但协议仍可用）: {protocol_name}")
            logger.warning(f"该协议将在首次发送消息时尝试重新连接")
        
        # 始终返回 True，因为协议已经设置为激活状态
        # 连接状态会在实际使用时检查
        return True
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        使用当前激活的协议发送消息
        
        Args:
            message: 消息字典
        
        Returns:
            是否发送成功
        """
        if not self._active_protocol:
            logger.error("没有激活的协议")
            return False
        logger.debug(f"通过协议 {self._active_protocol.get_name()} 发送消息: {message}")
        return await self._active_protocol.send_message(message)
    
    def register_message_handler(self, handler):
        """
        注册消息处理器（所有协议都会使用此处理器）
        
        Args:
            handler: 消息处理函数，签名: async handler(message: Dict[str, Any])
        """
        self._message_handler = handler
        
        # 为所有已添加的协议注册处理器
        for protocol in self._protocols.values():
            protocol.register_message_handler(handler)
        
        logger.info("协议管理器消息处理器已注册")
    
    def get_active_protocol(self) -> Optional[IProtocol]:
        """获取当前激活的协议"""
        return self._active_protocol
    
    def get_protocol(self, protocol_name: str) -> Optional[IProtocol]:
        """获取指定协议"""
        return self._protocols.get(protocol_name)
    
    def get_all_protocols(self) -> Dict[str, IProtocol]:
        """获取所有协议"""
        return self._protocols.copy()
    
    def get_protocol_names(self) -> List[str]:
        """获取所有协议名称"""
        return list(self._protocols.keys())
    
    def is_active_protocol_connected(self) -> bool:
        """当前激活的协议是否已连接"""
        return self._active_protocol and self._active_protocol.is_connected()
    
    async def switch_protocol(self, protocol_name: str) -> bool:
        """
        切换协议（别名，与 set_active_protocol 相同）
        
        Args:
            protocol_name: 协议名称
        
        Returns:
            是否切换成功
        """
        return await self.set_active_protocol(protocol_name)
    
    async def cleanup(self):
        """清理所有协议"""
        logger.info("清理协议管理器...")
        
        # 断开所有协议
        for protocol_name, protocol in self._protocols.items():
            try:
                await protocol.cleanup()
                logger.info(f"协议已清理: {protocol_name}")
            except Exception as e:
                logger.error(f"清理协议失败 {protocol_name}: {e}", exc_info=True)
        
        self._protocols.clear()
        self._active_protocol = None
        self._message_handler = None
        self._is_initialized = False
        
        logger.info("协议管理器清理完成")
    
    def print_status(self):
        """打印协议状态"""
        logger.info("=" * 50)
        logger.info("协议管理器状态")
        logger.info("=" * 50)
        logger.info(f"注册的协议数量: {len(self._protocols)}")
        logger.info(f"消息处理器: {'已注册' if self._message_handler else '未注册'}")
        logger.info("-" * 50)
        
        for i, (protocol_name, protocol) in enumerate(self._protocols.items()):
            is_active = "激活" if protocol == self._active_protocol else "未激活"
            is_connected = "已连接" if protocol.is_connected() else "未连接"
            logger.info(f"[{i}] {protocol_name}: {is_active}, {is_connected}")
        
        logger.info("=" * 50)


# 创建全局单例
protocol_manager = ProtocolManager()
