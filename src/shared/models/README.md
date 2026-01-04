# 标准消息类文档

本目录包含标准消息类的定义，完全兼容 `maim_message` 库 (v0.6.1+) 的消息结构。

## 概述

标准消息类提供了一个统一的消息格式，用于在整个应用中传递和处理消息数据。这些类与 `maim_message` 库保持兼容，确保与其他组件的无缝集成。

## 版本信息

- **maim_message 版本**: v0.6.1+
- **兼容性**: 完全兼容 maim_message v0.6.1 及以上版本
- **更新日期**: 2024-01-05

## 类结构

### 1. UserInfo - 用户信息

```python
@dataclass
class UserInfo:
    platform: str              # 平台类型
    user_id: str               # 用户ID
    user_nickname: str = ""    # 用户昵称
    user_cardname: str = ""    # 用户群名片
    
    def to_dict() -> Dict[str, Any]
```

### 2. GroupInfo - 群组信息

```python
@dataclass
class GroupInfo:
    group_id: str              # 群组ID
    group_name: str = ""       # 群组名称
    
    def to_dict() -> Dict[str, Any]
```

### 3. FormatInfo - 格式信息

```python
@dataclass
class FormatInfo:
    content_format: List[str]  # 支持的消息类型列表
    accept_format: List[str]   # 接受的消息类型列表
    
    def to_dict() -> Dict[str, Any]
```

### 4. TemplateInfo - 模板信息

```python
@dataclass
class TemplateInfo:
    template_id: str = ""           # 模板ID
    template_name: str = ""          # 模板名称
    template_data: Dict = {}        # 模板数据
    
    def to_dict() -> Dict[str, Any]
```

### 5. SenderInfo - 发送者信息

```python
@dataclass
class SenderInfo:
    platform: str = ""          # 平台类型
    user_id: str = ""           # 发送者ID
    user_nickname: str = ""     # 发送者昵称
    user_cardname: str = ""     # 发送者群名片
    
    def to_dict() -> Dict[str, Any]
```

### 6. ReceiverInfo - 接收者信息

```python
@dataclass
class ReceiverInfo:
    platform: str = ""          # 平台类型
    user_id: str = ""           # 接收者ID
    user_nickname: str = ""     # 接收者昵称
    user_cardname: str = ""     # 接收者群名片
    
    def to_dict() -> Dict[str, Any]
```

### 7. BaseMessageInfo - 基础消息信息

```python
@dataclass
class BaseMessageInfo:
    platform: str                 # 平台类型
    message_id: str               # 消息唯一ID
    time: float                   # 时间戳
    user_info: UserInfo           # 用户信息
    format_info: FormatInfo        # 格式信息
    group_info: Optional[GroupInfo] = None      # 群组信息（可选）
    template_info: Optional[TemplateInfo] = None # 模板信息（可选）
    sender_info: Optional[SenderInfo] = None     # 发送者信息（可选）
    receiver_info: Optional[ReceiverInfo] = None # 接收者信息（可选）
    additional_config: Dict       # 附加配置
    
    def to_dict() -> Dict[str, Any]
```

### 8. Seg - 消息段

```python
@dataclass
class Seg:
    type: str      # 消息类型（text/image/emoji等）
    data: Any      # 消息数据
    
    def to_dict() -> Dict[str, Any]
```

### 9. MessageBase - 消息基类

```python
@dataclass
class MessageBase:
    message_info: BaseMessageInfo  # 消息信息
    message_segment: Seg           # 消息段
    raw_message: str = ""          # 原始消息
    
    def to_dict() -> Dict[str, Any]
    @classmethod
    def from_dict(data: Dict[str, Any]) -> 'MessageBase'
    
    @classmethod
    def create_text_message(...) -> 'MessageBase'
    @classmethod
    def create_received_message(...) -> 'MessageBase'
    @classmethod
    def create_sent_message(...) -> 'MessageBase'
    
    # 便捷属性
    @property
    def message_type(self) -> str
    @property
    def message_content(self) -> Any
    @property
    def platform(self) -> str
    @property
    def message_id(self) -> str
    @property
    def timestamp(self) -> float
    @property
    def user_id(self) -> str
    @property
    def user_nickname(self) -> str
```

## 使用示例

### 基本用法

```python
from src.shared.models.message import MessageBase, UserInfo, Seg, FormatInfo, BaseMessageInfo

# 方式1: 使用便捷方法创建
message = MessageBase.create_text_message(
    text="你好，这是一条消息",
    platform="desktop-pet",
    user_id="0",
    user_nickname="桌面宠物",
    msg_type="text"
)

# 方式2: 创建接收消息
message = MessageBase.create_received_message(
    text="用户发送的消息",
    user_nickname="用户"
)

# 方式3: 创建发送消息
message = MessageBase.create_sent_message(
    text="这是我的回复",
    user_nickname="桌面宠物"
)

# 访问消息属性
print(f"消息ID: {message.message_id}")
print(f"消息内容: {message.message_content}")
print(f"用户: {message.user_nickname}")
print(f"时间戳: {message.timestamp}")
```

### 与数据库集成

```python
import asyncio
from src.shared.models.message import MessageBase
from src.database import db_manager

# 保存消息到数据库
async def save_message():
    # 创建消息
    message = MessageBase.create_sent_message("你好！")
    
    # 保存到数据库
    await db_manager.save_message(message)
    
    print(f"消息已保存: {message.message_id}")

# 从数据库加载消息
async def load_messages():
    # 获取消息列表
    messages = await db_manager.get_messages(limit=10)
    
    for msg_dict in messages:
        # 从字典创建 MessageBase 对象
        message = MessageBase.from_dict(msg_dict)
        print(f"{message.user_nickname}: {message.message_content}")

asyncio.run(save_message())
asyncio.run(load_messages())
```

### 与气泡显示集成

```python
from src.frontend.bubble_speech import SpeechBubbleList
from src.shared.models.message import MessageBase

# 创建气泡列表
bubble_list = SpeechBubbleList(parent=widget, use_database=True)

# 方式1: 添加文本消息（自动创建 MessageBase）
bubble_list.add_message(
    message="这是一条消息",
    msg_type="received"
)

# 方式2: 直接添加 MessageBase 对象
message_obj = MessageBase.create_received_message("这是从数据库加载的消息")
bubble_list.add_message(message=message_obj)

# 加载历史消息
await bubble_list.load_history(limit=20)
```

### 序列化和反序列化

```python
from src.shared.models.message import MessageBase

# 创建消息
message = MessageBase.create_text_message("测试消息")

# 转换为字典
message_dict = message.to_dict()
print(message_dict)

# 从字典创建消息
message2 = MessageBase.from_dict(message_dict)
print(message2.message_content)
```

### 与 maim_message 库兼容

```python
# 可以与 maim_message 库的类互换使用
from maim_message import MessageBase as MaimMessageBase
from src.shared.models.message import MessageBase as StdMessageBase

# 标准消息类与 maim_message 库的结构相同
# 可以轻松转换或兼容使用

# 例如，将标准消息传递给 maim_message 的路由
# from src.core.router import router
# await router.send_message(std_message)
```

## 最佳实践

### 1. 消息创建

```python
# ✅ 推荐：使用便捷方法
message = MessageBase.create_sent_message("消息内容")

# ✅ 推荐：指定详细信息
message = MessageBase.create_text_message(
    text="消息内容",
    platform="desktop-pet",
    user_id="user_123",
    user_nickname="用户昵称",
    msg_type="text"
)

# ❌ 不推荐：手动构建复杂结构（除非有特殊需求）
```

### 2. 数据持久化

```python
# ✅ 推荐：直接保存 MessageBase 对象
await db_manager.save_message(message_obj)

# ✅ 推荐：从字典恢复
message = MessageBase.from_dict(message_dict)
```

### 3. UI 集成

```python
# ✅ 推荐：使用 MessageBase 对象
bubble_list.add_message(message_obj)

# ✅ 推荐：简单文本消息
bubble_list.add_message("简单文本", msg_type="sent")
```

### 4. 消息传递

```python
# ✅ 推荐：传递完整的 MessageBase 对象
def process_message(message: MessageBase):
    print(f"处理消息: {message.message_content}")
    return message.to_dict()

# ✅ 推荐：使用属性访问
if message.user_id == "0":
    print("这是发送的消息")
```

## 注意事项

1. **类型安全**: 使用 `TYPE_CHECKING` 进行类型注解，避免循环导入
2. **异步操作**: 数据库操作都是异步的，需要使用 `await`
3. **消息ID**: 每条消息都有唯一的 `message_id`，用于标识和检索
4. **时间戳**: 使用 `time.time()` 生成浮点数时间戳
5. **JSON 序列化**: 消息数据可以轻松转换为 JSON 格式存储

## 与 maim_message 的兼容性

本标准消息类完全兼容 `maim_message` 库 (v0.6.1+) 的数据结构：

- ✅ `UserInfo` ↔ `maim_message.UserInfo`
- ✅ `GroupInfo` ↔ `maim_message.GroupInfo`
- ✅ `FormatInfo` ↔ `maim_message.FormatInfo`
- ✅ `TemplateInfo` ↔ `maim_message.TemplateInfo`
- ✅ `SenderInfo` ↔ `maim_message.SenderInfo`
- ✅ `ReceiverInfo` ↔ `maim_message.ReceiverInfo`
- ✅ `Seg` ↔ `maim_message.Seg`
- ✅ `MessageBase` ↔ `maim_message.MessageBase`
- ✅ `BaseMessageInfo` ↔ `maim_message.BaseMessageInfo`

## 新版本特性 (v0.6.1+)

### 新增类

1. **GroupInfo**: 支持群组信息
2. **TemplateInfo**: 支持消息模板
3. **SenderInfo**: 发送者信息类
4. **ReceiverInfo**: 接收者信息类

### BaseMessageInfo 新增字段

- `group_info`: 群组信息
- `template_info`: 模板信息
- `sender_info`: 发送者信息
- `receiver_info`: 接收者信息

### 向后兼容性

所有新增字段都是可选的（Optional），确保与旧版本的数据完全兼容。

## 相关文档

- [数据库集成](../../database/README.md)
- [气泡消息使用](../../frontend/bubble_speech_usage.md)
- [消息路由](../../core/router.py)

## 更新日志

### v2.0.0 (2024-01-05)
- 🚀 更新以兼容 maim_message v0.6.1+
- ✨ 新增 `GroupInfo` 群组信息类
- ✨ 新增 `TemplateInfo` 模板信息类
- ✨ 新增 `SenderInfo` 发送者信息类
- ✨ 新增 `ReceiverInfo` 接收者信息类
- ✨ 更新 `BaseMessageInfo` 支持新的可选字段
- ✨ 完全向后兼容 v1.0.0

### v1.0.0 (2024-01-05)
- ✨ 创建标准消息类
- ✨ 完全兼容 maim_message 库
- ✨ 支持序列化和反序列化
- ✨ 提供便捷的创建方法
- ✨ 集成到数据库和气泡显示系统
