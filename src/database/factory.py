"""
数据库工厂类
根据配置创建不同类型的数据库实例
"""

from typing import Dict, Any, Optional
from .base import BaseDatabase
from .sqlite import SQLiteDatabase
from src.util.logger import logger


class DatabaseFactory:
    """数据库工厂类"""

    # 支持的数据库类型映射（使用私有变量，外部不可直接修改）
    _database_types: Dict[str, type] = {
        'sqlite': SQLiteDatabase,
        # 未来可以添加其他数据库类型
        # 'mysql': MySQLDatabase,
        # 'postgresql': PostgreSQLDatabase,
    }

    @classmethod
    def create_database(cls, db_type: str, **kwargs) -> Optional[BaseDatabase]:
        """
        根据数据库类型创建数据库实例

        Args:
            db_type: 数据库类型（sqlite, mysql, postgresql）
            **kwargs: 数据库配置参数

        Returns:
            BaseDatabase: 数据库实例，创建失败返回 None

        Raises:
            ValueError: 如果数据库类型不支持
        """
        db_type = db_type.lower()

        if db_type not in cls._database_types:
            supported_types = ', '.join(cls._database_types.keys())
            logger.error(f"不支持的数据库类型: {db_type}. 支持的类型: {supported_types}")
            raise ValueError(
                f"不支持的数据库类型: {db_type}. "
                f"支持的类型: {supported_types}"
            )

        db_class = cls._database_types[db_type]
        logger.info(f"创建 {db_type} 数据库实例")

        try:
            return db_class(**kwargs)
        except Exception as e:
            logger.error(f"创建数据库实例失败: {e}", exc_info=True)
            return None

    @classmethod
    def register_database_type(cls, db_type: str, db_class: type) -> bool:
        """
        注册新的数据库类型

        Args:
            db_type: 数据库类型名称
            db_class: 数据库实现类

        Returns:
            bool: 是否注册成功
        """
        try:
            if not isinstance(db_class, type) or not issubclass(db_class, BaseDatabase):
                logger.error("注册的数据库类必须继承 BaseDatabase")
                return False
            cls._database_types[db_type.lower()] = db_class
            logger.info(f"注册新的数据库类型: {db_type}")
            return True
        except Exception as e:
            logger.error(f"注册数据库类型失败: {e}")
            return False

    @classmethod
    def get_supported_types(cls) -> list:
        """
        获取所有支持的数据库类型

        Returns:
            list: 支持的数据库类型列表
        """
        return list(cls._database_types.keys())
