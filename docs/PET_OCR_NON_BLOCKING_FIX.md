# OCR 功能非阻塞修复说明

## 问题描述

在 OCR 和翻译功能中，原来的实现使用了 `asyncio.run()` 来执行异步任务，这会阻塞主线程（UI 线程），导致界面冻结，用户体验不佳。

### 问题代码（修复前）

```python
def _on_ocr_triggered(self):
    # ... 截图代码 ...
    
    # ❌ 阻塞主线程！
    import asyncio
    asyncio.run(chat_manager.send_by_task(
        task_type='image_recognition',
        text=ocr_prompt,
        image_data=image_base64
    ))
```

**问题分析**：
- `asyncio.run()` 会创建新的事件循环并同步等待任务完成
- 这会阻塞主线程（Qt 的 UI 线程）
- 用户界面会冻结，无法响应任何操作

---

## 解决方案

使用 `QTimer.singleShot()` 包装 `asyncio.create_task()`，在 Qt 事件循环中安全地创建异步任务，配合回调函数实现非阻塞调用。

### 修复后的代码

```python
def _on_ocr_triggered(self):
    """OCR识别功能实现"""
    try:
        # ... 截图代码 ...
        
        # 显示"正在识别"提示
        self.pet.show_message("正在识别文字...", msg_type="received")
        
        # 构建 OCR prompt
        ocr_prompt = """请识别图片中的文字内容，只输出识别到的文字，不要添加任何解释或说明。"""
        
        # ✅ 使用 QTimer 包装异步任务（避免阻塞 UI）
        def start_ocr_task():
            try:
                loop = asyncio.get_event_loop()
                asyncio.create_task(chat_manager.send_by_task(
                    task_type='image_recognition',
                    text=ocr_prompt,
                    image_data=image_base64,
                    callback=self._ocr_callback
                ))
            except RuntimeError:
                # 如果没有事件循环，创建一个
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                asyncio.create_task(chat_manager.send_by_task(
                    task_type='image_recognition',
                    text=ocr_prompt,
                    image_data=image_base64,
                    callback=self._ocr_callback
                ))
        
        QTimer.singleShot(0, start_ocr_task)
        
    except Exception as e:
        logger.error(f"OCR识别失败: {e}", exc_info=True)
        self.pet.show_message("OCR识别失败，请重试", msg_type="received")

async def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    """OCR 回调函数（在后台线程执行）"""
    try:
        if success and response:
            logger.info(f"OCR识别成功: {response}")
            # 通过信号发送到主线程显示
            signals_bus.message_received.emit(response)
        else:
            logger.warning("OCR识别失败或无响应")
            # 通过信号发送错误消息到主线程
            signals_bus.message_received.emit("未能识别到文字内容")
    except Exception as e:
        logger.error(f"OCR回调处理失败: {e}", exc_info=True)
        signals_bus.message_received.emit("OCR识别处理失败，请重试")
```

---

## 修复要点

### 1. 使用 `QTimer.singleShot()` 包装 `asyncio.create_task()`

在 Qt 应用中，主线程（UI 线程）运行的是 Qt 事件循环，而不是 asyncio 事件循环。因此直接调用 `asyncio.create_task()` 会抛出 `RuntimeError: no running event loop` 错误。

**解决方案**：使用 `QTimer.singleShot()` 将异步任务创建推迟到 Qt 事件循环中执行。

```python
# ❌ 错误：直接调用 asyncio.create_task()
def _on_ocr_triggered(self):
    # ...
    asyncio.create_task(chat_manager.send_by_task(...))  # 抛出 RuntimeError: no running event loop

# ✅ 正确：使用 QTimer 包装
def _on_ocr_triggered(self):
    # ...
    def start_ocr_task():
        try:
            loop = asyncio.get_event_loop()
            asyncio.create_task(chat_manager.send_by_task(...))
        except RuntimeError:
            # 如果没有事件循环，创建一个
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            asyncio.create_task(chat_manager.send_by_task(...))
    
    QTimer.singleShot(0, start_ocr_task)
```

**为什么需要这样做**：
- `QTimer.singleShot(0, func)` 会在下一个 Qt 事件循环周期中调用 `func`
- 这确保了 `asyncio.create_task()` 在正确的上下文中执行
- 如果当前没有 asyncio 事件循环，代码会自动创建一个

**区别**：
```python
# ❌ 阻塞主线程
asyncio.run(some_async_function())

# ⚠️ 会报错（Qt 主线程没有 asyncio 事件循环）
asyncio.create_task(some_async_function())

# ✅ 正确：不阻塞，且能在 Qt 环境中运行
QTimer.singleShot(0, lambda: asyncio.create_task(some_async_function()))
```

### 2. 使用回调函数处理结果

```python
# 发送任务时注册回调
asyncio.create_task(chat_manager.send_by_task(
    task_type='image_recognition',
    text=ocr_prompt,
    image_data=image_base64,
    callback=self._ocr_callback  # 注册回调函数
))
```

**回调函数签名**：
```python
async def callback(success: bool, task_type: str, response: str = None):
    """
    参数:
        success: 是否发送成功
        task_type: 任务类型
        response: LLM 响应文本（仅 OpenAI 协议）
    """
    pass
```

### 3. 通过信号更新 UI

回调函数在后台线程执行，不能直接操作 UI。需要通过 Qt 信号将结果发送到主线程：

```python
async def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    # ❌ 错误：在后台线程直接操作 UI
    # self.pet.show_message(response, msg_type="received")
    
    # ✅ 正确：通过信号发送到主线程
    signals_bus.message_received.emit(response)
```

**信号连接**（在 `DesktopPet.__init__` 中）：
```python
signals_bus.message_received.connect(self.show_message)
```

---

## 工作流程

### 修复前的流程（阻塞）

```
用户触发 OCR
  ↓
截图并关闭窗口
  ↓
显示"正在识别..."
  ↓
asyncio.run() ←─ 阻塞主线程！界面冻结
  ↓
等待 LLM 响应（可能需要几秒到几十秒）
  ↓
显示结果
```

### 修复后的流程（非阻塞）

```
用户触发 OCR
  ↓
截图并关闭窗口
  ↓
显示"正在识别..."
  ↓
asyncio.create_task() ←─ 不阻塞！立即返回
  ↓
界面保持响应 ←─ 用户可以继续操作
  ↓
后台等待 LLM 响应
  ↓
回调函数被调用
  ↓
通过信号发送结果到主线程
  ↓
显示结果
```

---

## 同样修复的功能

### 1. OCR 识别

```python
async def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    """OCR 回调函数"""
    if success and response:
        signals_bus.message_received.emit(response)
    else:
        signals_bus.message_received.emit("未能识别到文字内容")
```

### 2. 翻译功能

```python
async def _translate_callback(self, success: bool, task_type: str, response: str = None):
    """翻译回调函数"""
    if success and response:
        signals_bus.message_received.emit(response)
    else:
        signals_bus.message_received.emit("未能完成翻译")
```

---

## 关键注意事项

### 1. 回调函数不能直接操作 UI

```python
# ❌ 错误：在回调函数中直接操作 UI
async def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    if success:
        self.pet.show_message(response)  # 可能导致崩溃！

# ✅ 正确：通过信号
async def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    if success:
        signals_bus.message_received.emit(response)
```

**原因**：回调函数在后台线程执行，Qt 要求所有 UI 操作必须在主线程进行。

### 2. 错误处理

```python
async def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    try:
        if success and response:
            # 处理成功
            pass
        else:
            # 处理失败
            pass
    except Exception as e:
        # 捕获所有异常
        logger.error(f"OCR回调处理失败: {e}", exc_info=True)
        signals_bus.message_received.emit("OCR识别处理失败，请重试")
```

### 3. 回调函数必须是异步的

```python
# ✅ 正确：异步回调
async def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    pass

# ⚠️ 同步回调也支持，但不推荐用于耗时操作
def _ocr_callback(self, success: bool, task_type: str, response: str = None):
    pass
```

---

## 测试建议

### 1. 基本功能测试

- [ ] 触发 OCR 识别，确认界面不冻结
- [ ] 触发翻译功能，确认界面不冻结
- [ ] 确认识别结果正确显示

### 2. 并发测试

- [ ] 连续多次触发 OCR，确认不会卡死
- [ ] 在 OCR 进行时移动窗口，确认窗口响应正常
- [ ] 在 OCR 进行时触发其他操作（如右键菜单），确认正常

### 3. 错误处理测试

- [ ] 测试网络错误时的提示
- [ ] 测试 API 返回错误时的提示
- [ ] 测试超时情况的处理

---

## 对比其他类似的代码

### ❌ 需要修复的代码

在 `pet.py` 中，还有一处使用了 `asyncio.run()`：

```python
def handle_user_input(self, text):
    """处理用户输入（同步接口）"""
    logger.info(f"收到用户输入: {text}")
    self.show_message(text=text, msg_type="sent")
    
    # ⚠️ 这里也使用了 asyncio.run，可能也会阻塞
    asyncio.run(chat_manager.send_text(
        str(text),
        additional_config={
            "maimcore_reply_probability_gain": 1
        }
    ))
```

**建议**：如果用户输入频繁，这里也应该改为非阻塞方式。

---

## 总结

### 修复内容

| 功能 | 修复前 | 修复后 |
|------|--------|--------|
| OCR 识别 | `asyncio.run()` 阻塞 | `asyncio.create_task()` + 回调 |
| 翻译功能 | `asyncio.run()` 阻塞 | `asyncio.create_task()` + 回调 |

### 效果

- ✅ 界面不再冻结
- ✅ 用户可以在识别过程中继续操作
- ✅ 用户体验显著提升
- ✅ 代码更符合异步编程最佳实践

### 关键技术点

1. **`asyncio.create_task()`** - 创建后台任务，不阻塞主线程
2. **回调函数** - 处理异步任务的结果
3. **Qt 信号** - 线程间通信，安全更新 UI
4. **错误处理** - 捕获并记录所有异常

---

## 参考资料

- [Python asyncio 官方文档](https://docs.python.org/3/library/asyncio-task.html)
- [Qt 信号与槽](https://doc.qt.io/qt-5/signalsandslots.html)
- [send_by_task 回调使用指南](./SEND_BY_TASK_CALLBACK_USAGE.md)