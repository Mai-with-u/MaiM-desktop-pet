"""
数据库基类接口
定义所有数据库实现必须遵循的接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseDatabase(ABC):
    """数据库基类，定义所有数据库实现的通用接口"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据库"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开数据库连接"""
        pass
    
    @abstractmethod
    async def initialize_tables(self) -> bool:
        """初始化数据库表结构"""
        pass
    
    @abstractmethod
    async def save_message(self, message: Dict[str, Any]) -> bool:
        """保存消息到数据库"""
        pass
    
    @abstractmethod
    async def get_messages(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取消息历史记录"""
        pass
    
    @abstractmethod
    async def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取单条消息"""
        pass
    
    @abstractmethod
    async def delete_message(self, message_id: str) -> bool:
        """删除指定ID的消息"""
        pass
    
    @abstractmethod
    async def clear_all_messages(self) -> bool:
        """清空所有消息记录"""
        pass
    
    @abstractmethod
    async def get_message_count(self) -> int:
        """获取消息总数"""
        pass
    
    @abstractmethod
    async def search_messages(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """搜索包含关键词的消息"""
        pass
