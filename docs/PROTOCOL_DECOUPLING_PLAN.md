# 协议层解耦方案

**目标**: 将 Maim (WebSocket) 和 OpenAI (HTTP API) 完全解耦，每个协议独立处理自己的消息流

---

## 🔍 当前架构的问题

### 问题 1：全局消息处理器

```python
# router.py - 全局处理器
async def message_handler(message):
    # 处理所有协议的消息
    signals_bus.message_received.emit(message_content)

# 需要注册到协议管理器
protocol_manager.register_message_handler(message_handler)
```

**问题**：
- ❌ 注册时机复杂（需要在协议连接后注册）
- ❌ 不同协议的消息流不同，但用同一个处理器
- ❌ Maim 需要接收推送，OpenAI 是请求-响应，强行统一

### 问题 2：初始化顺序依赖

```
1. chat_manager.initialize()
   ↓
2. protocol_manager.initialize_from_model_config()
   ↓
3. protocol.connect()  ← WebSocket 连接
   ↓
4. register_message_handler()  ← 注册太晚了！
   ↓
5. 问题：消息处理器未生效
```

### 问题 3：协议差异被忽略

| 协议 | 通信方式 | 消息流 | 特点 |
|------|---------|--------|------|
| **Maim** | WebSocket | 服务器推送 | 长连接，实时消息 |
| **OpenAI** | HTTP API | 请求-响应 | 无状态，按需请求 |

**强行统一导致**：
- OpenAI 的响应也需要通过 message_handler（没必要）
- Maim 的消息处理器注册时机复杂

---

## ✅ 解耦方案

### 方案概述

**核心思想**：每个协议独立处理自己的消息，直接触发 UI 信号

```
Maim 协议：
├── WebSocket 连接
├── 接收服务器推送
└── 直接触发 signals_bus.message_received ✅

OpenAI 协议：
├── HTTP API 调用
├── 接收响应
└── 直接触发 signals_bus.message_received ✅

移除：
├── router.py 的 message_handler ❌
├── protocol_manager.register_message_handler() ❌
└── 统一的消息处理器注册流程 ❌
```

---

## 📝 具体实现

### 1. Maim 协议改造

**当前**：
```python
# maim_protocol.py
def register_message_handler(self, handler: Callable):
    self._message_handler = self._create_message_handler_wrapper(handler)

async def connect(self):
    if self._message_handler:
        self._router.register_class_handler(self._message_handler)
```

**解耦后**：
```python
# maim_protocol.py
async def connect(self):
    # ✅ 直接在协议内部注册处理器，不需要外部传入
    self._router.register_class_handler(self._handle_incoming_message)

async def _handle_incoming_message(self, message):
    """
    处理接收到的 WebSocket 消息
    """
    try:
        # 1. 格式转换
        converted_message = self._convert_message_format(message)
        
        # 2. 保存到数据库
        if db_manager.is_initialized():
            await db_manager.save_message(converted_message)
        
        # 3. 直接触发 UI 信号
        message_segment = converted_message.get('message_segment', {})
        if message_segment.get('type') == 'text':
            from src.frontend.signals import signals_bus
            signals_bus.message_received.emit(str(message_segment.get('data', '')))
            
    except Exception as e:
        logger.error(f"处理接收消息失败: {e}", exc_info=True)
```

**优势**：
- ✅ 不需要外部注册消息处理器
- ✅ 协议连接时自动注册
- ✅ 消息处理逻辑封装在协议内部

---

### 2. OpenAI 协议改造

**当前**：
```python
# openai_protocol.py
async def send_message(self, message: Dict[str, Any]) -> bool:
    # 发送请求
    response = await self._send_chat_request(text)
    
    # 返回成功
    return True
    # ❌ 响应内容没有显示！需要通过 message_handler
```

**解耦后**：
```python
# openai_protocol.py
async def send_message(self, message: Dict[str, Any]) -> bool:
    try:
        # 发送请求
        response = await self._send_chat_request(text)
        
        # ✅ 直接处理响应，触发 UI 信号
        if response:
            await self._handle_response(response)
            return True
        
    except Exception as e:
        logger.error(f"发送消息失败: {e}", exc_info=True)
        return False

async def _handle_response(self, response: Dict[str, Any]):
    """
    处理 OpenAI API 响应
    """
    try:
        # 1. 提取响应内容
        content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        if not content:
            logger.warning("OpenAI 响应为空")
            return
        
        # 2. 构建消息对象
        message_data = {
            'message_info': {
                'platform': 'openai',
                'message_id': str(uuid.uuid4()),
                'time': time.time(),
                'user_info': {
                    'platform': 'openai',
                    'user_id': 'assistant',
                    'user_nickname': 'AI Assistant',
                }
            },
            'message_segment': {
                'type': 'text',
                'data': content,
            },
            'raw_message': content,
        }
        
        # 3. 保存到数据库
        if db_manager.is_initialized():
            await db_manager.save_message(message_data)
        
        # 4. 直接触发 UI 信号
        from src.frontend.signals import signals_bus
        signals_bus.message_received.emit(content)
        
        logger.info(f"OpenAI 响应: {content[:50]}...")
        
    except Exception as e:
        logger.error(f"处理 OpenAI 响应失败: {e}", exc_info=True)
```

**优势**：
- ✅ 响应直接处理，不需要通过 message_handler
- ✅ 符合 HTTP 请求-响应模型
- ✅ 流程清晰，易于理解

---

### 3. 移除不必要的代码

#### 删除 router.py 的 message_handler

**之前**：
```python
# router.py
async def message_handler(message):
    # 保存数据库
    await db_manager.save_message(message)
    # 触发信号
    signals_bus.message_received.emit(message_content)

# 注册到协议管理器
protocol_manager.register_message_handler(message_handler)
```

**之后**：
```python
# router.py
async def run_protocol_manager_async():
    """异步运行协议管理器"""
    thread_manager.register_cleanup(cleanup_router)
    
    # ❌ 删除：不再需要注册消息处理器
    # protocol_manager.register_message_handler(message_handler)
    
    # ✅ 简化：只保持线程运行
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("协议管理器线程被取消")
```

#### 简化 protocol_manager

**之前**：
```python
# protocol_manager.py
def register_message_handler(self, handler):
    self._message_handler = handler
    for protocol in self._protocols.values():
        protocol.register_message_handler(handler)
```

**之后**：
```python
# protocol_manager.py
# ❌ 完全删除 register_message_handler() 方法
# 每个协议自己处理消息
```

---

## 📊 对比总结

| 方面 | 当前架构 | 解耦后 |
|------|---------|--------|
| **消息处理** | 全局 message_handler | 每个协议独立处理 |
| **注册时机** | 复杂，容易出错 | 协议连接时自动注册 |
| **协议差异** | 强行统一 | 各自处理，符合特性 |
| **代码复杂度** | 高（router + handler 注册） | 低（协议内部处理） |
| **初始化流程** | 5步，有依赖 | 3步，独立 |
| **可维护性** | 难（耦合严重） | 易（完全解耦） |

---

## 🚀 实施步骤

### 步骤 1：修改 Maim 协议

```bash
# 在 maim_protocol.py 中添加 _handle_incoming_message() 方法
# 在 connect() 中注册自己的处理器
```

### 步骤 2：修改 OpenAI 协议

```bash
# 在 openai_protocol.py 中添加 _handle_response() 方法
# 在 send_message() 中直接调用
```

### 步骤 3：简化 router.py

```bash
# 删除 message_handler() 函数
# 删除 protocol_manager.register_message_handler() 调用
```

### 步骤 4：删除 protocol_manager.register_message_handler()

```bash
# 从 protocol_manager.py 中删除该方法
```

### 步骤 5：测试验证

```bash
python main.py
# 测试 Maim 协议：发送消息，接收推送
# 测试 OpenAI 协议：发送请求，接收响应
```

---

## 🎯 预期效果

### Maim 协议流程

```
[启动]
WebSocket 连接
    ↓
注册 _handle_incoming_message
    ↓
[接收消息]
服务器推送 → _handle_incoming_message
    ↓
保存数据库 + 触发信号
    ↓
UI 显示消息 ✅
```

### OpenAI 协议流程

```
[发送消息]
用户输入 → send_message
    ↓
HTTP 请求 → API 响应
    ↓
_handle_response
    ↓
保存数据库 + 触发信号
    ↓
UI 显示消息 ✅
```

---

## ✅ 总结

**优势**：
- ✅ 完全解耦，各协议独立
- ✅ 简化初始化流程
- ✅ 符合协议特性（WebSocket vs HTTP）
- ✅ 减少代码复杂度
- ✅ 易于维护和扩展

**需要修改的文件**：
1. `src/core/protocols/maim_protocol.py` - 添加内部消息处理
2. `src/core/protocols/openai_protocol.py` - 添加响应处理
3. `src/core/router.py` - 删除 message_handler
4. `src/core/protocol_manager.py` - 删除 register_message_handler()

**不需要修改**：
- `src/frontend/signals.py` - 信号总线保持不变
- `src/frontend/presentation/pet.py` - UI 连接保持不变
- `config/` - 配置文件保持不变

---

**解耦方案完成！** 架构更清晰，维护更简单。🎉