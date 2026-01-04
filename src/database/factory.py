"""
数据库工厂类
根据配置创建不同类型的数据库实例
"""

from typing import Dict, Any
from .base import BaseDatabase
from .sqlite import SQLiteDatabase
from src.util.logger import logger


class DatabaseFactory:
    """数据库工厂类"""
    
    # 支持的数据库类型映射
    _database_types: Dict[str, type] = {
        'sqlite': SQLiteDatabase,
        # 未来可以添加其他数据库类型
        # 'mysql': MySQLDatabase,
        # 'postgresql': PostgreSQLDatabase,
    }
    
    @classmethod
    def create_database(cls, db_type: str, **kwargs) -> BaseDatabase:
        """
        根据数据库类型创建数据库实例
        
        Args:
            db_type: 数据库类型（sqlite, mysql, postgresql）
            **kwargs: 数据库配置参数
            
        Returns:
            BaseDatabase: 数据库实例
            
        Raises:
            ValueError: 如果数据库类型不支持
        """
        db_type = db_type.lower()
        
        if db_type not in cls._database_types:
            supported_types = ', '.join(cls._database_types.keys())
            raise ValueError(
                f"不支持的数据库类型: {db_type}. "
                f"支持的类型: {supported_types}"
            )
        
        db_class = cls._database_types[db_type]
        logger.info(f"创建 {db_type} 数据库实例")
        
        return db_class(**kwargs)
    
    @classmethod
    def register_database_type(cls, db_type: str, db_class: type) -> None:
        """
        注册新的数据库类型
        
        Args:
            db_type: 数据库类型名称
            db_class: 数据库实现类
        """
        cls._database_types[db_type.lower()] = db_class
        logger.info(f"注册新的数据库类型: {db_type}")
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        获取所有支持的数据库类型
        
        Returns:
            list: 支持的数据库类型列表
        """
        return list(cls._database_types.keys())
