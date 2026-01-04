# SpeechBubble 数据库集成使用指南

`SpeechBubbleList` 现已集成数据库功能，可以自动保存和加载消息历史记录。

## 主要功能

- ✅ 自动保存消息到数据库
- ✅ 从数据库加载历史消息
- ✅ 搜索历史消息
- ✅ 清空消息记录
- ✅ 可配置是否使用数据库

## 初始化配置

### 1. 在应用启动时初始化数据库

在 `main.py` 或应用的启动代码中：

```python
import asyncio
from src.database import db_manager
from config import config

async def initialize_database():
    """初始化数据库"""
    await db_manager.initialize(
        db_type=config.database.type,
        db_path=config.database.path
    )

async def main():
    # 初始化数据库
    await initialize_database()
    
    # 启动应用
    # ...

if __name__ == '__main__':
    asyncio.run(main())
```

### 2. 创建 SpeechBubbleList 实例

```python
from src.frontend.bubble_speech import SpeechBubbleList

# 创建实例（默认启用数据库）
bubble_list = SpeechBubbleList(parent=pet_widget)

# 或者禁用数据库功能
# bubble_list = SpeechBubbleList(parent=pet_widget, use_database=False)
```

## 基本使用

### 添加消息（自动保存到数据库）

```python
# 添加接收的消息
bubble_list.add_message(
    message="你好，这是一条消息",
    msg_type="received"
)

# 添加发送的消息
bubble_list.add_message(
    message="这是我的回复",
    msg_type="sent"
)

# 添加带图片的消息
from PyQt5.QtGui import QPixmap
pixmap = QPixmap("path/to/image.png")
bubble_list.add_message(
    message="图片描述",
    msg_type="received",
    pixmap=pixmap
)

# 添加消息但不保存到数据库
bubble_list.add_message(
    message="临时消息",
    msg_type="sent",
    save_to_db=False
)
```

### 加载历史消息

```python
import asyncio

async def load_history():
    """加载最近20条历史消息"""
    await bubble_list.load_history(limit=20)

# 在异步上下文中调用
asyncio.run(load_history())
```

### 搜索消息

```python
import asyncio

async def search():
    """搜索包含关键词的消息"""
    results = await bubble_list.search_messages("你好", limit=10)
    print(f"找到 {len(results)} 条消息")
    for msg in results:
        print(f"- {msg['message_content']}")

asyncio.run(search())
```

### 清空消息

```python
# 清空当前显示的消息气泡（不影响数据库）
bubble_list.clear_all()

# 清空数据库中的所有消息
import asyncio

async def clear_db():
    await bubble_list.clear_database()

asyncio.run(clear_db())
```

## 完整示例

### 示例1：初始化并加载历史消息

```python
import asyncio
from src.frontend.bubble_speech import SpeechBubbleList
from src.database import db_manager
from config import config
from PyQt5.QtWidgets import QApplication, QWidget

class PetWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.bubble_list = None
    
    async def initialize(self):
        """初始化组件"""
        # 初始化数据库
        await db_manager.initialize(
            db_type=config.database.type,
            db_path=config.database.path
        )
        
        # 创建气泡列表
        self.bubble_list = SpeechBubbleList(parent=self, use_database=True)
        
        # 加载历史消息
        await self.bubble_list.load_history(limit=20)
    
    def add_new_message(self, text: str, msg_type: str = "received"):
        """添加新消息"""
        self.bubble_list.add_message(
            message=text,
            msg_type=msg_type
        )

# 使用示例
import sys

async def main():
    app = QApplication(sys.argv)
    
    pet = PetWidget()
    await pet.initialize()
    
    pet.show()
    
    # 添加新消息
    pet.add_new_message("欢迎使用桌面宠物！")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    asyncio.run(main())
```

### 示例2：聊天界面集成

```python
import asyncio
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit
from src.frontend.bubble_speech import SpeechBubbleList
from src.database import db_manager

class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.bubble_list = None
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        
        # 消息显示区域（气泡列表）
        self.message_area = QWidget()
        self.message_layout = QVBoxLayout(self.message_area)
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.returnPressed.connect(self.send_message)
        
        # 按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        
        self.load_history_button = QPushButton("加载历史")
        self.load_history_button.clicked.connect(self.load_history)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_messages)
        
        layout.addWidget(self.message_area)
        layout.addWidget(self.input_field)
        layout.addWidget(self.send_button)
        layout.addWidget(self.load_history_button)
        layout.addWidget(self.clear_button)
        
        self.setLayout(layout)
    
    async def initialize(self):
        """初始化"""
        # 初始化数据库
        await db_manager.initialize(
            db_type='sqlite',
            db_path='data/chat.db'
        )
        
        # 创建气泡列表
        self.bubble_list = SpeechBubbleList(parent=self, use_database=True)
        
        # 加载历史消息
        await self.bubble_list.load_history(limit=20)
    
    def send_message(self):
        """发送消息"""
        text = self.input_field.text().strip()
        if text:
            self.bubble_list.add_message(
                message=text,
                msg_type="sent"
            )
            self.input_field.clear()
    
    def receive_message(self, text: str):
        """接收消息"""
        self.bubble_list.add_message(
            message=text,
            msg_type="received"
        )
    
    def load_history(self):
        """加载历史消息"""
        asyncio.create_task(self.bubble_list.load_history(limit=20))
    
    def clear_messages(self):
        """清空消息"""
        self.bubble_list.clear_all()
        asyncio.create_task(self.bubble_list.clear_database())
```

## 注意事项

1. **异步操作**：所有数据库相关的方法都是异步的，需要在异步上下文中调用
2. **初始化顺序**：必须先初始化数据库 (`db_manager.initialize`)，然后才能使用数据库功能
3. **避免重复保存**：从数据库加载的消息会自动设置 `save_to_db=False`，避免重复保存
4. **UI线程安全**：使用 `asyncio.create_task()` 异步调用数据库方法，避免阻塞UI线程
5. **关闭连接**：应用退出时记得关闭数据库连接

```python
# 应用退出时关闭数据库连接
async def cleanup():
    await db_manager.close()

asyncio.run(cleanup())
```

## 配置选项

在 `SpeechBubbleList` 构造函数中可以配置：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `parent` | QWidget | None | 父窗口 |
| `use_database` | bool | True | 是否使用数据库存储 |

在 `add_message` 方法中可以配置：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `message` | str | "" | 消息文本 |
| `msg_type` | str | "received" | 消息类型：received/sent |
| `pixmap` | QPixmap | None | 图片对象 |
| `save_to_db` | bool | True | 是否保存到数据库 |

## 数据库表结构

消息存储在 `messages` 表中，包含以下字段：

- `id`: 消息唯一ID
- `platform`: 平台类型（固定为 'desktop-pet'）
- `user_id`: 用户ID
- `user_nickname`: 用户昵称
- `user_cardname`: 用户群名片
- `message_type`: 消息类型
- `message_content`: 消息内容（JSON格式）
- `raw_message`: 原始消息文本
- `timestamp`: 时间戳
- `created_at`: 创建时间

详细说明请参考 `src/database/README.md`
