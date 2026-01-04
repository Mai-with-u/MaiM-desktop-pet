# 更新日志

本文档记录 MaiM-desktop-pet 项目的所有重要更新和变更。

## [2025-01-05] - v2.0.0

### 🎉 重大更新 - maim_message 库升级

#### 标准消息类更新

**文件**: `src/shared/models/message.py`

**变更内容**:
- 升级以兼容 `maim_message` v0.6.1+ 版本
- 新增 `GroupInfo` 类 - 支持群组信息
- 新增 `TemplateInfo` 类 - 支持消息模板
- 新增 `SenderInfo` 类 - 发送者信息
- 新增 `ReceiverInfo` 类 - 接收者信息
- 更新 `BaseMessageInfo` 类，添加新的可选字段：
  - `group_info`: 群组信息（可选）
  - `template_info`: 模板信息（可选）
  - `sender_info`: 发送者信息（可选）
  - `receiver_info`: 接收者信息（可选）
- 更新序列化和反序列化逻辑以支持新字段
- 完全向后兼容旧版本数据

**向后兼容性**: ✅ 完全兼容 - 所有新增字段都是可选的

#### 聊天模块重构

**文件**: `src/core/chat.py`

**变更内容**:
- 重构 `chat` 类为 `Chat` 类（符合 PEP 8 命名规范）
- 改进代码结构，将消息创建逻辑拆分为多个私有方法：
  - `_create_user_info()`: 创建用户信息
  - `_create_message_info()`: 创建消息信息
  - `_create_message()`: 创建完整消息对象
- 添加输入验证和错误处理
- 改进日志记录，包含更详细的信息
- 添加新的便捷方法：
  - `send_text()`: 发送文本消息
  - `send_image()`: 发送图片消息
  - `send_emoji()`: 发送表情消息
- 修复配置文件 `userNickname` 为空时的问题
- 确保 `platform`、`user_id`、`user_nickname`、`user_cardname` 参数不为空
- 添加完整的文档字符串

**API 变更**:
```python
# 旧版本（仍兼容）
await chat_util.easy_to_send("消息", "text")

# 新版本（推荐）
await chat_util.send("消息", msg_type="text")
await chat_util.send_text("消息")
await chat_util.send_image("image_url")
await chat_util.send_emoji("😊")
```

**向后兼容性**: ✅ 完全兼容 - 保留 `easy_to_send()` 方法

#### 样式表修复

**文件**: `src/frontend/style_sheets/bubble_input.css`

**修复内容**:
- 修复 `QPushButton` 样式块的格式错误
- 添加缺失的右括号
- 修复 `QPushButton:hover` 样式定义

**问题**: CSS 文件中 `QPushButton` 样式块缺少结束括号，导致样式解析错误。

#### 文档更新

**文件**: 
- `src/shared/models/README.md`
- `docs/CHANGELOG.md` (新建)

**更新内容**:
- 更新标准消息类文档，说明 v0.6.1+ 版本的新特性
- 添加新类的详细说明和使用示例
- 添加与 maim_message 库的兼容性说明
- 更新版本信息和更新日志

### 🐛 Bug 修复

1. **修复注册用户失败问题**
   - 问题：发送消息时报错 "platform、user_id 和 nickname 都是必需参数"
   - 原因：配置文件中 `userNickname` 为空字符串，且缺少参数验证
   - 解决：在 `_create_user_info()` 方法中添加参数验证，确保所有必需参数不为空
   - 优先使用 `userNickname`，如果为空则使用 `Nickname` 作为后备

2. **修复 CSS 样式解析错误**
   - 问题：`bubble_input.css` 文件格式错误，导致样式无法正常应用
   - 解决：修复 QPushButton 样式块的括号缺失问题

3. **修复异步任务执行错误**
   - 问题：在 PyQt5 回调函数中调用 `asyncio.create_task()` 报错 "RuntimeError: no running event loop"
   - 原因：PyQt5 的事件循环与 asyncio 的事件循环不兼容，直接调用 `create_task()` 会失败
   - 解决：添加 `_async_save()` 方法，智能处理异步任务的执行：
     - 检查是否有运行中的事件循环
     - 如果有，使用 `asyncio.ensure_future()` 在现有循环中执行
     - 如果没有，创建新的事件循环来执行任务
     - 添加完整的异常处理，避免影响 UI 线程
   - 影响：修复了用户发送消息时保存到数据库的崩溃问题

### 📝 技术细节

#### maim_message v0.6.1+ 变更

新增类：

```python
# GroupInfo - 群组信息
@dataclass
class GroupInfo:
    group_id: str = ""
    group_name: str = ""

# TemplateInfo - 模板信息
@dataclass
class TemplateInfo:
    template_id: str = ""
    template_name: str = ""
    template_data: Dict[str, Any] = field(default_factory=dict)

# SenderInfo - 发送者信息
@dataclass
class SenderInfo:
    platform: str = ""
    user_id: str = ""
    user_nickname: str = ""
    user_cardname: str = ""

# ReceiverInfo - 接收者信息
@dataclass
class ReceiverInfo:
    platform: str = ""
    user_id: str = ""
    user_nickname: str = ""
    user_cardname: str = ""
```

BaseMessageInfo 新增字段：

```python
@dataclass
class BaseMessageInfo:
    # ... 原有字段 ...
    group_info: Optional[GroupInfo] = None
    template_info: Optional[TemplateInfo] = None
    sender_info: Optional[SenderInfo] = None
    receiver_info: Optional[ReceiverInfo] = None
```

#### Chat 类改进

**初始化逻辑**:
```python
def __init__(self):
    self.format_info = FormatInfo(...)
    self.default_user_id = "0"
    
    # 智能获取默认昵称
    default_nick = getattr(config, 'userNickname', '')
    self.default_sender_nickname = (
        default_nick if default_nick 
        else getattr(config, 'Nickname', '桌面宠物')
    )
```

**用户信息创建**:
```python
def _create_user_info(self, user_id=None, user_nickname=None, user_cardname=None):
    platform = getattr(config, 'platform', 'desktop-pet')
    uid = user_id or self.default_user_id
    nickname = user_nickname if user_nickname else self.default_sender_nickname
    cardname = user_cardname if user_cardname else nickname
    
    return UserInfo(
        platform=platform,
        user_id=uid,
        user_nickname=nickname,
        user_cardname=cardname,
    )
```

### 🔧 配置建议

为确保消息正常发送，建议在 `config.toml` 中配置：

```toml
[Nickname]
userNickname = "你的昵称"  # 设置你的昵称，不要留空
platform = "desktop-pet"
```

如果 `userNickname` 留空，系统会自动使用 `Nickname` 作为后备。

### 📊 兼容性矩阵

| 组件 | 旧版本 | 新版本 | 兼容性 |
|------|--------|--------|--------|
| maim_message | v0.5.x | v0.6.1+ | ✅ 向上兼容 |
| 标准消息类 | v1.0.0 | v2.0.0 | ✅ 完全兼容 |
| Chat 模块 | v1.0.0 | v2.0.0 | ✅ 完全兼容 |
| 配置文件 | v1.0.0 | v2.0.0 | ✅ 完全兼容 |

### 🧪 测试

建议运行以下测试验证更新：

```bash
# 测试标准消息类
python tests/test_message_update.py

# 测试聊天模块
python tests/test_chat_fix.py
```

### 📖 相关文档

- [标准消息类文档](../src/shared/models/README.md)
- [气泡消息使用指南](../src/frontend/bubble_speech_usage.md)
- [数据库集成文档](../src/database/README.md)

---

## 更新日志格式

每个版本的更新日志应包含：

- **版本号**: 遵循语义化版本规范 (Semantic Versioning)
- **发布日期**: YYYY-MM-DD 格式
- **重大更新**: 🎉 标记
- **新增功能**: ✨ 标记
- **改进优化**: 🔧 标记
- **Bug 修复**: 🐛 标记
- **文档更新**: 📝 标记
- **破坏性变更**: ⚠️ 标记

---

*本文档由 MaiM-desktop-pet 团队维护*
