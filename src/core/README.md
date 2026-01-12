# 线程管理器使用指南

## 概述

`ThreadManager` 是一个统一的线程管理器，用于管理应用程序中的所有后台线程和清理函数。

### 核心特性

- **单例模式**：全局唯一的线程管理器实例
- **延迟启动**：支持预先注册线程配置，统一启动
- **立即启动**：支持直接启动线程
- **清理管理**：统一管理所有清理函数
- **状态监控**：提供线程状态查询和打印功能

## 使用方法

### 1. 在模块中注册线程

#### 方法一：延迟注册（推荐）

适合需要在主程序初始化后统一启动的后台服务。

```python
# src/core/my_service.py
from src.core.thread_manager import thread_manager

def register_my_service():
    """向线程管理器注册服务（延迟启动）"""
    thread_manager.register_thread_deferred(
        target=my_service_worker,
        name="MyService",
        daemon=True
    )

async def cleanup_my_service():
    """清理服务资源"""
    logger.info("清理 MyService...")
    # 清理逻辑

def my_service_worker():
    """服务工作线程"""
    import asyncio
    
    # 注册清理函数
    thread_manager.register_cleanup(cleanup_my_service)
    
    # 运行异步服务
    asyncio.run(run_service_async())

async def run_service_async():
    """异步运行服务"""
    # 服务逻辑
    await asyncio.Event().wait()  # 保持运行
```

在 `main.py` 中注册并启动：

```python
# main.py
from src.core.my_service import register_my_service

if __name__ == "__main__":
    # 初始化数据库
    asyncio.run(initialize_database())
    
    # 注册所有后台服务
    register_my_service()
    # ... 注册其他服务
    
    # 统一启动所有延迟注册的线程
    thread_manager.start_all()
    
    # 启动主窗口
    chat_pet.show()
    sys.exit(app.exec_())
```

#### 方法二：立即启动

适合需要立即启动的线程（通常不建议在模块级别使用）。

```python
from src.core.thread_manager import thread_manager

# 直接启动线程
thread_manager.register_thread(
    target=my_function,
    name="MyThread",
    daemon=True
)
```

### 2. 注册清理函数

清理函数可以是同步或异步函数：

```python
async def cleanup_async():
    """异步清理函数"""
    logger.info("正在清理资源...")
    await async_cleanup_operation()
    logger.info("资源清理完成")

def cleanup_sync():
    """同步清理函数"""
    logger.info("正在清理资源...")
    sync_cleanup_operation()
    logger.info("资源清理完成")

# 注册清理函数
thread_manager.register_cleanup(cleanup_async)
thread_manager.register_cleanup(cleanup_sync)
```

### 3. 查询线程状态

```python
# 获取线程信息列表
thread_info = thread_manager.get_thread_info()
for info in thread_info:
    print(f"{info['name']}: {'运行中' if info['alive'] else '已停止'}")

# 打印详细状态
thread_manager.print_status()
```

### 4. 手动清理

```python
import asyncio

# 执行所有清理操作
asyncio.run(thread_manager.cleanup_all())
```

## 完整示例

### 示例 1：创建一个新的后台服务

```python
# src/core/weather_service.py
import asyncio
from src.core.thread_manager import thread_manager
from src.util.logger import logger

class WeatherService:
    """天气服务示例"""
    
    @staticmethod
    def register():
        """注册天气服务"""
        thread_manager.register_thread_deferred(
            target=lambda: asyncio.run(WeatherService.run()),
            name="WeatherService",
            daemon=True
        )
        logger.info("天气服务已注册")
    
    @staticmethod
    async def cleanup():
        """清理天气服务"""
        logger.info("清理天气服务...")
        # 清理逻辑
    
    @staticmethod
    async def run():
        """运行天气服务"""
        # 注册清理函数
        thread_manager.register_cleanup(WeatherService.cleanup)
        
        try:
            while True:
                # 定期获取天气数据
                weather = await WeatherService.fetch_weather()
                logger.info(f"当前天气: {weather}")
                
                # 等待 10 分钟
                await asyncio.sleep(600)
        except asyncio.CancelledError:
            logger.info("天气服务已取消")
    
    @staticmethod
    async def fetch_weather():
        """获取天气数据（示例）"""
        # 实际实现中，这里会调用天气 API
        return "晴，25°C"
```

在 `main.py` 中使用：

```python
# main.py
from src.core.weather_service import WeatherService

if __name__ == "__main__":
    asyncio.run(initialize_database())
    
    # 注册所有后台服务
    from src.core.router import register_router
    register_router()
    
    WeatherService.register()
    
    # 启动所有服务
    thread_manager.start_all()
    
    # 启动主窗口
    chat_pet.show()
    sys.exit(app.exec_())
```

## 设计原则

### 1. 模块自注册

每个模块负责自己的线程注册，主程序只需调用注册函数。

**优点：**
- 解耦：主程序不需要知道具体实现
- 灵活：可以按需启用/禁用服务
- 清晰：每个模块的职责明确

### 2. 延迟启动

先注册，后启动。

**优点：**
- 确保初始化顺序正确
- 便于调试和监控
- 可以统一管理启动时机

### 3. 统一清理

所有清理函数通过线程管理器统一管理。

**优点：**
- 避免资源泄漏
- 简化退出逻辑
- 保证清理顺序

## 线程类型

### 守护线程 (daemon=True)

- 主程序退出时自动终止
- 不影响程序退出
- 适合：后台监控、定期任务等

### 非守护线程 (daemon=False)

- 主程序需要等待其结束
- 可能阻塞程序退出
- 适合：重要任务、需要完整执行的任务

## 清理时机

清理操作会在以下时机执行：

1. **正常退出**：通过托盘菜单或快捷键退出
2. **异常捕获**：程序捕获到退出信号
3. **手动触发**：调用 `thread_manager.cleanup_all()`

**注意：** 如果进程被强制终止（如 `taskkill /F`），清理函数不会被执行。

## 常见问题

### Q1: 如何调试线程启动失败？

```python
# 检查线程配置
print(f"已注册 {len(thread_manager._thread_configs)} 个线程")

# 检查线程状态
thread_manager.print_status()

# 查看详细日志
logger.setLevel(logging.DEBUG)
```

### Q2: 如何禁用某个服务？

只需在 `main.py` 中不调用其注册函数：

```python
# 注释掉这行即可禁用 MaimRouter
# from src.core.router import register_router
# register_router()
```

### Q3: 如何在运行时动态添加线程？

使用 `register_thread()` 方法（立即启动）：

```python
thread_manager.register_thread(
    target=my_function,
    name="DynamicThread",
    daemon=True
)
```

### Q4: 清理函数执行顺序？

清理函数按照注册顺序的**相反顺序**执行（后进先出）。

## 最佳实践

1. **命名规范**：线程名称应清晰描述其用途
   ```python
   name="WeatherService"  # ✅ 好
   name="Thread-1"       # ❌ 差
   ```

2. **异常处理**：所有线程函数都应该有异常处理
   ```python
   async def my_service():
       try:
           # 服务逻辑
       except Exception as e:
           logger.error(f"服务异常: {e}", exc_info=True)
   ```

3. **资源清理**：确保所有资源都能被正确清理
   ```python
   async def cleanup():
       # 清理数据库连接
       await db.close()
       # 清理文件句柄
       file.close()
       # 清理网络连接
       await session.close()
   ```

4. **日志记录**：重要操作都应该记录日志
   ```python
   logger.info("服务已启动")
   logger.info("正在处理任务...")
   logger.info("任务完成")
   logger.info("服务已停止")
   ```

## 现有服务

### MaimRouter

负责与 Maim 服务的通信。

```python
from src.core.router import register_router
register_router()
```

### 桌面宠物

主窗口本身不是线程，但管理着多个工作线程（如 MoveWorker）。

## 参考资源

- [Python 线程文档](https://docs.python.org/zh-cn/3/library/threading.html)
- [asyncio 文档](https://docs.python.org/zh-cn/3/library/asyncio.html)
- [PyQt5 线程文档](https://doc.qt.io/qt-5/qthread.html)
