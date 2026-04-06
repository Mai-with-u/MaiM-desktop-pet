# 简化的协议和聊天管理架构

**创建时间**: 2026-04-06  
**架构状态**: ✅ 已完成  

---

## 📁 目录结构

```
src/core/
├── protocol/              # 协议管理模块
│   ├── __init__.py
│   └── manager.py        # 协议管理器
│
├── chat/                  # 聊天管理模块
│   ├── __init__.py
│   └── manager.py        # 聊天管理器
│
├── model_manager.py       # 模型管理器（可选）
└── thread_manager.py      # 线程管理器
```

---

## 🎯 职责划分

### 协议管理器 (protocol/manager.py)

**职责**：
1. ✅ 确认聊天协议类型（openai 兼容 / maim）
2. ✅ 返回正确的 base_url 和 api_key
3. ✅ 提供连接信息给聊天管理器

**核心方法**：
```python
# 获取协议类型
get_protocol_type(model_name) -> 'maim' / 'openai' / 'gemini'

# 获取连接信息
get_connection_info(model_name) -> {
    'protocol_type': 'maim',
    'base_url': 'ws://127.0.0.1:8000/ws',
    'api_key': '',
    'model_identifier': 'maim-default',
    ...
}

# 根据任务获取连接信息
get_task_connection_info(task_type) -> {...}
```

**不负责**：
- ❌ 建立连接
- ❌ 发送消息
- ❌ 接收消息

---

### 聊天管理器 (chat/manager.py)

**职责**：
1. ✅ 接收协议管理器提供的连接信息
2. ✅ 根据协议类型创建对应的客户端
3. ✅ 管理聊天会话
4. ✅ 发送和接收消息

**核心方法**：
```python
# 初始化
initialize(task_type) -> bool

# 发送消息
send_message(content) -> bool

# 清理资源
cleanup()
```

**协议支持**：
- ✅ OpenAI 兼容协议（HTTP）
- ✅ Gemini 协议（HTTP）
- ⚠️ Maim 协议（WebSocket - 待实现）

---

## 🔄 协作流程

### 初始化流程

```
1. main.py
   ↓
2. chat_manager.initialize('chat')
   ↓
3. protocol_manager.initialize()
   - 加载 model_config.toml
   - 解析供应商和模型配置
   ↓
4. protocol_manager.get_task_connection_info('chat')
   - 查找任务配置
   - 选择模型
   - 返回连接信息
   ↓
5. chat_manager 根据协议类型初始化
   - 如果是 maim: 初始化 WebSocket（待实现）
   - 如果是 openai: 创建 HTTP session
```

### 发送消息流程

```
1. 用户输入
   ↓
2. chat_manager.send_message(content)
   ↓
3. 获取连接信息
   protocol_manager.get_task_connection_info(task_type)
   ↓
4. 根据协议类型发送
   - 如果是 maim: 通过 WebSocket 发送（待实现）
   - 如果是 openai: 通过 HTTP API 发送
   ↓
5. 接收响应
   ↓
6. 触发 UI 信号
   signals_bus.message_received.emit(reply)
```

---

## 📝 使用示例

### 协议管理器

```python
from src.core.protocol import protocol_manager

# 初始化
await protocol_manager.initialize()

# 获取协议类型
protocol_type = protocol_manager.get_protocol_type('maim-local')
# 返回: 'maim'

# 获取连接信息
info = protocol_manager.get_connection_info('maim-local')
# 返回: {
#     'protocol_type': 'maim',
#     'base_url': 'ws://127.0.0.1:8000/ws',
#     'api_key': '',
#     ...
# }

# 判断协议类型
if protocol_manager.is_maim_protocol('maim-local'):
    print("是 Maim 协议")
```

### 聊天管理器

```python
from src.core.chat import chat_manager

# 初始化（使用 chat 任务）
await chat_manager.initialize('chat')

# 发送消息
await chat_manager.send_message('你好')

# 清理资源
await chat_manager.cleanup()
```

---

## 🔧 配置示例

### model_config.toml

```toml
# 供应商配置
[[api_providers]]
name = "Maim-Local"
base_url = "ws://127.0.0.1:8000/ws"
client_type = "maim"
api_key = ""

[[api_providers]]
name = "DeepSeek"
base_url = "https://api.deepseek.com/v1"
client_type = "openai"
api_key = "sk-xxx"

# 模型配置
[[models]]
model_identifier = "maim-default"
name = "maim-local"
api_provider = "Maim-Local"

[[models]]
model_identifier = "deepseek-chat"
name = "deepseek-chat"
api_provider = "DeepSeek"

# 任务配置
[model_task_config.chat]
model_list = ["maim-local", "deepseek-chat"]
temperature = 0.7
max_tokens = 800
```

---

## ⚠️ 待实现功能

### Maim WebSocket 集成

**位置**: `src/core/chat/manager.py` 的 `_initialize_maim()` 和 `_send_maim()` 方法

**实现计划**：
1. 使用 `maim_message` 库的原生处理方式
2. 初始化时向聊天管理器请求初始化 WebSocket 连接
3. 注册消息处理器
4. 通过 WebSocket 发送和接收消息

**示例代码**（待实现）：
```python
async def _initialize_maim(self, connection_info):
    from maim_message import Router, RouteConfig, TargetConfig
    
    # 创建路由配置
    route_config = RouteConfig(
        route_config={
            connection_info['platform']: TargetConfig(
                url=connection_info['base_url'],
                token=connection_info['api_key']
            )
        }
    )
    
    # 创建路由器
    self._router = Router(route_config)
    
    # 注册消息处理器
    self._router.register_class_handler(self._handle_maim_message)
    
    # 启动连接
    await self._router.connect(connection_info['platform'])
```

---

## ✅ 完成状态

| 组件 | 职责 | 状态 |
|------|------|------|
| 协议管理器 | 协议识别、配置管理 | ✅ 完成 |
| 聊天管理器 - HTTP | OpenAI/Gemini 协议 | ✅ 完成 |
| 聊天管理器 - WebSocket | Maim 协议 | ⚠️ 待实现 |
| 架构文档 | 完整说明 | ✅ 完成 |

---

## 🎯 架构优势

| 优势 | 说明 |
|------|------|
| **职责分离** | 协议管理和聊天逻辑完全分离 |
| **模块化** | 两个独立的文件夹，易于维护 |
| **可扩展** | 添加新协议只需扩展聊天管理器 |
| **清晰** | 每个管理器职责单一明确 |

---

## 📊 调用关系

```
用户 → chat_manager.send_message()
         ↓
       chat_manager 获取连接信息
         ↓
       protocol_manager.get_task_connection_info()
         ↓
       protocol_manager 返回连接信息
         ↓
       chat_manager 根据协议类型发送消息
         ↓
       HTTP/WebSocket 发送
         ↓
       接收响应
         ↓
       触发 UI 信号
```

---

**架构重构完成！** 协议管理和聊天管理完全分离，职责清晰。🎉