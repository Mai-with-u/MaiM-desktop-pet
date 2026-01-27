# send_by_task 回调函数使用指南

## 概述

`send_by_task` 方法现在支持自定义回调函数，可以在消息发送成功或失败后执行自定义逻辑。回调函数是可选的，如果不提供，则使用原来的行为（不执行回调）。

---

## 方法签名

```python
async def send_by_task(
    self,
    task_type: str,
    text: str = None,
    image_data: str = None,
    callback=None,
    **kwargs
) -> bool
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_type` | `str` | 任务类型（'chat', 'image_recognition', 'expression' 等） |
| `text` | `str` | 文本内容（可选） |
| `image_data` | `str` | 图片数据（base64，可选） |
| `callback` | `callable` | 回调函数（可选，默认为 None） |
| `**kwargs` | `dict` | 其他参数（如 user_id, user_nickname 等） |

### 返回值

- 返回 `bool`：是否发送成功

---

## 回调函数签名

### 同步回调

```python
def callback(success: bool, task_type: str, response: str = None):
    """
    同步回调函数
    
    参数:
        success: 是否发送成功
        task_type: 任务类型
        response: LLM 响应文本（仅 OpenAI 协议，可能为 None）
    """
    pass
```

### 异步回调

```python
async def callback(success: bool, task_type: str, response: str = None):
    """
    异步回调函数
    
    参数:
        success: 是否发送成功
        task_type: 任务类型
        response: LLM 响应文本（仅 OpenAI 协议，可能为 None）
    """
    pass
```

**注意**：系统会自动检测回调函数是同步还是异步，并相应地调用。

---

## 使用示例

### 示例 1: 不使用回调（默认行为）

```python
from src.core.chat_manager import chat_manager

# 简单发送，不使用回调
success = await chat_manager.send_by_task(
    task_type='image_recognition',
    image_data='base64_encoded_image_data'
)

if success:
    print("识图任务发送成功")
else:
    print("识图任务发送失败")
```

---

### 示例 2: 使用同步回调

```python
from src.core.chat_manager import chat_manager

def my_callback(success: bool, task_type: str, response: str = None):
    """同步回调函数"""
    if success:
        print(f"✓ 任务 {task_type} 成功")
        if response:
            print(f"  响应内容: {response[:50]}...")
    else:
        print(f"✗ 任务 {task_type} 失败")

# 发送识图任务
success = await chat_manager.send_by_task(
    task_type='image_recognition',
    image_data='base64_encoded_image_data',
    callback=my_callback
)
```

---

### 示例 3: 使用异步回调

```python
from src.core.chat_manager import chat_manager
from PyQt5.QtCore import pyqtSignal, QObject

class CallbackHandler(QObject):
    """回调处理器（使用 Qt 信号）"""
    
    # 定义信号
    task_completed = pyqtSignal(bool, str, str)  # success, task_type, response
    
    async def handle_callback(self, success: bool, task_type: str, response: str = None):
        """异步回调函数"""
        # 可以执行异步操作
        if success and response:
            # 例如：保存到数据库
            await self.save_to_database(task_type, response)
        
        # 发射信号到主线程
        self.task_completed.emit(success, task_type, response)
    
    async def save_to_database(self, task_type: str, response: str):
        """保存到数据库（示例）"""
        # ... 数据库操作 ...
        pass

# 使用
handler = CallbackHandler()
handler.task_completed.connect(lambda s, t, r: print(f"主线程收到: {t}, 成功: {s}"))

success = await chat_manager.send_by_task(
    task_type='image_recognition',
    image_data='base64_encoded_image_data',
    callback=handler.handle_callback
)
```

---

### 示例 4: 在 DesktopPet 中使用（识图结果显示）

```python
from src.core.chat_manager import chat_manager
from src.frontend.signals import signals_bus

async def ocr_callback(success: bool, task_type: str, response: str = None):
    """
    OCR 任务回调函数
    
    将识图结果显示为 OCR 类型气泡（淡黄色）
    """
    if success and response:
        print(f"识图成功: {response}")
        # 发射信号到主线程显示
        signals_bus.message_received.emit(response)  # 暂时使用普通消息类型
    else:
        print("识图失败")

# 在 DesktopPet 的识图方法中
async def perform_ocr(self, image_data: str):
    """执行 OCR 识图"""
    success = await chat_manager.send_by_task(
        task_type='image_recognition',
        image_data=image_data,
        callback=ocr_callback
    )
    
    return success
```

---

### 示例 5: 自定义错误处理

```python
from src.core.chat_manager import chat_manager
from src.util.logger import logger

def robust_callback(success: bool, task_type: str, response: str = None):
    """
    带错误处理的回调函数
    """
    try:
        if success:
            logger.info(f"任务 {task_type} 完成")
            
            # 根据任务类型处理响应
            if task_type == 'image_recognition':
                # 识图任务：显示结果
                print(f"识图结果: {response}")
            elif task_type == 'expression':
                # 表情生成任务：使用表情
                print(f"生成表情: {response}")
            elif task_type == 'chat':
                # 聊天任务：显示回复
                print(f"回复: {response}")
        else:
            logger.warning(f"任务 {task_type} 失败，重试...")
            # 可以添加重试逻辑
    except Exception as e:
        logger.error(f"回调执行出错: {e}", exc_info=True)

# 使用
await chat_manager.send_by_task(
    task_type='chat',
    text='你好',
    callback=robust_callback
)
```

---

### 示例 6: 批量发送并收集结果

```python
from src.core.chat_manager import chat_manager

class ResultCollector:
    """结果收集器"""
    
    def __init__(self):
        self.results = []
        self.completed_count = 0
        self.total_count = 0
    
    def create_callback(self, task_id: str):
        """为每个任务创建回调"""
        def callback(success: bool, task_type: str, response: str = None):
            self.results.append({
                'task_id': task_id,
                'success': success,
                'task_type': task_type,
                'response': response
            })
            self.completed_count += 1
            print(f"任务 {task_id} 完成: {success}")
        return callback
    
    async def wait_all(self):
        """等待所有任务完成"""
        while self.completed_count < self.total_count:
            await asyncio.sleep(0.1)

# 使用
async def batch_ocr(image_list):
    """批量识图"""
    collector = ResultCollector()
    collector.total_count = len(image_list)
    
    # 发送所有任务
    for i, image_data in enumerate(image_list):
        await chat_manager.send_by_task(
            task_type='image_recognition',
            image_data=image_data,
            callback=collector.create_callback(f"task_{i}")
        )
    
    # 等待所有任务完成
    await collector.wait_all()
    
    # 输出结果
    for result in collector.results:
        if result['success']:
            print(f"{result['task_id']}: {result['response']}")
    
    return collector.results
```

---

## 回调参数详解

### success (bool)

- `True`: 消息发送成功
- `False`: 消息发送失败

### task_type (str)

任务类型字符串，如：
- `'chat'`: 聊天任务
- `'image_recognition'`: 识图任务
- `'expression'`: 表情生成任务
- 其他自定义任务类型

### response (str | None)

- **OpenAI 协议**: LLM 的响应文本（可能是识图结果、聊天回复等）
- **Maim 协议**: 通常为 `None`（因为响应是通过其他方式返回的）

**注意**: 响应文本可能为 `None`，使用前需要检查。

---

## 注意事项

### 1. 回调函数的异常处理

回调函数中的异常会被捕获并记录日志，不会影响主流程：

```python
def safe_callback(success: bool, task_type: str, response: str = None):
    try:
        # 回调逻辑
        pass
    except Exception as e:
        # 记录错误
        print(f"回调出错: {e}")
        raise
```

系统会自动捕获并记录回调中的异常：

```python
# 在 send_by_task 中
try:
    if asyncio.iscoroutinefunction(callback):
        await callback(**callback_args)
    else:
        callback(**callback_args)
except Exception as e:
    logger.error(f"回调函数执行失败: {e}", exc_info=True)
```

### 2. 异步回调中不能直接操作 UI

如果需要在异步回调中操作 UI，应该通过 Qt 信号：

```python
from PyQt5.QtCore import QObject, pyqtSignal

class UICallbackHandler(QObject):
    # 定义信号（参数类型必须指定）
    show_result = pyqtSignal(str)
    
    async def callback(self, success: bool, task_type: str, response: str = None):
        if success and response:
            # 不能直接操作 UI，使用信号
            self.show_result.emit(response)
    
    def on_show_result(self, result: str):
        # 在主线程中操作 UI
        print(f"显示结果: {result}")

# 连接信号和槽
handler = UICallbackHandler()
handler.show_result.connect(handler.on_show_result)

# 使用
await chat_manager.send_by_task(
    task_type='image_recognition',
    image_data='...',
    callback=handler.callback
)
```

### 3. 回调函数的执行时机

回调函数在消息发送**之后**立即执行：

```
发送消息 → 等待响应 → 回调执行
```

对于 OpenAI 协议：
- 回调会在收到 LLM 响应后执行
- `response` 参数包含 LLM 的完整响应

对于 Maim 协议：
- 回调会在消息发送成功后立即执行
- `response` 参数通常为 `None`（因为响应是通过消息处理器异步返回的）

### 4. 回调函数的性能影响

- 同步回调会阻塞当前协程
- 异步回调不会阻塞（使用 `await`）
- 如果回调中有耗时操作，建议使用异步回调

```python
# ✅ 推荐：异步回调
async def async_callback(success: bool, task_type: str, response: str = None):
    if success:
        await save_to_database(response)  # 耗时操作

# ⚠️ 谨慎：同步回调
def sync_callback(success: bool, task_type: str, response: str = None):
    if success:
        save_to_database(response)  # 会阻塞当前协程
```

---

## 高级用法

### 1. 使用 lambda 匿名函数

```python
# 简单的 lambda 回调
await chat_manager.send_by_task(
    task_type='chat',
    text='你好',
    callback=lambda s, t, r: print(f"{'✓' if s else '✗'} {t}: {r}")
)
```

### 2. 使用 functools.partial 绑定参数

```python
from functools import partial

def callback_with_prefix(prefix: str, success: bool, task_type: str, response: str = None):
    print(f"{prefix} - {task_type}: {response}")

# 绑定前缀
callback = partial(callback_with_prefix, "OCR任务")

await chat_manager.send_by_task(
    task_type='image_recognition',
    image_data='...',
    callback=callback
)
```

### 3. 类方法作为回调

```python
class TaskManager:
    def __init__(self):
        self.results = {}
    
    async def handle_task(self, success: bool, task_type: str, response: str = None):
        """类方法作为回调"""
        self.results[task_type] = {
            'success': success,
            'response': response
        }
    
    async def send_ocr(self, image_data: str):
        return await chat_manager.send_by_task(
            task_type='image_recognition',
            image_data=image_data,
            callback=self.handle_task
        )

# 使用
manager = TaskManager()
await manager.send_ocr('base64_image_data')
print(manager.results['image_recognition'])
```

---

## 完整示例：DesktopPet 集成 OCR 回调

```python
from src.core.chat_manager import chat_manager
from src.frontend.signals import signals_bus

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        # ... 初始化代码 ...
        
        # 连接信号
        signals_bus.message_received.connect(self.show_message)
    
    async def perform_ocr(self, pixmap):
        """
        执行 OCR 识图
        
        参数:
            pixmap: QPixmap 对象（要识别的图片）
        """
        try:
            # 转换为 base64
            from src.util.image_util import pixmap_to_base64
            image_data = pixmap_to_base64(pixmap)
            
            # 定义回调函数
            async def ocr_callback(success: bool, task_type: str, response: str = None):
                """OCR 回调函数"""
                if success and response:
                    print(f"识图成功: {response}")
                    # 通过信号显示结果（主线程）
                    signals_bus.message_received.emit(response)
                else:
                    print("识图失败")
            
            # 发送识图任务
            success = await chat_manager.send_by_task(
                task_type='image_recognition',
                image_data=image_data,
                callback=ocr_callback
            )
            
            return success
            
        except Exception as e:
            print(f"OCR 识图出错: {e}")
            return False
    
    def show_message(self, text=None, msg_type="received", pixmap=None):
        """显示消息（槽函数）"""
        # 原有的消息显示逻辑
        self.bubble_manager.show_message(text, msg_type, pixmap)
```

---

## 总结

`send_by_task` 的回调功能提供了灵活的消息处理方式：

✅ **可选**: 不提供回调时保持原有行为  
✅ **灵活**: 支持同步和异步回调  
✅ **安全**: 自动捕获回调中的异常  
✅ **易用**: 自动检测回调类型（同步/异步）  
✅ **强大**: 可用于结果处理、UI 更新、错误处理等  

通过合理使用回调函数，可以更好地控制消息发送后的流程，实现更复杂的应用场景。