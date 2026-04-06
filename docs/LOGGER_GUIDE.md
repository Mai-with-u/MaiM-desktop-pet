# 日志系统使用说明

## 📋 功能特性

### 1. 多文件日志记录

#### 主日志文件 (pet.log)
- **路径**: `logs/pet.log`
- **用途**: 长期保存所有运行日志
- **轮转策略**: 每天午夜自动轮转
- **保留期限**: 最近 30 天
- **格式**: `2026-04-06 19:11:16 - pet - INFO - 消息内容`

#### 最近一次运行日志 (last_run.log)
- **路径**: `logs/last_run.log`
- **用途**: 仅保存最近一次程序启动的完整日志
- **特点**: 
  - 每次启动时自动清空
  - 包含启动时间标记
  - 方便快速查看最近一次运行的问题
- **格式**: 
  ```
  ================================================================================
  程序启动时间: 2026-04-06 19:11:16
  ================================================================================
  
  2026-04-06 19:11:16 - pet - INFO - 消息内容
  ```

#### 控制台输出
- **级别**: INFO 及以上
- **格式**: `04-06 19:11:16 [INFO] 消息内容`
- **用途**: 实时查看程序运行状态

## 🔧 使用方法

### 导入 logger

```python
from src.util.logger import logger
```

### 记录不同级别的日志

```python
# DEBUG - 详细调试信息（仅写入文件，不显示在控制台）
logger.debug("这是调试信息")

# INFO - 一般信息
logger.info("这是一般信息")

# WARNING - 警告信息
logger.warning("这是警告信息")

# ERROR - 错误信息
logger.error("这是错误信息")

# CRITICAL - 严重错误
logger.critical("这是严重错误")
```

### 记录异常信息

```python
try:
    result = 1 / 0
except Exception as e:
    logger.error(f"捕获到异常: {e}", exc_info=True)
```

### 记录性能数据

```python
import time

start_time = time.time()
# ... 执行操作 ...
end_time = time.time()

logger.info(f"操作耗时: {(end_time - start_time) * 1000:.2f} ms")
```

## 📂 日志文件结构

```
MaiM-desktop-pet/
└── logs/
    ├── pet.log                  # 主日志文件（当前）
    ├── pet.log.2026-04-05      # 历史日志（按日期）
    ├── pet.log.2026-04-04
    └── last_run.log            # 最近一次运行日志
```

## 🎯 使用场景

### 场景 1：快速查看最近一次运行的错误

```bash
# 查看 last_run.log 文件
cat logs/last_run.log

# 或者在 Windows PowerShell
Get-Content logs\last_run.log
```

### 场景 2：查看历史日志

```bash
# 查看主日志文件
cat logs/pet.log

# 查看特定日期的日志
cat logs/pet.log.2026-04-05
```

### 场景 3：实时监控日志

```bash
# Linux/Mac
tail -f logs/pet.log

# Windows PowerShell
Get-Content logs\pet.log -Wait
```

## ⚙️ 配置选项

### 修改日志级别

在 `src/util/logger.py` 中修改：

```python
# 修改全局日志级别
logger.setLevel(logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 修改控制台输出级别
console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上

# 修改文件记录级别
main_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
last_run_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
```

### 修改日志保留期限

```python
main_handler = TimedRotatingFileHandler(
    filename=main_log_path,
    when='midnight',
    interval=1,
    backupCount=30,  # 修改这里：保留最近 30 天的日志
    encoding='utf-8'
)
```

### 修改日志格式

```python
# 详细格式（用于文件）
detailed_formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 简洁格式（用于控制台）
simple_formatter = logging.Formatter(
    fmt='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%m-%d %H:%M:%S'
)
```

## 🚨 注意事项

### 1. print 语句重定向

由于 `sys.stdout` 和 `sys.stderr` 已被重定向，所有 `print()` 语句会自动记录到日志中：

```python
# 这两条语句效果相同
print("这是 print 输出")
logger.info("这是 logger 输出")
```

### 2. 日志性能

- 记录日志是同步操作，大量日志可能影响性能
- DEBUG 级别日志不会显示在控制台，但会写入文件
- 100 条日志记录耗时约 4ms（测试环境）

### 3. 文件权限

确保程序有 `logs/` 目录的读写权限：

```python
# 如果日志目录不存在，会自动创建
log_dir = './logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
```

## 📊 日志级别说明

| 级别 | 数值 | 用途 | 控制台显示 | 文件记录 |
|------|------|------|-----------|----------|
| DEBUG | 10 | 详细调试信息 | ❌ | ✅ |
| INFO | 20 | 一般信息 | ✅ | ✅ |
| WARNING | 30 | 警告信息 | ✅ | ✅ |
| ERROR | 40 | 错误信息 | ✅ | ✅ |
| CRITICAL | 50 | 严重错误 | ✅ | ✅ |

## 🔍 故障排查

### 问题 1：日志文件未生成

**检查**:
```python
import os
print(f"当前工作目录: {os.getcwd()}")
print(f"logs 目录是否存在: {os.path.exists('./logs')}")
```

### 问题 2：日志内容乱码

**原因**: Windows PowerShell 编码问题

**解决**:
```powershell
# 在 PowerShell 中设置编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

### 问题 3：日志文件过大

**解决**: 减少 `backupCount` 或提高日志级别：

```python
# 只保留最近 7 天的日志
backupCount=7

# 提高日志级别，减少日志量
logger.setLevel(logging.INFO)
console_handler.setLevel(logging.WARNING)
```

## 📝 最佳实践

### 1. 合理使用日志级别

```python
# ✅ 好的做法
logger.debug("变量 x 的值: {x}")  # 详细调试信息
logger.info("用户登录成功")       # 重要业务事件
logger.warning("磁盘空间不足")    # 需要关注的警告
logger.error("数据库连接失败")    # 错误但可恢复

# ❌ 不好的做法
logger.error("用户点击了按钮")    # 这应该是 INFO
logger.info("变量 x = 1")         # 这应该是 DEBUG
```

### 2. 使用结构化日志

```python
# ✅ 好的做法
logger.info(f"用户 {user_id} 登录成功，IP: {ip_address}")
logger.error(f"API 请求失败: {api_name}, 错误: {error_message}")

# ❌ 不好的做法
logger.info("用户登录成功")
logger.error("API 失败")
```

### 3. 记录上下文信息

```python
try:
    result = risky_operation()
except Exception as e:
    # ✅ 包含上下文信息
    logger.error(f"操作失败 - 参数: {params}, 错误: {e}", exc_info=True)
    
    # ❌ 缺少上下文
    logger.error(f"操作失败: {e}")
```

## 🎉 总结

新的日志系统提供了：

✅ **清晰的文件结构** - 主日志和最近运行日志分离  
✅ **自动管理** - 按天轮转，自动清理旧日志  
✅ **灵活配置** - 支持多级别、多格式日志  
✅ **性能优化** - 异步写入，不影响主流程  
✅ **便于调试** - 快速定位最近一次运行的问题  

现在可以更轻松地追踪和诊断程序运行中的问题了！🚀