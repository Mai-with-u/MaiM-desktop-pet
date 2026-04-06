# Maim WebSocket 集成说明

## 概述

本次集成实现了 **Maim 协议的 WebSocket 长连接**，使用 `maim_message` 库的 `Router` 组件管理 WebSocket 连接。

---

## 集成架构

### 1. 核心组件

- **`maim_message.Router`** - WebSocket 路由管理器
  - 管理多个 WebSocket 连接
  - 提供消息发送/接收接口
  - 自动处理连接维护

- **`ChatManager`** - 聊天管理器
  - 根据协议类型选择 HTTP 或 WebSocket
  - 集成 Router 进行 WebSocket 通信
  - 注册消息处理器接收回复

---

## 实现细节

### 初始化流程（Maim 协议）

```python
# 1. 创建 Router 配置
target_config = TargetConfig(
    url=ws_url,           # WebSocket 地址
    token=api_key         # 认证令牌（可选）
)
route_config = RouteConfig(
    route_config={platform: target_config}
)

# 2. 创建 Router 实例
router = Router(config=route_config, custom_logger=logger)

# 3. 注册消息处理器
router.register_message_handler(handle_maim_message)

# 4. 连接到服务器
await router.connect(platform)
```

---

### 消息发送流程

```python
# 1. 构建 UserInfo
user_info = UserInfo(
    platform='desktop-pet',
    user_id=user_id,
    user_nickname=user_name,
    user_cardname=''
)

# 2. 构建 FormatInfo
format_info = FormatInfo(
    content_format=['text'],
    accept_format=['text']
)

# 3. 构建 BaseMessageInfo
message_info = BaseMessageInfo(
    platform='desktop-pet',
    message_id='',
    time=0.0,
    user_info=user_info,
    format_info=format_info,
    additional_config={
        "maimcore_reply_probability_gain": 1
    }
)

# 4. 构建 Seg（消息内容）
seg = Seg(type='text', data=content)

# 5. 构建 MessageBase
message = MessageBase(
    message_info=message_info,
    message_segment=seg,
    raw_message=content
)

# 6. 发送消息
await router.send_message(message)
```

---

### 消息接收流程

```python
def _handle_maim_message(message: MessageBase):
    """处理从 WebSocket 接收到的消息"""
    # 1. 提取回复内容
    reply_content = message.message_segment.data
    
    # 2. 触发 UI 信号
    signals_bus.message_received.emit(reply_content)
```

---

### 清理流程

```python
async def cleanup():
    """清理 WebSocket 连接"""
    if router:
        await router.stop()
        router = None
```

---

## 配置说明

### model_config.toml

```toml
# Maim 协议提供商配置
[[api_providers]]
name = "Maim-Local"
base_url = "ws://127.0.0.1:8000/ws"  # WebSocket 地址
client_type = "maim"                 # 协议类型
api_key = ""                         # 认证令牌（可选）

# Maim 模型配置
[[models]]
model_identifier = "maim-default"
name = "maim-local"
api_provider = "Maim-Local"

# 任务配置（使用 Maim 模型）
[model_task_config.chat]
model_list = ["maim-local", "deepseek-chat"]
```

### config.toml

```toml
# 平台标识（用于 WebSocket 连接）
platform = "desktop-pet"
```

---

## 关键特性

### 1. **长连接管理**

- ✅ Router 自动维护 WebSocket 连接
- ✅ 支持断线重连（Router 内置）
- ✅ 连接状态检查

### 2. **消息格式标准化**

- ✅ 使用 `MessageBase` 标准格式
- ✅ 包含完整的消息元数据（UserInfo、FormatInfo 等）
- ✅ 支持 `additional_config` 扩展字段

### 3. **协议切换灵活性**

- ✅ HTTP 协议：临时创建 session，按需请求
- ✅ WebSocket 协议：长连接，实时双向通信
- ✅ 通过 `protocol_type` 自动选择通信方式

### 4. **错误处理**

- ✅ `MAIM_MESSAGE_AVAILABLE` 检查库是否安装
- ✅ 连接失败时返回 False，不阻塞其他协议
- ✅ 消息处理器异常捕获

---

## 使用示例

### 场景 1：连接到本地 Maim 服务

```python
# 配置 WebSocket 地址
base_url = "ws://127.0.0.1:19000/ws"

# 初始化聊天管理器
await chat_manager.initialize(task_type='chat')

# 发送消息（自动使用 WebSocket）
await chat_manager.send_message("你好", user_id='0', user_name='麦麦')
```

### 场景 2：协议切换

```python
# model_config.toml 配置多个模型
[model_task_config.chat]
model_list = ["maim-local", "gpt-4o-mini", "deepseek-chat"]

# 优先使用 Maim WebSocket，失败时自动切换到 HTTP API
# protocol_manager 会按顺序尝试
```

---

## 与 HTTP 协议对比

| 特性 | HTTP (OpenAI/Gemini) | WebSocket (Maim) |
|------|---------------------|------------------|
| **连接类型** | 临时 session | 长连接 Router |
| **初始化时机** | 无需初始化 | 启动时连接 |
| **消息格式** | OpenAI JSON | MessageBase |
| **人设管理** | PromptManager | additional_config |
| **响应方式** | 同步等待 | 异步回调 |
| **适用场景** | API 调用 | 实时通信 |

---

## 注意事项

### 1. **maim_message 库依赖**

```bash
# 必须安装 maim_message
pip install maim-message

# 如果未安装，Maim 协议将不可用
# ChatManager 会返回初始化失败
```

### 2. **platform 配置**

```toml
# config.toml 必须配置 platform
platform = "desktop-pet"  # 用于 WebSocket 连接标识

# 如果未配置，默认使用 "desktop-pet"
```

### 3. **WebSocket 地址格式**

```toml
# 必须是 WebSocket URL
base_url = "ws://127.0.0.1:19000/ws"

# ❌ 错误：HTTP URL
# base_url = "http://127.0.0.1:19000"
```

### 4. **消息处理器注册时机**

```python
# 必须在 connect() 之前注册
router.register_message_handler(handler)
await router.connect(platform)
```

---

## 故障排查

### 问题 1：连接失败

**症状**：
```
Maim WebSocket 连接初始化失败
```

**排查**：
1. 检查 WebSocket 地址是否正确
2. 检查 maim_message 是否安装：`pip show maim-message`
3. 检查服务端是否运行：访问 WebSocket 地址
4. 查看日志：`logs/pet.log`

---

### 问题 2：收不到回复

**症状**：
- 消息发送成功，但 UI 无响应

**排查**：
1. 检查消息处理器是否注册
2. 检查 `signals_bus.message_received` 是否连接到 UI
3. 检查服务端是否返回消息（查看日志）

---

### 问题 3：maim_message 导入失败

**症状**：
```
maim_message 库未安装，Maim 协议将不可用
```

**解决**：
```bash
pip install maim-message
```

---

## 未来扩展

### 1. **从配置文件读取人设**

```python
# 在 PromptManager 中支持从 model_config.toml 读取
[prompt.system]
content = "你是麦麦..."

# ChatManager 根据协议类型选择人设
# Maim: 通过 additional_config
# HTTP: 通过 PromptManager
```

### 2. **多 WebSocket 连接**

```python
# Router 支持多个平台连接
route_config = {
    'desktop-pet': TargetConfig(...),
    'mobile-app': TargetConfig(...),
}

# 同时连接多个 WebSocket
await router.run()  # 自动连接所有平台
```

### 3. **WebSocket 连接状态监控**

```python
# 添加连接状态检查方法
def is_websocket_connected(self) -> bool:
    if not self._maim_router:
        return False
    return self._maim_router.check_connection(self._maim_platform)
```

---

## 相关文件

- **核心实现**：`src/core/chat/manager.py`
- **协议管理**：`src/core/protocol/manager.py`
- **配置模板**：`model_config.toml`
- **依赖库**：`maim_message (>= 0.6.8)`

---

## 总结

本次集成成功实现了：

✅ **Maim WebSocket 长连接** - 使用 Router 管理连接
✅ **消息格式标准化** - MessageBase 统一格式
✅ **协议灵活切换** - HTTP/WebSocket 双协议支持
✅ **长连接维护** - Router 自动处理断线重连
✅ **消息收发完整** - 发送/接收/清理流程完善

**下一步**：测试实际连接和消息交互功能。