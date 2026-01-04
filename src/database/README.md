# 数据库存储层

这是一个支持多种数据库类型的灵活存储层，默认使用 SQLite，支持通过配置文件切换数据库类型。

## 功能特性

- ✅ 支持多种数据库类型（SQLite、MySQL、PostgreSQL）
- ✅ 异步操作支持
- ✅ 统一的接口设计
- ✅ 自动初始化表结构
- ✅ 完整的 CRUD 操作
- ✅ 消息搜索功能
- ✅ 索引优化查询性能

## 配置

在 `config.toml` 文件中配置数据库：

```toml
[database]
type = "sqlite"                # 数据库类型: sqlite, mysql, postgresql
path = "data/chat.db"          # SQLite 数据库文件路径
```

## 使用方法

### 1. 初始化数据库

```python
from src.database import db_manager

# 根据配置文件初始化
from config import config
await db_manager.initialize(
    db_type=config.database.type,
    db_path=config.database.path
)
```

### 2. 保存消息

```python
message = {
    'message_info': {
        'message_id': str(uuid.uuid4()),
        'platform': 'desktop-pet',
        'time': time.time(),
    },
    'message_segment': {
        'type': 'text',
        'data': '这是一条消息',
    },
    'raw_message': '这是一条消息',
}

await db_manager.save_message(message)
```

### 3. 获取消息列表

```python
# 获取最近 100 条消息
messages = await db_manager.get_messages(limit=100)

# 分页获取消息
messages = await db_manager.get_messages(limit=50, offset=50)
```

### 4. 根据ID获取消息

```python
message = await db_manager.get_message_by_id(message_id)
```

### 5. 搜索消息

```python
# 搜索包含关键词的消息
messages = await db_manager.search_messages('关键词', limit=50)
```

### 6. 删除消息

```python
await db_manager.delete_message(message_id)
```

### 7. 获取消息总数

```python
count = await db_manager.get_message_count()
```

### 8. 清空所有消息

```python
await db_manager.clear_all_messages()
```

### 9. 关闭数据库连接

```python
await db_manager.close()
```

## 数据库表结构

### messages 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 消息唯一ID（主键） |
| platform | TEXT | 平台类型 |
| user_id | TEXT | 用户ID |
| user_nickname | TEXT | 用户昵称 |
| user_cardname | TEXT | 用户群名片 |
| message_type | TEXT | 消息类型（text/image/emoji） |
| message_content | TEXT | 消息内容（JSON格式） |
| raw_message | TEXT | 原始消息文本 |
| timestamp | REAL | 时间戳 |
| created_at | TEXT | 创建时间 |

## 索引

- `idx_timestamp`: 按时间戳降序索引，提高查询性能
- `idx_user_id`: 用户ID索引
- `idx_message_type`: 消息类型索引

## 扩展其他数据库类型

如需支持其他数据库类型（如 MySQL、PostgreSQL），可以：

1. 在 `src/database/` 目录下创建新的数据库实现文件（如 `mysql.py`）
2. 继承 `BaseDatabase` 类并实现所有抽象方法
3. 在 `DatabaseFactory` 中注册新的数据库类型

示例：

```python
# src/database/mysql.py
from .base import BaseDatabase

class MySQLDatabase(BaseDatabase):
    async def connect(self) -> bool:
        # 实现连接逻辑
        pass
    
    async def initialize_tables(self) -> bool:
        # 实现表初始化逻辑
        pass
    
    # 实现其他抽象方法...

# 在 factory.py 中注册
DatabaseFactory.register_database_type('mysql', MySQLDatabase)
```

## 测试

运行数据库功能测试：

```bash
python src/database/test_database.py
```

测试脚本会验证以下功能：
- 数据库连接和初始化
- 消息保存
- 消息查询
- 消息搜索
- 消息删除
- 数据库关闭

## 注意事项

1. 数据库文件默认存储在 `data/` 目录下
2. 使用异步操作，确保在异步上下文中调用
3. 数据库管理器是单例模式，全局共享
4. 应用关闭时应调用 `db_manager.close()` 关闭连接

## 依赖

- `aiosqlite==0.19.0` - SQLite 异步驱动

未来支持其他数据库时需要添加相应的驱动：
- MySQL: `aiomysql`
- PostgreSQL: `asyncpg`
