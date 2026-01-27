# 麦麦桌面宠物 - 通信层架构说明

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层 (UI)                           │
│  - DesktopPet (pet.py)                                     │
│  - BubbleInput (输入框)                                     │
│  - ScreenshotSelector (截图)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ 发送消息
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   聊天管理层                         │
│  - 提供统一的消息发送接口                                   │
│  - 根据协议类型选择对应的聊天实现                             │
│  - ChatManager (单例)                                       │
│    ├── OpenAIChat (OpenAI 协议聊天实现)                     │
│    └── MaimChat (Maim 协议聊天实现)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ 协议管理
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 协议管理层                  │
│  - 管理所有通信协议                                           │
│  - 协议的注册、初始化、切换                                   │
│  - ProtocolManager (单例)                                    │
│    ├── OpenAIProtocol (OpenAI HTTP 协议)                    │
│    └── MaimProtocol (Maim WebSocket 协议)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ 网络通信
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                       外部 API 服务                         │
│  - OpenAI API / 兼容 API                                    │
│  - Maim WebSocket 服务                                      │
└─────────────────────────────────────────────────────────────┘
```

## 配置文件结构

### model_config.toml

```toml
# 1. API 提供商配置
[[api_providers]]
name = "DeepSeek"
base_url = "https://api.deepseek.com/v1"
client_type = "openai"
api_key = "sk-xxx"

# 2. 模型配置
[[models]]
model_identifier = "deepseek-chat"
name = "deepseek-chat"
api_provider = "DeepSeek"
price_in = 0.0
price_out = 0.0

# 3. 任务配置（关键！）
[model_task_config.chat]
model_list = ["deepseek-chat", "qwen3-30b"]
temperature = 0.7
max_tokens = 800

[model_task_config.expression]
model_list = ["deepseek-chat", "qwen3-30b"]
temperature = 0.5
max_tokens = 800

[model_task_config.image_recognition]
model_list = ["qwen3-vl-8b"]
max_tokens = 800
```

## 当前消息发送流程

### 示例：用户发送文本消息

```python
# 1. 用户在输入框输入文本
# pet.py: handle_user_input(text)

# 2. 调用 ChatManager 发送
await chat_manager.send_text(text)

# 3. ChatManager 路由到对应的 Chat 实现
# ChatManager._chat.send_text(text)
# -> OpenAIChat.send_text(text) 或 MaimChat.send_text(text)

# 4. Chat 构建消息格式
# OpenAIChat 构建消息: {'message_segment': {'type': 'text', 'data': text}}

# 5. 通过 ProtocolManager 发送
await protocol_manager.send_message(message)

# 6. ProtocolManager 路由到当前激活的协议
# ProtocolManager._active_protocol.send_message(message)
# -> OpenAIProtocol.send_message(message) 或 MaimProtocol.send_message(message)

# 7. 协议与外部 API 通信
# OpenAIProtocol: HTTP POST 到 OpenAI API
# MaimProtocol: WebSocket 发送消息
```

## 重要发现

### 当前架构的限制

1. **单一模型配置**
   - ChatManager 初始化时只从 `[model_task_config.chat]` 读取模型
   - 所有消息都使用相同的模型
   - 无法根据任务类型动态切换模型

2. **模型固定在协议层**
   - OpenAIProtocol 在初始化时就确定了模型名称
   - 后续无法动态更改模型
   - 每个 base_url 只能配置一个模型

3. **缺少任务路由机制**
   - 没有根据任务类型选择模型的机制
   - `expression`、`image_recognition` 等任务的配置无法使用

## 如何实现任务类型的消息发送

### 方案 1：扩展 ChatManager（推荐）

在 ChatManager 中添加任务类型参数：

```python
class ChatManager:
    async def send_by_task(
        self,
        task_type: str,  # 'chat', 'expression', 'image_recognition' 等
        text: str = None,
        image_data: str = None,
        **kwargs
    ) -> bool:
        """
        根据任务类型发送消息
        
        Args:
            task_type: 任务类型（对应 model_task_config 中的键）
            text: 文本内容
            image_data: 图片数据（base64）
            **kwargs: 其他参数
        """
        # 1. 获取任务配置
        from config.model_config_loader import get_task_config
        task_config = get_task_config(task_type)
        if not task_config:
            logger.error(f"任务配置未找到: {task_type}")
            return False
        
        # 2. 获取第一个可用模型
        model_name = task_config.model_list[0]
        model_config = get_model_config(model_name)
        if not model_config:
            logger.error(f"模型配置未找到: {model_name}")
            return False
        
        # 3. 获取提供商配置
        provider_config = get_provider_config(model_config.api_provider)
        if not provider_config:
            logger.error(f"提供商配置未找到: {model_config.api_provider}")
            return False
        
        # 4. 确定协议类型
        protocol_type = provider_config.client_type.lower()
        
        # 5. 创建或获取协议实例
        if protocol_type == 'openai':
            protocol_name = f"OpenAI-{provider_config.base_url}"
            protocol = protocol_manager.get_protocol(protocol_name)
            if not protocol:
                # 创建临时协议实例
                from src.core.protocols.openai_protocol import OpenAIProtocol
                protocol = OpenAIProtocol()
                await protocol.initialize({
                    'api_key': provider_config.api_key,
                    'base_url': provider_config.base_url,
                    'model': model_name,
                    'temperature': task_config.get('temperature'),
                    'max_tokens': task_config.get('max_tokens')
                })
        elif protocol_type == 'maim':
            protocol_name = f"Maim-{provider_config.name}"
            protocol = protocol_manager.get_protocol(protocol_name)
        
        # 6. 发送消息
        if protocol:
            message = self._build_message(text, image_data)
            return await protocol.send_message(message)
        
        return False
    
    def _build_message(self, text, image_data):
        """构建消息格式"""
        if text and image_data:
            return {
                'message_segment': {
                    'type': 'seglist',
                    'data': [
                        {'type': 'text', 'data': text},
                        {'type': 'image', 'data': image_data}
                    ]
                }
            }
        elif text:
            return {
                'message_segment': {
                    'type': 'text',
                    'data': text
                }
            }
        elif image_data:
            return {
                'message_segment': {
                    'type': 'image',
                    'data': image_data
                }
            }
```

### 方案 2：为每个任务创建独立的 Chat 实例

```python
class TaskChatManager:
    """任务聊天管理器 - 为每个任务创建独立的聊天实例"""
    
    def __init__(self):
        self._task_chats = {}  # {task_type: chat_instance}
    
    async def initialize(self):
        """初始化所有任务聊天实例"""
        from config.model_config_loader import get_all_task_configs
        
        task_configs = get_all_task_configs()
        
        for task_type, config in task_configs.items():
            # 为每个任务创建聊天实例
            if config.model_list:
                model_name = config.model_list[0]
                chat = await self._create_chat_for_model(model_name)
                self._task_chats[task_type] = chat
                logger.info(f"任务 {task_type} 已绑定模型: {model_name}")
    
    async def send_by_task(self, task_type, text=None, image_data=None):
        """使用指定任务发送消息"""
        chat = self._task_chats.get(task_type)
        if not chat:
            logger.error(f"任务 {task_type} 未初始化")
            return False
        
        return await chat.send(text, image_data)
```

## 实际使用示例

### 使用方案 1（推荐）

```python
# 1. 发送普通对话消息
await chat_manager.send_by_task(
    task_type='chat',
    text='你好，麦麦！'
)

# 2. 发送表情分析消息
await chat_manager.send_by_task(
    task_type='expression',
    text='分析这个表情的含义'
)

# 3. 发送图片识别消息
await chat_manager.send_by_task(
    task_type='image_recognition',
    image_data=base64_image,
    text='描述这张图片'
)

# 4. 发送语音识别消息
await chat_manager.send_by_task(
    task_type='voice',
    audio_data=base64_audio
)
```

## 旧架构 vs 新架构

### src/core/chat.py 的作用

**位置**：`src/core/chat.py`（旧实现）

**职责**：
- 创建 Maim 协议专用的消息对象（使用 `maim_message` 库的 `MessageBase`、`UserInfo`、`Seg`）
- 提供简化版的消息发送方法
- 构建完整的用户信息和消息信息

**特点**：
- ✅ 完整的 Maim 协议支持
- ✅ 支持 seglist 复合消息
- ✅ 自动处理用户信息
- ❌ 仅支持 Maim 协议
- ❌ 依赖 `maim_message` 库的特定格式
- ❌ 无法灵活切换到其他协议

### 新架构的优势

**新架构**：`ChatManager` + `ProtocolManager`

**优势对比**：

| 特性 | 旧架构 (chat.py) | 新架构 (chat_manager) |
|------|------------------|----------------------|
| **协议支持** | 仅 Maim | Maim + OpenAI + 可扩展 |
| **消息格式** | MessageBase 对象 | 统一字典格式 |
| **协议切换** | 不支持 | 支持运行时切换 |
| **配置驱动** | 硬编码 | model_config.toml |
| **任务路由** | 不支持 | 支持（扩展后） |
| **依赖** | maim_message | 协议抽象层 |
| **代码复用** | 低 | 高 |

### 使用对比

**旧方式（不推荐）**：
```python
from src.core.chat import chat_util

# 只能发送 Maim 协议消息
await chat_util.send_text("你好")

# 创建复杂的 Maim 消息
await chat_util.send_seglist([
    ("text", "这是一张图片："),
    ("image", "base64..."),
])
```

**新方式（推荐）**：
```python
from src.core.chat_manager import chat_manager

# 统一接口，自动选择协议
await chat_manager.send_text("你好")

# 支持多种协议
await chat_manager.send_pixmap_with_text(pixmap, "描述这张图片")

# 未来扩展：支持任务类型
await chat_manager.send_by_task('image_recognition', image_data=base64)
```

### 迁移指南

**从旧架构迁移到新架构**：

1. **替换导入**
   ```python
   # 旧
   from src.core.chat import chat_util
   
   # 新
   from src.core.chat_manager import chat_manager
   ```

2. **替换调用**
   ```python
   # 旧
   await chat_util.send_text("你好")
   
   # 新
   await chat_manager.send_text("你好")
   ```

3. **特殊处理**
   ```python
   # 旧 - Maim 协议特有
   await chat_util.send_seglist([
       ("text", "文本"),
       ("image", "base64..."),
   ], 
   user_id="123",  # Maim 需要
   user_nickname="昵称")
   
   # 新 - 协议无关
   await chat_manager.send_text_and_image(
       text="文本",
       image_data="base64...",
       user_id="123",  # Maim 协议需要
       user_nickname="昵称"
   )
   ```

### 当前状态

**使用情况**：
- ✅ 主要代码使用 `ChatManager`（新架构）
- ✅ `src/frontend/presentation/pet.py` 使用 `chat_manager`
- ✅ `src/core/chats/` 下的实现都是新架构
- ⚠️ `src/core/chat.py` 保留用于向后兼容
- ⚠️ `src/frontend/pet.py.backup` 中仍使用旧方式

**建议**：
1. **继续使用** `ChatManager` 作为主要接口
2. **保留** `src/core/chat.py` 用于向后兼容
3. **逐步迁移** 旧代码到新架构
4. **文档维护**：更新文档说明新架构的优势

### 代码位置

| 文件 | 作用 | 架构 |
|------|------|------|
| `src/core/chat.py` | 旧的聊天工具类 | 旧架构 |
| `src/core/chat_manager.py` | 新的聊天管理器 | 新架构 |
| `src/core/chats/openai_chat.py` | OpenAI 聊天实现 | 新架构 |
| `src/core/chats/maim_chat.py` | Maim 聊天实现 | 新架构 |
| `src/core/protocol_manager.py` | 协议管理器 | 新架构 |
| `src/core/protocols/openai_protocol.py` | OpenAI 协议 | 新架构 |
| `src/core/protocols/maim_protocol.py` | Maim 协议 | 新架构 |

### 架构演进历史

```
v1.0: 单一 Maim 协议
  └── src/core/chat.py (Maim 专用)

v2.0: 多协议支持（当前）
  ├── src/core/chat_manager.py (统一接口)
  ├── src/core/chats/ (聊天实现层)
  │   ├── openai_chat.py
  │   └── maim_chat.py
  ├── src/core/protocol_manager.py (协议管理层)
  └── src/core/protocols/ (协议实现层)
      ├── openai_protocol.py
      └── maim_protocol.py

v3.0: 任务类型路由（计划中）
  └── ChatManager.send_by_task()
      ├── 根据任务类型选择模型
      └── 自动切换协议
```

## 总结

### 当前架构特点

✅ 优点：
- 分层清晰，职责明确
- 支持多种协议（OpenAI、Maim）
- 配置灵活，易于扩展
- 单例模式，全局唯一

❌ 限制：
- 无法根据任务类型动态切换模型
- 每个协议只能配置一个模型
- 任务配置（expression、image_recognition 等）未被充分利用

### 建议改进

1. **实现任务路由机制**
   - 在 ChatManager 中添加 `send_by_task()` 方法
   - 根据 task_type 动态选择模型和协议

2. **支持多模型实例**
   - 允许为同一个 base_url 创建多个模型实例
   - 每个任务可以独立配置模型

3. **模型缓存**
   - 缓存已创建的协议实例
   - 避免重复创建和销毁

4. **错误处理和降级**
   - 当第一个模型不可用时，自动切换到下一个
   - 实现任务级别的故障转移

### 实现优先级

🔥 高优先级：
- 在 ChatManager 中添加 `send_by_task()` 方法
- 支持根据任务类型选择模型

🔸 中优先级：
- 实现模型缓存机制
- 添加任务级别的错误处理

🔹 低优先级：
- 优化协议实例管理
- 添加性能监控和统计