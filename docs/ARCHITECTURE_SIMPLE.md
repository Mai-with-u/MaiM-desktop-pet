# 简化的配置和协议架构

**创建时间**: 2026-04-06  
**架构状态**: ✅ 已完成  

---

## 🎯 架构设计

### 三层配置结构

```
供应商 (api_providers)
    ↓
模型 (models)
    ↓
任务配置 (model_task_config)
```

---

## 📁 文件结构

### 核心组件

```
src/core/
├── model_manager.py      # 模型管理器
├── protocol_client.py     # 协议客户端
└── chat_client.py         # 聊天客户端

config/
├── schema.py             # 配置模式定义
└── loader.py             # 配置加载器
```

---

## 🔧 组件说明

### 1. 配置模式 (config/schema.py)

**三层结构定义**：

#### 第一层：供应商配置
```python
class APIProviderConfig:
    name: str              # 供应商名称
    base_url: str          # API 地址
    client_type: str       # 客户端类型 (maim/openai/gemini)
    api_key: str           # API 密钥
    max_retry: int         # 最大重试次数
    timeout: int           # 超时时间
    retry_interval: int    # 重试间隔
```

#### 第二层：模型配置
```python
class ModelConfig:
    model_identifier: str  # 模型标识符
    name: str              # 模型名称
    api_provider: str      # 使用的供应商
    price_in: float        # 输入价格
    price_out: float       # 输出价格
```

#### 第三层：任务配置
```python
class TaskConfig:
    model_list: List[str]  # 模型列表（按优先级）
    temperature: float     # 温度参数
    max_tokens: int        # 最大输出token
```

---

### 2. 模型管理器 (src/core/model_manager.py)

**核心职责**：
- 查询可用模型类型
- 根据类型查询配置
- 提供连接信息

**关键方法**：

```python
# 查询可用任务类型
get_available_task_types() -> List[str]

# 查询任务可用模型
get_available_models_for_task(task_type) -> List[str]

# 根据模型名获取连接信息
get_model_connection_info(model_name) -> Dict[str, Any]

# 根据任务类型获取连接信息
get_task_connection_info(task_type, model_index) -> Dict[str, Any]
```

**使用示例**：

```python
# 初始化
await model_manager.initialize()

# 查询可用任务
tasks = model_manager.get_available_task_types()
# 返回: ['chat', 'image_recognition', 'tool_use', ...]

# 获取 chat 任务的连接信息
info = model_manager.get_task_connection_info('chat')
# 返回: {
#     'base_url': 'ws://127.0.0.1:8000/ws',
#     'api_key': '',
#     'client_type': 'maim',
#     'model_identifier': 'maim-default',
#     'model_name': 'maim-local',
#     ...
# }
```

---

### 3. 协议客户端 (src/core/protocol_client.py)

**核心职责**：
- 建立 WebSocket/HTTP 连接
- 发送消息
- 接收消息

**支持的协议**：
- `maim`: WebSocket 长连接
- `openai`: HTTP API（OpenAI 兼容）
- `gemini`: HTTP API（Google Gemini）

**使用示例**：

```python
# 初始化
client = ProtocolClient()
await client.initialize(connection_info)

# 建立连接
await client.connect()

# 注册消息处理器
client.register_message_handler(handler)

# 发送消息
await client.send_message({'content': '你好'})

# 断开连接
await client.disconnect()
```

---

### 4. 聊天客户端 (src/core/chat_client.py)

**核心职责**：
- 用户交互
- 消息发送和接收
- 任务切换

**使用示例**：

```python
# 初始化（使用 chat 任务）
chat_client = ChatClient()
await chat_client.initialize('chat')

# 发送消息
await chat_client.send_message('你好')

# 切换任务
await chat_client.switch_task('image_recognition')

# 清理资源
await chat_client.cleanup()
```

---

## 🔄 数据流

### 初始化流程

```
1. main.py
   ↓
2. chat_client.initialize('chat')
   ↓
3. model_manager.initialize()
   - 加载 model_config.toml
   - 解析三层配置
   ↓
4. get_task_connection_info('chat')
   - 查询任务模型列表
   - 选择第一个模型
   - 获取供应商配置
   - 组合连接信息
   ↓
5. protocol_client.initialize(connection_info)
   - 创建 WebSocket/HTTP 客户端
   ↓
6. protocol_client.connect()
   - 建立连接
```

### 发送消息流程

```
1. 用户输入
   ↓
2. chat_client.send_message(content)
   ↓
3. protocol_client.send_message(message)
   ↓
4. WebSocket/HTTP 发送
   ↓
5. 接收响应
   ↓
6. _handle_message(message)
   ↓
7. signals_bus.message_received.emit(content)
   ↓
8. UI 显示
```

---

## 📊 架构优势

### 简洁性
- ✅ 删除了所有复杂的协议管理器
- ✅ 删除了所有消息处理器注册逻辑
- ✅ 三层配置结构清晰易懂

### 灵活性
- ✅ 支持多种协议（maim/openai/gemini）
- ✅ 支持多任务类型（chat/vision/tool）
- ✅ 支持模型自动切换

### 可维护性
- ✅ 每个组件职责单一
- ✅ 接口清晰
- ✅ 易于扩展

---

## 🎯 使用场景

### 场景 1：普通对话

```python
chat_client = ChatClient()
await chat_client.initialize('chat')
await chat_client.send_message('你好')
```

### 场景 2：图片识别

```python
chat_client = ChatClient()
await chat_client.initialize('image_recognition')
await chat_client.send_message('描述这张图片', image_data)
```

### 场景 3：切换模型

```python
# 切换到不同的任务
await chat_client.switch_task('tool_use')
```

---

## 📝 配置示例

### model_config.toml

```toml
# 供应商配置
[[api_providers]]
name = "Maim-Local"
base_url = "ws://127.0.0.1:8000/ws"
client_type = "maim"

# 模型配置
[[models]]
model_identifier = "maim-default"
name = "maim-local"
api_provider = "Maim-Local"

# 任务配置
[model_task_config.chat]
model_list = ["maim-local", "deepseek-chat"]
temperature = 0.7
max_tokens = 800
```

---

## ✅ 完成状态

| 组件 | 状态 | 文件 |
|------|------|------|
| 配置模式 | ✅ 完成 | config/schema.py |
| 模型管理器 | ✅ 完成 | src/core/model_manager.py |
| 协议客户端 | ✅ 完成 | src/core/protocol_client.py |
| 聊天客户端 | ✅ 完成 | src/core/chat_client.py |
| 文档 | ✅ 完成 | 本文档 |

---

**架构重构完成！** 简洁、灵活、易维护。🎉