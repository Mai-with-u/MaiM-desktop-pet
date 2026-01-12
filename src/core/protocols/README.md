# 通信协议层

## 概述

通信协议层提供了一个统一的抽象接口，支持多种通信协议的无缝切换。目前支持：

- **Maim 协议**：基于 WebSocket 的通信协议，适用于连接 Maim 后端服务
- **OpenAI 协议**：基于 OpenAI API 的 HTTP 通信协议，适用于直接使用 AI 对话
- **自定义协议**：支持扩展自定义协议

## 架构设计

```
┌─────────────────────────────────────────────────┐
│           Application Layer                     │
│         (chat.py, router.py)                    │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────┐
│        ProtocolManager (协议管理器)             │
│  - 统一管理所有协议                             │
│  - 协议切换                                     │
│  - 消息分发                                     │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────┐
│         IProtocol (协议接口)                     │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼─────┐  ┌──────▼──────┐
│ MaimProtocol│  │OpenAIProtocol│
└─────────────┘  └─────────────┘
```

## 快速开始

### 1. 配置协议

在 `config.toml` 中配置协议：

```toml
[[protocols]]
type = "maim"
url = "ws://127.0.0.1:8000/ws"
platform = "desktop-pet"
```

或使用 OpenAI 协议：

```toml
[[protocols]]
type = "openai"
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
model = "gpt-3.5-turbo"
system_prompt = "你是一个友好的桌面宠物助手"
```

### 2. 初始化协议管理器

```python
from src.core.protocol_manager import protocol_manager
import asyncio

async def main():
    # 从配置加载协议列表
    from config import config
    
    # 初始化协议管理器
    await protocol_manager.initialize(config.protocols)
    
    # 注册消息处理器
    async def message_handler(message):
        print(f"收到消息: {message}")
    
    protocol_manager.register_message_handler(message_handler)
    
    # 发送消息
    await protocol_manager.send_message({
        'message_segment': {
            'type': 'text',
            'data': '你好，麦麦！'
        }
    })
    
    # 切换协议
    await protocol_manager.switch_protocol('OpenAI')

asyncio.run(main())
```

### 3. 清理资源

```python
# 程序退出时清理
await protocol_manager.cleanup()
```

## 详细使用说明

### 协议接口 (IProtocol)

所有协议必须实现以下接口：

```python
from src.core.protocols.interfaces import IProtocol

class MyProtocol(IProtocol):
    async def initialize(self, config: dict) -> bool:
        """初始化协议"""
        pass
    
    async def connect(self) -> bool:
        """建立连接"""
        pass
    
    async def disconnect(self):
        """断开连接"""
        pass
    
    async def send_message(self, message: dict) -> bool:
        """发送消息"""
        pass
    
    def register_message_handler(self, handler):
        """注册消息处理器"""
        pass
    
    def is_connected(self) -> bool:
        """是否已连接"""
        pass
    
    def get_name(self) -> str:
        """获取协议名称"""
        pass
    
    async def cleanup(self):
        """清理资源"""
        pass
```

### 协议工厂 (ProtocolFactory)

协议工厂用于创建协议实例：

```python
from src.core.protocols.protocol_factory import ProtocolFactory

# 创建 Maim 协议
config = {
    'type': 'maim',
    'url': 'ws://127.0.0.1:8000/ws',
    'platform': 'default'
}
protocol = ProtocolFactory.create_from_dict(config)

# 创建 OpenAI 协议
config = {
    'type': 'openai',
    'api_key': 'sk-xxx',
    'model': 'gpt-3.5-turbo'
}
protocol = ProtocolFactory.create_from_dict(config)

# 检查协议是否支持
if ProtocolFactory.is_protocol_supported('maim'):
    print("Maim 协议已支持")

# 获取所有支持的协议
protocols = ProtocolFactory.get_supported_protocols()
print(f"支持的协议: {protocols}")
```

### 注册自定义协议

```python
from src.core.protocols.interfaces import IProtocol
from src.core.protocols.protocol_factory import ProtocolFactory

class CustomProtocol(IProtocol):
    """自定义协议示例"""
    
    def __init__(self):
        self._config = {}
        self._connected = False
    
    async def initialize(self, config: dict) -> bool:
        self._config = config
        print(f"初始化自定义协议: {config}")
        return True
    
    async def connect(self) -> bool:
        print("连接自定义协议")
        self._connected = True
        return True
    
    async def disconnect(self):
        print("断开自定义协议")
        self._connected = False
    
    async def send_message(self, message: dict) -> bool:
        print(f"发送消息: {message}")
        return True
    
    def register_message_handler(self, handler):
        print("注册消息处理器")
    
    def is_connected(self) -> bool:
        return self._connected
    
    def get_name(self) -> str:
        return "Custom"
    
    async def cleanup(self):
        await self.disconnect()

# 注册自定义协议
ProtocolFactory.register_protocol('custom', CustomProtocol)

# 现在可以使用自定义协议了
config = {'type': 'custom'}
protocol = ProtocolFactory.create_from_dict(config)
```

### 协议管理器 (ProtocolManager)

协议管理器是单例模式，统一管理所有协议：

```python
from src.core.protocol_manager import protocol_manager

# 初始化
await protocol_manager.initialize(config.protocols)

# 发送消息（使用当前激活的协议）
success = await protocol_manager.send_message(message_dict)

# 切换协议
await protocol_manager.switch_protocol('OpenAI')

# 获取当前激活的协议
active_protocol = protocol_manager.get_active_protocol()

# 获取指定协议
protocol = protocol_manager.get_protocol('Maim')

# 获取所有协议名称
names = protocol_manager.get_protocol_names()

# 打印状态
protocol_manager.print_status()

# 清理
await protocol_manager.cleanup()
```

## 消息格式

### 统一消息格式

所有协议使用统一的消息格式：

```python
# 文本消息
{
    'message_segment': {
        'type': 'text',
        'data': '消息内容'
    }
}

# 多段消息
{
    'message_segment': {
        'type': 'seglist',
        'data': [
            {'type': 'text', 'data': '第一段'},
            {'type': 'text', 'data': '第二段'}
        ]
    }
}
```

### Maim 协议消息

Maim 协议直接使用上述统一格式。

### OpenAI 协议消息

OpenAI 协议会自动处理消息格式：

- 发送的文本消息会被添加到对话历史
- OpenAI 的回复会通过消息处理器返回
- 支持对话历史管理

## 配置说明

### Maim 协议配置

```toml
[[protocols]]
type = "maim"
url = "ws://127.0.0.1:8000/ws"
platform = "desktop-pet"
token = "optional_token"
```

**参数说明：**
- `type`: 必须为 "maim"
- `url`: WebSocket 服务器地址
- `platform`: 平台标识
- `token`: 可选的认证令牌

### OpenAI 协议配置

```toml
[[protocols]]
type = "openai"
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
base_url = "https://api.openai.com/v1"
model = "gpt-3.5-turbo"
system_prompt = "你是一个友好的桌面宠物助手"
```

**参数说明：**
- `type`: 必须为 "openai"
- `api_key`: OpenAI API 密钥（必填）
- `base_url`: API 基础地址（可选，默认官方地址）
- `model`: 模型名称（可选，默认 gpt-3.5-turbo）
- `system_prompt`: 系统提示词（可选）

### 多协议配置

可以同时配置多个协议：

```toml
[[protocols]]
type = "maim"
url = "ws://127.0.0.1:8000/ws"
platform = "desktop-pet"

[[protocols]]
type = "openai"
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
model = "gpt-3.5-turbo"
```

程序启动时会自动使用第一个协议作为默认协议。

## 协议切换

### 运行时切换协议

```python
# 切换到 OpenAI 协议
await protocol_manager.switch_protocol('OpenAI')

# 切换到 Maim 协议
await protocol_manager.switch_protocol('Maim')
```

### 切换协议时的行为

1. 断开当前激活的协议
2. 连接新协议
3. 所有新消息将通过新协议发送

## 示例代码

### 完整示例：使用协议管理器

```python
import asyncio
from src.core.protocol_manager import protocol_manager
from config import config

async def message_handler(message):
    """消息处理器"""
    msg_type = message.get('message_segment', {}).get('type')
    if msg_type == 'text':
        content = message['message_segment']['data']
        print(f"收到文本消息: {content}")

async def main():
    # 初始化协议管理器
    await protocol_manager.initialize(config.protocols)
    
    # 注册消息处理器
    protocol_manager.register_message_handler(message_handler)
    
    # 发送消息
    await protocol_manager.send_message({
        'message_segment': {
            'type': 'text',
            'data': '你好，麦麦！'
        }
    })
    
    # 打印状态
    protocol_manager.print_status()
    
    # 切换协议（如果配置了多个）
    if len(protocol_manager.get_protocol_names()) > 1:
        await protocol_manager.switch_protocol('OpenAI')
        print("已切换到 OpenAI 协议")
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # 清理
        await protocol_manager.cleanup()
        print("程序退出")

if __name__ == "__main__":
    asyncio.run(main())
```

### 集成到 chat.py

```python
from src.core.protocol_manager import protocol_manager
from src.core.chat import ChatManager

class ChatManager:
    def __init__(self):
        self.protocol_manager = protocol_manager
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置消息处理器"""
        self.protocol_manager.register_message_handler(
            self._handle_message
        )
    
    async def _handle_message(self, message):
        """处理接收到的消息"""
        # 解析消息
        msg_type = message.get('message_segment', {}).get('type')
        
        if msg_type == 'text':
            content = message['message_segment']['data']
            # 处理文本消息
            await self._process_text_message(content)
    
    async def send_message(self, text: str):
        """发送消息"""
        message = {
            'message_segment': {
                'type': 'text',
                'data': text
            }
        }
        await self.protocol_manager.send_message(message)
    
    async def cleanup(self):
        """清理资源"""
        await self.protocol_manager.cleanup()
```

## 常见问题

### Q: 如何添加新的协议？

A: 创建一个实现 IProtocol 接口的类，然后使用 ProtocolFactory.register_protocol() 注册。

### Q: 协议切换会影响正在进行的对话吗？

A: 不会。每个协议维护自己的状态，切换协议不会影响对话历史（OpenAI 协议会保持对话历史）。

### Q: 可以同时使用多个协议吗？

A: 可以配置多个协议，但同一时间只能有一个激活的协议。可以在运行时切换。

### Q: 如何调试协议问题？

A: 查看 logs/pet.log 文件，协议管理器会记录详细的日志信息。也可以使用 `protocol_manager.print_status()` 查看当前状态。

### Q: OpenAI 协议支持哪些功能？

A: 支持基本的对话功能，包括：
- 文本对话
- 对话历史管理
- 自定义系统提示词
- 支持自定义 API 端点

## 技术细节

### 协议生命周期

1. **初始化** (initialize)
   - 解析配置
   - 创建必要的资源

2. **连接** (connect)
   - 建立连接
   - 注册消息处理器

3. **使用** (send_message, message_handler)
   - 发送和接收消息

4. **断开** (disconnect)
   - 关闭连接

5. **清理** (cleanup)
   - 释放所有资源

### 线程安全

协议管理器的设计考虑了线程安全：
- 所有异步操作都在事件循环中执行
- 使用 asyncio 锁保护共享状态

### 性能考虑

- 协议切换开销较小，适合频繁切换
- OpenAI 协议使用 HTTP 会话池，提高性能
- Maim 协议使用 WebSocket 长连接，降低延迟

## 未来扩展

### 计划中的协议

- **Telegram 协议**：支持 Telegram Bot API
- **Slack 协议**：支持 Slack Web API
- **本地 LLM 协议**：支持本地部署的大语言模型

### 功能增强

- 协议热加载
- 协议负载均衡
- 消息队列支持
- 协议插件系统

## 相关文档

- [配置文件说明](../../../config/templates/config.toml.template)
- [主文档](../../../README.md)
- [开发指南](../../../docs/DOCS_INDEX.md)
