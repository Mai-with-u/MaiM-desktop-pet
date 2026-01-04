"""
SQLite 数据库实现
提供 SQLite 数据库的具体实现
"""

import sqlite3
import json
import os
import aiosqlite
from typing import Optional, List, Dict, Any
from .base import BaseDatabase
from src.util.logger import logger


class SQLiteDatabase(BaseDatabase):
    """SQLite 数据库实现类"""
    
    def __init__(self, db_path: str):
        """
        初始化 SQLite 数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        
    async def connect(self) -> bool:
        """连接到 SQLite 数据库"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # 使用 aiosqlite 进行异步连接
            self.connection = await aiosqlite.connect(self.db_path)
            logger.info(f"成功连接到 SQLite 数据库: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"连接 SQLite 数据库失败: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """断开数据库连接"""
        try:
            if self.connection:
                await self.connection.close()
                logger.info("成功断开 SQLite 数据库连接")
            return True
        except Exception as e:
            logger.error(f"断开 SQLite 数据库连接失败: {e}")
            return False
    
    async def initialize_tables(self) -> bool:
        """初始化数据库表结构"""
        try:
            # 创建消息表
            await self.connection.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    user_id TEXT,
                    user_nickname TEXT,
                    user_cardname TEXT,
                    message_type TEXT,
                    message_content TEXT,
                    raw_message TEXT,
                    timestamp REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提高查询性能
            await self.connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON messages(timestamp DESC)
            ''')
            
            await self.connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON messages(user_id)
            ''')
            
            await self.connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_type 
                ON messages(message_type)
            ''')
            
            await self.connection.commit()
            logger.info("成功初始化 SQLite 数据库表结构")
            return True
        except Exception as e:
            logger.error(f"初始化 SQLite 数据库表失败: {e}")
            return False
    
    async def save_message(self, message: Dict[str, Any]) -> bool:
        """
        保存消息到数据库
        
        Args:
            message: 消息字典，包含消息信息
            
        Returns:
            bool: 是否保存成功
        """
        try:
            message_info = message.get('message_info', {})
            user_info = message_info.get('user_info', {})
            message_segment = message.get('message_segment', {})
            
            await self.connection.execute('''
                INSERT OR REPLACE INTO messages (
                    id, platform, user_id, user_nickname, user_cardname,
                    message_type, message_content, raw_message, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_info.get('message_id', ''),
                message_info.get('platform', ''),
                user_info.get('user_id', ''),
                user_info.get('user_nickname', ''),
                user_info.get('user_cardname', ''),
                message_segment.get('type', ''),
                json.dumps(message_segment.get('data', ''), ensure_ascii=False),
                message.get('raw_message', ''),
                message_info.get('time', 0)
            ))
            
            await self.connection.commit()
            logger.debug(f"成功保存消息: {message_info.get('message_id', '')}")
            return True
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            return False
    
    async def get_messages(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取消息历史记录
        
        Args:
            limit: 返回消息数量限制
            offset: 偏移量
            
        Returns:
            List[Dict]: 消息列表
        """
        try:
            cursor = await self.connection.execute('''
                SELECT * FROM messages 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            messages = []
            for row in rows:
                message = dict(zip(columns, row))
                # 解析 JSON 字段
                try:
                    message['message_content'] = json.loads(message['message_content'])
                except:
                    pass
                messages.append(message)
            
            return messages
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return []
    
    async def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单条消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            Optional[Dict]: 消息字典，如果不存在返回 None
        """
        try:
            cursor = await self.connection.execute('''
                SELECT * FROM messages WHERE id = ?
            ''', (message_id,))
            
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                message = dict(zip(columns, row))
                # 解析 JSON 字段
                try:
                    message['message_content'] = json.loads(message['message_content'])
                except:
                    pass
                return message
            return None
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return None
    
    async def delete_message(self, message_id: str) -> bool:
        """
        删除指定ID的消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            await self.connection.execute('''
                DELETE FROM messages WHERE id = ?
            ''', (message_id,))
            
            await self.connection.commit()
            logger.info(f"成功删除消息: {message_id}")
            return True
        except Exception as e:
            logger.error(f"删除消息失败: {e}")
            return False
    
    async def clear_all_messages(self) -> bool:
        """
        清空所有消息记录
        
        Returns:
            bool: 是否清空成功
        """
        try:
            await self.connection.execute('DELETE FROM messages')
            await self.connection.commit()
            logger.info("成功清空所有消息记录")
            return True
        except Exception as e:
            logger.error(f"清空消息记录失败: {e}")
            return False
    
    async def get_message_count(self) -> int:
        """
        获取消息总数
        
        Returns:
            int: 消息总数
        """
        try:
            cursor = await self.connection.execute('SELECT COUNT(*) FROM messages')
            result = await cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"获取消息总数失败: {e}")
            return 0
    
    async def search_messages(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜索包含关键词的消息
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Dict]: 匹配的消息列表
        """
        try:
            cursor = await self.connection.execute('''
                SELECT * FROM messages 
                WHERE message_content LIKE ? OR raw_message LIKE ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', limit))
            
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            messages = []
            for row in rows:
                message = dict(zip(columns, row))
                # 解析 JSON 字段
                try:
                    message['message_content'] = json.loads(message['message_content'])
                except:
                    pass
                messages.append(message)
            
            return messages
        except Exception as e:
            logger.error(f"搜索消息失败: {e}")
            return []
