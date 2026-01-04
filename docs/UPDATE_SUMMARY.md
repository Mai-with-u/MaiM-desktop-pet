# 更新摘要

本文档提供 MaiM-desktop-pet 项目 v2.0.0 版本的快速更新概览。

## 📋 快速概览

**版本**: v2.0.0  
**发布日期**: 2025-01-05  
**主要更新**: maim_message 库升级、聊天模块重构、Bug 修复

## 🎯 主要变更

### 1. 标准消息类升级
- ✅ 兼容 maim_message v0.6.1+
- ✅ 新增 4 个消息信息类（GroupInfo、TemplateInfo、SenderInfo、ReceiverInfo）
- ✅ 完全向后兼容

### 2. 聊天模块重构
- ✅ 改进代码结构和可维护性
- ✅ 添加输入验证和错误处理
- ✅ 新增便捷方法（send_text、send_image、send_emoji）
- ✅ 修复配置文件参数为空的问题

### 3. 样式表修复
- ✅ 修复 bubble_input.css 格式错误

## 🔧 关键修复

### 修复 1: 注册用户失败
**问题**: 发送消息时报错 "platform、user_id 和 nickname 都是必需参数"

**原因**: 
- 配置文件中 `userNickname` 为空字符串
- 缺少参数验证

**解决**:
```python
# 智能获取默认昵称
default_nick = getattr(config, 'userNickname', '')
self.default_sender_nickname = (
    default_nick if default_nick 
    else getattr(config, 'Nickname', '桌面宠物')
)
```

### 修复 2: CSS 样式解析错误
**问题**: bubble_input.css 格式错误导致样式无法正常应用

**解决**: 修复 QPushButton 样式块的括号缺失问题

## 📊 更新文件清单

### 修改的文件
- `src/shared/models/message.py` - 标准消息类升级
- `src/core/chat.py` - 聊天模块重构
- `src/frontend/style_sheets/bubble_input.css` - CSS 修复
- `src/shared/models/README.md` - 文档更新

### 新增的文件
- `docs/CHANGELOG.md` - 详细更新日志
- `docs/UPDATE_SUMMARY.md` - 本文件

## 🚀 升级指南

### 对于开发者

1. **更新依赖**:
```bash
pip install --upgrade maim-message>=0.6.1
```

2. **代码迁移**（可选，旧代码仍兼容）:
```python
# 旧方式（仍然可用）
await chat_util.easy_to_send("消息", "text")

# 新方式（推荐）
await chat_util.send("消息", msg_type="text")
await chat_util.send_text("消息")  # 更简洁
```

3. **配置更新**:
```toml
# config.toml
userNickname = "你的昵称"  # 建议设置，不要留空
```

### 对于用户

无需任何操作，所有更新完全向后兼容。如果遇到问题，请检查配置文件中的 `userNickname` 设置。

## ✅ 验证更新

运行测试验证更新是否成功：

```bash
# 测试标准消息类
python tests/test_message_update.py

# 测试聊天模块
python tests/test_chat_fix.py
```

## 📚 详细文档

- [完整更新日志](CHANGELOG.md)
- [标准消息类文档](../src/shared/models/README.md)
- [气泡消息使用指南](../src/frontend/bubble_speech_usage.md)

## 💡 使用示例

### 发送消息

```python
from src.core.chat import chat_util

# 方式 1: 旧方法（兼容）
await chat_util.easy_to_send("你好", "text")

# 方式 2: 新方法（推荐）
await chat_util.send_text("你好")

# 方式 3: 发送图片
await chat_util.send_image("http://example.com/image.png")

# 方式 4: 发送表情
await chat_util.send_emoji("😊")

# 方式 5: 自定义参数
await chat_util.send(
    text="自定义消息",
    msg_type="text",
    user_id="custom_id",
    user_nickname="自定义用户",
    additional_config={"custom_key": "custom_value"}
)
```

### 创建消息对象

```python
from src.shared.models.message import MessageBase

# 创建消息
message = MessageBase.create_text_message(
    text="测试消息",
    platform="desktop-pet",
    user_id="123",
    user_nickname="测试用户",
    msg_type="text"
)

# 访问属性
print(f"消息ID: {message.message_id}")
print(f"内容: {message.message_content}")
print(f"用户: {message.user_nickname}")
```

## ⚠️ 注意事项

1. **配置文件**: 确保 `config.toml` 中的 `userNickname` 不为空，或正确设置 `Nickname` 作为后备
2. **maim_message 版本**: 确保安装了 maim_message v0.6.1 或更高版本
3. **测试**: 升级后建议运行测试验证功能正常

## 🤝 贡献

如果您在更新过程中遇到问题或发现 Bug，请：

1. 检查 [更新日志](CHANGELOG.md) 中的已知问题
2. 运行测试验证环境
3. 提交 Issue 到项目仓库

---

**更新完成时间**: 2025-01-05  
**维护团队**: MaiM-desktop-pet Team
