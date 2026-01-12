# 通信协议层实现总结

## 概述

本次实现为桌面宠物应用添加了统一的通信协议抽象层，支持多种协议的无缝切换。

**实现日期：** 2026-01-13  
**版本：** 1.0

---

## 核心组件

### 1. 协议接口 (`src/core/protocols/interfaces.py`)

定义了所有协议必须实现的接口：

```python
class IProtocol(ABC):
    - initialize(config: dict) -> bool
    - connect() -> bool
    - disconnect()
    - send_message(message: dict) -> bool
    - register_message_handler(handler)
    - is_connected() -> bool
    - get_name() -> str
    - cleanup()
```

### 2. 消息转换工具 (`src/util/message_util.py`)

处理协议层与应用层之间的消息格式转换：

```python
- dict_to_message_base(message: dict) -> MessageBase
- message_base_to_dict(message_base) -> dict
- convert_message_format(message: dict) -> dict
- is_valid_message(message: dict) -> bool
- extract_text_content(message: dict) -> str
```

### 3. 协议实现

#### MaimProtocol (`src/core/protocols/maim_protocol.py`)
- 基于 WebSocket 的 Maim 协议
- **消息格式转换**：使用 `message_util.py` 自动将 seglist 转换为 text 格式
- 使用 `maim_message` 库
- 自动处理字典 ↔ MessageBase 对象转换

#### OpenAIProtocol (`src/core/protocols/openai_protocol.py`)
- 基于 HTTP 的 OpenAI API 协议
- 支持对话历史管理
- 支持自定义系统提示词

### 3. 协议工厂 (`src/core/protocols/protocol_factory.py`)

负责创建和管理协议实例：

```python
ProtocolFactory.register_protocol('maim', MaimProtocol)
ProtocolFactory.create_from_dict(config)
```

### 4. 协议管理器 (`src/core/protocol_manager.py`)

单例模式，统一管理所有协议：

```python
protocol_manager = ProtocolManager()
await protocol_manager.initialize(configs)
await protocol_manager.send_message(message)
await protocol_manager.switch_protocol('OpenAI')
```

---

## 架构设计

```
Application Layer (chat.py, router.py)
           ↓
ProtocolManager (协议管理器)
           ↓
   IProtocol (协议接口)
      ↓         ↓
  MaimProtocol  OpenAIProtocol
```

---

## 关键特性

### 1. 消息格式转换

使用专用的消息转换工具（`src/util/message_util.py`）处理格式转换：

```python
# 发送消息：字典 → MessageBase
dict_to_message_base(message_dict)

# 接收消息：MessageBase → 字典
message_base_to_dict(message_base)

# 格式转换：seglist → text
convert_message_format(message)
```

Maim 协议特有的 `seglist` 格式自动转换为统一的 `text` 格式：

```python
# 输入：seglist 格式
{
    'message_segment': {
        'type': 'seglist',
        'data': [
            {'type': 'text', 'data': '你好'},
            {'type': 'emoji', 'data': '😊'}
        ]
    }
}

# 输出：统一格式
{
    'message_segment': {
        'type': 'text',
        'data': '你好'
    }
}
```

### 2. 协议切换

运行时动态切换协议：

```python
await protocol_manager.switch_protocol('OpenAI')
```

### 3. 向后兼容

通过 `RouterAdapter` 保持与旧代码的兼容性：

```python
# 旧代码仍然可以工作
router.send_message(message)
```

---

## 配置示例

### config.toml

```toml
[[protocols]]
type = "maim"
url = "ws://127.0.0.1:8000/ws"
platform = "desktop-pet"

[[protocols]]
type = "openai"
api_key = "sk-xxx"
model = "gpt-3.5-turbo"
```

---

## 代码修改

### chat.py
- 从 `router.send_message` 改为 `protocol_manager.send_message`

### router.py
- 添加 `RouterAdapter` 保持兼容性
- 简化 `message_handler`（协议内部已处理格式转换）
- 注册到 `protocol_manager` 而不是直接使用 `Router`

---

## 测试

测试脚本：`tests/test_protocol_switching.py`

运行测试：
```bash
python tests/test_protocol_switching.py
```

---

## 扩展指南

### 添加自定义协议

```python
from src.core.protocols.interfaces import IProtocol
from src.core.protocols.protocol_factory import ProtocolFactory

class CustomProtocol(IProtocol):
    # 实现接口方法
    pass

# 注册协议
ProtocolFactory.register_protocol('custom', CustomProtocol)
```

---

## 文档

详细文档：`src/core/protocols/README.md`

---

## 总结

✅ 实现了统一的协议抽象层  
✅ 支持 Maim 和 OpenAI 协议  
✅ 支持运行时协议切换  
✅ 自动处理消息格式转换  
✅ 保持向后兼容性  
✅ 易于扩展新协议  
✅ 完整的测试覆盖  
✅ 详细的文档说明
