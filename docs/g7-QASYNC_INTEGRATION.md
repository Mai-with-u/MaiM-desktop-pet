# qasync 集成说明

## 概述

本项目已成功集成 `qasync` 库，解决了 PyQt5 与 asyncio 事件循环冲突的问题。

## 问题背景

在集成 `qasync` 之前，项目存在以下问题：

1. **事件循环冲突**：PyQt5 使用自己的事件循环，而 asyncio 也有自己的事件循环
2. **嵌套事件循环问题**：在 PyQt 的信号处理函数中调用 `asyncio.run()` 会创建新的事件循环
3. **任务取消错误**：关闭时出现 "attached to a different loop" 错误
4. **资源清理失败**：MaimProtocol 的清理函数没有被正确调用

## 解决方案：qasync

### 什么是 qasync？

`qasync` 是一个专门为 PyQt/PySide 和 asyncio 集成而设计的库，它提供了一个 `QEventLoop` 类，将 Qt 的事件循环适配为 asyncio 事件循环。

### 主要优势

1. **统一事件循环**：Qt 和 asyncio 共享同一个事件循环
2. **无需嵌套循环**：不再需要在 Qt 回调中创建新的事件循环
3. **优雅的任务管理**：可以使用 `asyncio.create_task()` 在主循环中创建任务
4. **正确的资源清理**：所有异步资源都能被正确清理

## 代码变更

### 1. 依赖添加 (requirements.txt)

```python
# PyQt 与 asyncio 集成
qasync==0.24.0
```

### 2. 主程序改造 (main.py)

**改造前：**
```python
app = QApplication(sys.argv)

asyncio.run(initialize_database())
asyncio.run(initialize_chat_manager())

thread_manager.start_all()
thread_manager.print_status()

from src.frontend.presentation.pet import desktop_pet
desktop_pet.show()
sys.exit(app.exec_())
```

**改造后：**
```python
async def main():
    """主函数 - 使用 qasync 事件循环"""
    from src.util.logger import logger
    from src.frontend.presentation.pet import desktop_pet
    
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    
    # 设置 qasync 事件循环
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 初始化后台服务
    await setup_backend_services()
    
    # 创建并显示桌面宠物
    desktop_pet.show()
    
    # 启动事件循环
    with loop:
        await loop.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序正在退出...")
        sys.exit(0)
```

### 3. 异步任务调用改造 (pet.py)

**改造前：**
```python
def handle_user_input(self, text):
    logger.info(f"收到用户输入: {text}")
    self.show_message(text=text, msg_type="sent")
    
    # 使用 asyncio.run 创建新的事件循环
    asyncio.run(chat_manager.send_text(
        str(text),
        additional_config={
            "maimcore_reply_probability_gain": 1
        }
    ))
```

**改造后：**
```python
def handle_user_input(self, text):
    logger.info(f"收到用户输入: {text}")
    self.show_message(text=text, msg_type="sent")
    
    # 使用 qasync 事件循环，创建异步任务而不阻塞主线程
    asyncio.create_task(chat_manager.send_text(
        str(text),
        additional_config={
            "maimcore_reply_probability_gain": 1
        }
    ))
```

## 核心改进点

### 1. 统一事件循环

```python
# 创建 qasync 事件循环
loop = qasync.QEventLoop(app)
asyncio.set_event_loop(loop)
```

这样设置后：
- Qt 事件循环和 asyncio 事件循环是同一个
- 可以在 Qt 回调中直接使用 `asyncio.create_task()`
- 不再需要创建嵌套的事件循环

### 2. 使用 asyncio.create_task()

```python
# 在 Qt 信号处理函数中直接创建异步任务
def some_qt_callback(self):
    # 直接使用 asyncio.create_task()，不需要 asyncio.run()
    asyncio.create_task(some_async_function())
```

### 3. 优雅的资源清理

由于不再有嵌套的事件循环，资源清理变得更加简单：

```python
async def cleanup_all(self):
    """执行所有清理操作"""
    # 执行所有清理函数
    for cleanup_func in self._cleanup_functions:
        try:
            if asyncio.iscoroutinefunction(cleanup_func):
                await cleanup_func()
            else:
                cleanup_func()
        except Exception as e:
            logger.error(f"清理函数执行失败: {e}", exc_info=True)
```

## 迁移指南

### 对于开发者

1. **安装依赖**
   ```bash
   pip install qasync==0.24.0
   ```

2. **修改异步调用**
   - 将所有 `asyncio.run()` 调用改为 `asyncio.create_task()`
   - 将所有 `await` 调用放在异步函数中

3. **测试验证**
   - 确保所有异步功能正常工作
   - 验证退出时资源被正确清理

### 代码示例对比

#### 场景 1：在 Qt 回调中调用异步函数

**错误做法（改造前）：**
```python
def on_button_clicked(self):
    # ❌ 创建新的事件循环，可能导致冲突
    asyncio.run(async_function())
```

**正确做法（改造后）：**
```python
def on_button_clicked(self):
    # ✅ 在主循环中创建任务
    asyncio.create_task(async_function())
```

#### 场景 2：等待异步结果

**改造前：**
```python
def get_result(self):
    # ❌ 阻塞等待，可能冻结 UI
    result = asyncio.run(get_async_result())
    return result
```

**改造后：**
```python
async def get_result(self):
    # ✅ 正确的异步等待
    result = await get_async_result()
    return result

# 在 Qt 回调中
def on_button_clicked(self):
    asyncio.create_task(self.get_result_and_display())

async def get_result_and_display(self):
    result = await get_async_result()
    self.display_result(result)
```

## 注意事项

1. **不要在 Qt 回调中使用 await**
   - Qt 信号处理函数是同步的
   - 使用 `asyncio.create_task()` 将异步任务放到后台执行

2. **避免长时间运行的同步操作**
   - 长时间同步操作会阻塞 Qt 事件循环
   - 将这些操作包装成异步函数

3. **任务错误处理**
   ```python
   task = asyncio.create_task(some_async_function())
   task.add_done_callback(lambda t: handle_exception(t.exception()))
   ```

4. **资源清理**
   - 确保所有异步资源在退出时被正确清理
   - 使用线程管理器统一管理清理函数

## 相关文件

- `main.py` - 主程序入口，使用 qasync 事件循环
- `requirements.txt` - 项目依赖
- `src/frontend/presentation/pet.py` - 使用 `asyncio.create_task()` 的示例
- `src/core/thread_manager.py` - 线程和资源管理
- `src/core/protocols/maim_protocol.py` - 异步协议实现

## 参考资料

- [qasync GitHub](https://github.com/CabbageDevelopment/qasync)
- [PyQt5 官方文档](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Python asyncio 官方文档](https://docs.python.org/3/library/asyncio.html)

## 总结

通过集成 `qasync`，项目成功解决了 PyQt5 与 asyncio 的事件循环冲突问题。现在：

✅ 统一的事件循环  
✅ 无需嵌套事件循环  
✅ 正确的资源清理  
✅ 更优雅的异步代码  

这将使项目更加稳定和易于维护。