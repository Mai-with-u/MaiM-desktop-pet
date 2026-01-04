"""
数据库管理器
提供统一的数据库访问接口和管理功能
"""

from typing import Optional, List, Dict, Any
from .base import BaseDatabase
from .factory import DatabaseFactory
from src.util.logger import logger


class DatabaseManager:
    """数据库管理器单例类"""
    
    _instance = None
    _database: Optional[BaseDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self, db_type: str, **kwargs) -> bool:
        """
        初始化数据库连接
        
        Args:
            db_type: 数据库类型
            **kwargs: 数据库配置参数
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 创建数据库实例
            self._database = DatabaseFactory.create_database(db_type, **kwargs)
            
            # 连接数据库
            if not await self._database.connect():
                logger.error("数据库连接失败")
                return False
            
            # 初始化表结构
            if not await self._database.initialize_tables():
                logger.error("数据库表初始化失败")
                return False
            
            logger.info("数据库管理器初始化成功")
            return True
        except Exception as e:
            logger.error(f"数据库管理器初始化失败: {e}")
            self._database = None
            return False
    
    async def close(self) -> bool:
        """
        关闭数据库连接
        
        Returns:
            bool: 是否关闭成功
        """
        if self._database:
            result = await self._database.disconnect()
            self._database = None
            return result
        return True
    
    def is_initialized(self) -> bool:
        """
        检查数据库是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._database is not None
    
    async def save_message(self, message: Dict[str, Any]) -> bool:
        """
        保存消息到数据库
        
        Args:
            message: 消息字典
            
        Returns:
            bool: 是否保存成功
        """
        if not self._database:
            logger.error("数据库未初始化")
            return False
        
        return await self._database.save_message(message)
    
    async def get_messages(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取消息历史记录
        
        Args:
            limit: 返回消息数量限制
            offset: 偏移量
            
        Returns:
            List[Dict]: 消息列表
        """
        if not self._database:
            logger.error("数据库未初始化")
            return []
        
        return await self._database.get_messages(limit, offset)
    
    async def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单条消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            Optional[Dict]: 消息字典，如果不存在返回 None
        """
        if not self._database:
            logger.error("数据库未初始化")
            return None
        
        return await self._database.get_message_by_id(message_id)
    
    async def delete_message(self, message_id: str) -> bool:
        """
        删除指定ID的消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否删除成功
        """
        if not self._database:
            logger.error("数据库未初始化")
            return False
        
        return await self._database.delete_message(message_id)
    
    async def clear_all_messages(self) -> bool:
        """
        清空所有消息记录
        
        Returns:
            bool: 是否清空成功
        """
        if not self._database:
            logger.error("数据库未初始化")
            return False
        
        return await self._database.clear_all_messages()
    
    async def get_message_count(self) -> int:
        """
        获取消息总数
        
        Returns:
            int: 消息总数
        """
        if not self._database:
            logger.error("数据库未初始化")
            return 0
        
        return await self._database.get_message_count()
    
    async def search_messages(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜索包含关键词的消息
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Dict]: 匹配的消息列表
        """
        if not self._database:
            logger.error("数据库未初始化")
            return []
        
        return await self._database.search_messages(keyword, limit)


# 创建全局数据库管理器实例
db_manager = DatabaseManager()
