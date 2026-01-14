# 聊天层

## 概述

聊天层提供了统一的聊天接口，支持多种协议的聊天功能。目前支持：

- **Maim 聊天**：基于 Maim 协议的聊天功能，支持文本、图片、表情等多种消息类型
- **OpenAI 聊天**：基于 OpenAI 协议的聊天功能，支持文本和图片（视觉模型）

## 架构设计

```
┌─────────────────────────────────────────────────┐
│           Application Layer                     │
│         (pet.py, main.py)                        │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────┐
│        ChatManager (聊天管理器)                  │
│  - 根据配置自动选择聊天实现                       │
│  - 统一的聊天接口                                │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼─────┐  ┌──────▼──────┐
│ MaimChat    │  │  OpenAIChat │
└─────────────┘  └─────────────┘
```

## 快速开始

### 1. 配置协议

在 `config.toml` 或 `model_config.toml` 中配置协议：

```toml
# 配置使用 Maim 协议
[[protocols]]
type = "maim"
url = "ws://127.0.0.1:8000/ws"
platform = "desktop-pet"

# 或者配置使用 OpenAI 协议
[[protocols]]
type = "openai"
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
model = "gpt-4o"  # 支持 Vision 的模型
system_prompt = "你是一个友好的桌面宠物助手"
```

### 2. 初始化聊天管理器

```python
from src.core.chat_manager import chat_manager
from src.core.protocol_manager import protocol_manager
import asyncio

async def main():
    # 初始化协议管理器
    await protocol_manager.initialize(config.protocols)
    
    # 获取当前激活的协议类型
    active_protocol = protocol_manager.get_active_protocol()
    protocol_type = active_protocol.get_name().lower() if active_protocol else 'maim'
    
    # 初始化聊天管理器（根据协议类型自动选择）
    await chat_manager.initialize(protocol_type)
    
    # 发送消息
    await chat_manager.send_text("你好，麦麦！")
    
    # 打印状态
    chat_manager.print_status()

asyncio.run(main())
```

### 3. 发送不同类型的消息

```python
from src.core.chat_manager import chat_manager
import asyncio

async def main():
    # 发送文本消息
    await chat_manager.send_text("这是一条文本消息")
    
    # 发送图片消息
    await chat_manager.send_image("base64_encoded_image_data")
    
    # 发送表情消息（仅 Maim 协议）
    await chat_manager.send_emoji("🎉")
    
    # 发送复合消息（文本+图片）
    await chat_manager.send_text_and_image(
        "看这张图片",
        "base64_encoded_image_data"
    )
    
    # 发送多段消息
    segments = [
        {'type': 'text', 'data': '第一段文本'},
        {'type': 'image', 'data': 'base64_image'}
    ]
    await chat_manager.send_seglist(segments)

asyncio.run(main())
```

## 详细使用说明

### Maim 聊天

Maim 聊天支持多种消息类型，需要提供用户信息：

```python
from src.core.chats.maim_chat import maim_chat_util

# 方式1：使用单例
await maim_chat_util.send_text(
    text="你好",
    user_id="user123",
    user_nickname="张三",
    user_cardname="群名片"
)

# 方式2：创建实例
from src.core.chats.maim_chat import MaimChat
chat = MaimChat()
await chat.send_text(
    text="你好",
    user_id="user123",
    user_nickname="张三",
    user_cardname="群名片"
)
```

### OpenAI 聊天

OpenAI 聊天主要用于 AI 对话，不需要用户信息：

```python
from src.core.chats.openai_chat import openai_chat_util

# 方式1：使用单例
await openai_chat_util.send_text("你好，能帮我解答一个问题吗？")

# 方式2：创建实例
from src.core.chats.openai_chat import OpenAIChat
chat = OpenAIChat()
await chat.send_text("你好，能帮我解答一个问题吗？")

# 如果使用支持 Vision 的模型，可以发送图片
await openai_chat_util.send_image("base64_encoded_image_data")

# 发送文本+图片
await openai_chat_util.send_text_and_image(
    "描述这张图片",
    "base64_encoded_image_data"
)

# 清除对话历史
openai_chat_util.clear_history()

# 获取对话历史
history = openai_chat_util.get_history()
```

### 聊天管理器

聊天管理器是单例模式，根据配置的协议类型自动选择对应的聊天实现：

```python
from src.core.chat_manager import chat_manager

# 初始化（根据协议类型）
await chat_manager.initialize('maim')  # 或 'openai'

# 统一的接口，自动适配底层协议
await chat_manager.send_text("消息内容")
await chat_manager.send_image("base64_image")
await chat_manager.send_emoji("🎉")
await chat_manager.send_text_and_image("文本", "base64_image")

# 获取当前协议类型
protocol_type = chat_manager.get_protocol_type()
print(f"当前协议: {protocol_type}")

# 获取支持的消息类型
supported_types = chat_manager.get_supported_message_types()
print(f"支持的消息类型: {supported_types}")

# 打印状态
chat_manager.print_status()

# 对话历史管理（仅 OpenAI 协议）
chat_manager.clear_history()
history = chat_manager.get_history()
```

## 消息类型说明

### 文本消息 (text)

所有协议都支持的基本消息类型：

```python
await chat_manager.send_text("这是文本消息")
```

### 图片消息 (image)

- **Maim 协议**：支持发送图片，使用 seglist 格式
- **OpenAI 协议**：仅支持 Vision API 的模型（如 GPT-4 Vision、GPT-4o、通义千问 Vision 等）

```python
await chat_manager.send_image("base64_encoded_image_data")
```

### 表情消息 (emoji)

- **Maim 协议**：支持发送表情
- **OpenAI 协议**：不支持

```python
await chat_manager.send_emoji("🎉")
```

### 复合消息 (seglist)

支持发送多段消息的组合：

```python
segments = [
    {'type': 'text', 'data': '第一段'},
    {'type': 'image', 'data': 'base64_image'},
    {'type': 'text', 'data': '第二段'}
]
await chat_manager.send_seglist(segments)
```

### 文本+图片消息

文本和图片的组合：

```python
await chat_manager.send_text_and_image(
    "这是图片描述",
    "base64_encoded_image_data"
)
```

## 与协议管理器的配合

聊天管理器需要与协议管理器配合使用：

```python
from src.core.chat_manager import chat_manager
from src.core.protocol_manager import protocol_manager
import asyncio

async def initialize_communication():
    # 1. 初始化协议管理器
    await protocol_manager.initialize(config.protocols)
    
    # 2. 获取当前激活的协议
    active_protocol = protocol_manager.get_active_protocol()
    
    # 3. 初始化聊天管理器（根据协议类型）
    protocol_type = active_protocol.get_name().lower()
    await chat_manager.initialize(protocol_type)
    
    # 4. 注册消息处理器
    async def message_handler(message):
        msg_type = message.get('message_segment', {}).get('type')
        if msg_type == 'text':
            content = message['message_segment']['data']
            print(f"收到消息: {content}")
    
    protocol_manager.register_message_handler(message_handler)
    
    # 5. 现在可以使用聊天管理器发送消息了
    await chat_manager.send_text("测试消息")

asyncio.run(initialize_communication())
```

## 示例：集成到 Pet 类

```python
from src.core.chat_manager import chat_manager
from src.core.protocol_manager import protocol_manager

class Pet:
    def __init__(self):
        self.chat_manager = chat_manager
        self.protocol_manager = protocol_manager
    
    async def initialize(self):
        # 初始化通信层
        await self.protocol_manager.initialize(config.protocols)
        
        # 初始化聊天层
        active_protocol = self.protocol_manager.get_active_protocol()
        if active_protocol:
            protocol_type = active_protocol.get_name().lower()
            await self.chat_manager.initialize(protocol_type)
        
        # 注册消息处理器
        self.protocol_manager.register_message_handler(
            self.handle_message
        )
    
    async def handle_message(self, message):
        """处理接收到的消息"""
        # 处理消息逻辑
        pass
    
    async def send_message(self, text: str):
        """发送消息"""
        await self.chat_manager.send_text(text)
```

## 常见问题

### Q: 如何在运行时切换协议？

A: 使用协议管理器切换协议后，需要重新初始化聊天管理器：

```python
# 切换协议
await protocol_manager.switch_protocol('OpenAI')

# 重新初始化聊天管理器
await chat_manager.initialize('openai')
```

### Q: OpenAI 协议支持哪些模型？

A: 
- 所有模型都支持文本消息
- 图片消息需要支持 Vision API 的模型，如：
  - GPT-4 Vision
  - GPT-4o
  - 通义千问 Vision
  - 其他支持视觉 API 的模型

### Q: 如何判断当前协议是否支持某种消息类型？

A: 使用 `is_supported_message_type` 方法：

```python
if chat_manager.is_supported_message_type('image'):
    await chat_manager.send_image("base64_image")
else:
    print("当前协议不支持图片消息")
```

### Q: Maim 协议需要哪些用户信息？

A: Maim 协议需要以下信息：
- `user_id`: 用户 ID
- `user_nickname`: 用户昵称
- `user_cardname`: 用户群名片（可选）

这些信息会在发送消息时自动填充或需要手动提供。

### Q: 如何管理 OpenAI 的对话历史？

A: 使用以下方法：

```python
# 清除对话历史（保留系统提示词）
chat_manager.clear_history()

# 获取对话历史
history = chat_manager.get_history()
```

## 技术细节

### 聊天接口 (IChat)

所有聊天实现必须实现以下接口：

```python
from src.core.chats.interfaces import IChat

class MyChat(IChat):
    async def send(
        self,
        text: str,
        msg_type: str = "text",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        pass
    
    async def send_text(self, text: str) -> bool:
        pass
    
    async def send_image(self, image_data: str) -> bool:
        pass
    
    async def send_emoji(self, emoji: str) -> bool:
        pass
    
    async def send_seglist(self, segments: List, ...) -> bool:
        pass
    
    async def send_text_and_image(self, text: str, image_data: str, ...) -> bool:
        pass
    
    async def send_pixmap_with_text(self, pixmap, text: str = "", ...) -> bool:
        pass
    
    def get_name(self) -> str:
        pass
    
    def is_supported_message_type(self, msg_type: str) -> bool:
        pass
    
    def get_supported_message_types(self) -> List[str]:
        pass
    
    def clear_history(self):
        pass
    
    def get_history(self) -> List:
        pass
```

### 单例模式

`MaimChat` 和 `OpenAIChat` 都提供了全局单例实例：
- `maim_chat_util`: Maim 聊天单例
- `openai_chat_util`: OpenAI 聊天单例

这些单例实例可以直接使用，无需手动创建实例。

### 聊天管理器设计

聊天管理器采用单例模式，根据配置的协议类型自动创建对应的聊天实例：
- 初始化时根据协议类型选择聊天实现
- 提供统一的接口，屏蔽底层协议差异
- 支持运行时查询当前协议类型和支持的消息类型

## 相关文档

- [协议层文档](../protocols/README.md)
- [协议管理器文档](../protocol_manager.py)
- [配置文件说明](../../../config/templates/config.toml.template)
- [主文档](../../../README.md)
