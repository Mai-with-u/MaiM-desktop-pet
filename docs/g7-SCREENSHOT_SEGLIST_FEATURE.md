# 截图功能增强 - 支持文本+图片复合消息

## 文档概述

本文档记录了截图功能的增强改造，使其支持在截图时添加文本说明，并使用 `seglist`（复合消息）格式发送。

**文档版本：** v1.0  
**创建日期：** 2026-01-14  
**最后更新：** 2026-01-14

---

## 一、背景与需求

### 1.1 原有功能

原有截图功能：
- 用户按快捷键触发截图
- 在全屏模式下选择截图区域
- 确认后发送纯图片消息

### 1.2 新需求

用户希望在发送截图时能够：
1. 添加文本说明（可选）
2. 将文本和图片组合成一个消息发送
3. 使用 `maim_message` 规范的 `seglist` 格式

---

## 二、技术方案

### 2.1 消息格式设计

根据 `maim_message` 规范，`seglist` 是一个复合消息类型，包含多个 `Seg` 对象：

```python
# seglist 结构示例
{
    "message_info": {...},
    "message_segment": {
        "type": "seglist",
        "data": [
            {"type": "text", "data": "这是一张图片："},
            {"type": "image", "data": "base64编码的图片数据"}
        ]
    },
    "raw_message": ""
}
```

### 2.2 实现方案

1. **截图选择器增强**：在确认面板中添加文本输入框
2. **chat.py 扩展**：添加 seglist 相关发送方法
3. **消息发送逻辑**：根据是否有文本选择发送方式

---

## 三、详细实现

### 3.1 chat.py 重构

#### 新增方法

##### 3.1.1 `_create_seglist_segment()`

创建 `seglist` 类型的消息片段：

```python
def _create_seglist_segment(
    self,
    segments: List[Union[Seg, tuple]]
) -> Seg:
    """创建 seglist 类型的消息片段
    
    参数:
        segments: Seg 对象列表，或 (type, data) 元组列表
    
    返回:
        Seg: seglist 类型的消息片段
    """
    seg_list = []
    
    for seg in segments:
        if isinstance(seg, Seg):
            # 已经是 Seg 对象，直接使用
            seg_list.append(seg)
        elif isinstance(seg, tuple) and len(seg) == 2:
            # 元组形式，创建 Seg 对象
            seg_type, seg_data = seg
            
            # 确保 seg_data 是字符串类型
            if isinstance(seg_data, dict):
                # 如果是字典，转换为字符串
                import json
                seg_data = json.dumps(seg_data, ensure_ascii=False)
            elif not isinstance(seg_data, str):
                # 其他非字符串类型，转换为字符串
                seg_data = str(seg_data)
            
            seg_list.append(Seg(type=seg_type, data=seg_data))
        else:
            logger.warning(f"无效的段格式，已跳过: {seg}")
    
    return Seg(type="seglist", data=seg_list)
```

**设计要点：**
- 支持两种输入形式：Seg 对象或元组
- 自动过滤无效输入
- 返回完整的 seglist Seg 对象
- **重要**：确保所有 `data` 字段都是字符串类型，避免序列化错误

##### 3.1.2 `send_seglist()`

发送复合消息：

```python
async def send_seglist(
    self,
    segments: List[Union[Seg, tuple]],
    user_id: Optional[str] = None,
    user_nickname: Optional[str] = None,
    user_cardname: Optional[str] = None,
    additional_config: Optional[dict] = None
) -> bool:
    """发送复合消息（seglist）"""
    try:
        # 创建 seglist 段
        seglist = self._create_seglist_segment(segments)
        
        # 创建用户信息和消息信息
        user_info = self._create_user_info(user_id, user_nickname, user_cardname)
        message_info = self._create_message_info(user_info, additional_config)
        
        # 创建消息
        message_base = MessageBase(
            message_info=message_info,
            message_segment=seglist,
            raw_message=""
        )
        
        # 发送消息
        send_success = await protocol_manager.send_message(message_base.to_dict())
        
        if not send_success:
            logger.warning(f"seglist 消息发送失败 - 协议管理器返回失败")
            return False
        
        # 保存到数据库
        if db_manager.is_initialized():
            await db_manager.save_message(message_base.to_dict())
        
        logger.info(f"seglist 消息发送成功 - ID: {message_base.message_info.message_id}, "
                   f"段数: {len(segments)}")
        
        return True
        
    except Exception as e:
        logger.error(f"seglist 消息发送失败 - 错误: {e}", exc_info=True)
        return False
```

**设计要点：**
- 完整的错误处理和日志记录
- 自动保存到数据库
- 支持所有用户信息参数

##### 3.1.3 `send_text_and_image()`

发送文本+图片的便捷方法：

```python
async def send_text_and_image(
    self,
    text: str,
    image_data: str,
    user_id: Optional[str] = None,
    user_nickname: Optional[str] = None,
    user_cardname: Optional[str] = None,
    additional_config: Optional[dict] = None
) -> bool:
    """发送文本+图片的复合消息（便捷方法）"""
    return await self.send_seglist([
        ("text", text),
        ("image", image_data),
    ], user_id, user_nickname, user_cardname, additional_config)
```

##### 3.1.4 `send_pixmap_with_text()`

发送 QPixmap 图片（带可选文本）：

```python
async def send_pixmap_with_text(
    self,
    pixmap,
    text: str = "",
    user_id: Optional[str] = None,
    user_nickname: Optional[str] = None,
    user_cardname: Optional[str] = None,
    additional_config: Optional[dict] = None
) -> bool:
    """发送 QPixmap 图片（带可选文本）"""
    try:
        # 将 QPixmap 转换为 base64（无头部）
        image_base64 = pixmap_to_base64(pixmap, add_header=False)
        
        if text:
            # 发送文本+图片
            return await self.send_text_and_image(
                text, image_base64, user_id, user_nickname, user_cardname, additional_config
            )
        else:
            # 只发送图片
            return await self.send_image(image_base64)
            
    except Exception as e:
        logger.error(f"发送 QPixmap 失败 - 错误: {e}", exc_info=True)
        return False
```

**设计要点：**
- 自动处理 QPixmap 到 base64 的转换
- 根据是否有文本智能选择发送方式
- 完整的异常处理

### 3.2 ScreenshotSelector.py 增强

#### 3.2.1 选项栏布局改进

**新增组件：**
- `QLineEdit`：用于输入文本说明

**尺寸调整：**
- 原尺寸：280x50
- 新尺寸：350x90

**布局结构：**
```
OptionPanel (350x90)
├── 文本输入框容器 (margin: 10,8,10,0)
│   └── QLineEdit (placeholder: "输入文字说明（可选）...")
└── 按钮容器 (margin: 10,0,10,8)
    ├── 确认按钮 (✓)
    ├── 取消按钮 (✕)
    └── 重新选择按钮 (↺)
```

#### 3.2.2 新增方法

##### `get_text()`

获取用户输入的文本：

```python
def get_text(self) -> str:
    """获取输入的文本"""
    return self.text_input.text().strip()
```

##### `clear_text()`

清空文本输入框：

```python
def clear_text(self):
    """清空文本输入框"""
    self.text_input.clear()
```

#### 3.2.3 修改的方法

##### `_confirm_screenshot()`

确认截图时获取文本：

```python
def _confirm_screenshot(self):
    """确认截图"""
    if self.selection_rect.isNull() or self.selection_rect.width() < 10 or self.selection_rect.height() < 10:
        logger.warning("选区无效，取消截图")
        self.close()
        return
    
    logger.info(f"确认截图，选区: {self.selection_rect}")
    
    # 获取输入的文本
    text = self.option_panel.get_text()
    
    # 隐藏窗口和选项面板
    self.option_panel.hide()
    self.hide()
    QApplication.processEvents()
    
    # 获取屏幕截图
    screen = QApplication.primaryScreen()
    full_pixmap = screen.grabWindow(0)
    
    # 截取选定区域
    selected_pixmap = full_pixmap.copy(self.selection_rect)
    
    # 关闭选择器
    self.close()
    
    # 返回截图和文本
    self.on_screenshot_captured(selected_pixmap, text)
```

##### `on_screenshot_captured()`

修改方法签名以支持文本：

```python
def on_screenshot_captured(self, pixmap, text=""):
    """子类需重写此方法处理截图
    
    参数:
        pixmap: 截图 QPixmap
        text: 用户输入的文本（可选）
    """
    raise NotImplementedError
```

#### 3.2.4 UI 样式优化

文本输入框样式：

```python
self.text_input.setStyleSheet("""
    QLineEdit {
        background-color: rgba(255, 255, 255, 0.95);
        color: #333;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 12px;
    }
    QLineEdit:focus {
        border: 1px solid #007bff;
        background-color: rgba(255, 255, 255, 1);
    }
""")
```

**设计要点：**
- 半透明白色背景，与面板风格一致
- 聚焦时高亮边框
- 清晰的占位符文本

### 3.3 pet.py 集成

#### 3.3.1 ScreenshotManager 修改

##### `handle_screenshot()`

处理截图结果并智能选择发送方式：

```python
def handle_screenshot(self, pixmap, text=""):
    """处理截图结果
    
    参数:
        pixmap: 截图 QPixmap
        text: 用户输入的文本说明（可选）
    """
    self.parent.show()
    for chat_bubble in self.parent.chat_bubbles._active_bubbles:
        chat_bubble.show()
    
    # 显示截图气泡
    self.parent.show_message(pixmap=pixmap, msg_type="sent")
    
    # 发送消息
    if text:
        # 有文本，发送文本+图片的 seglist
        logger.info(f"发送文本+图片复合消息，文本: {text}")
        asyncio.run(chat_util.send_pixmap_with_text(pixmap, text))
    else:
        # 无文本，只发送图片
        logger.info("发送纯图片消息")
        asyncio.run(chat_util.send_pixmap_with_text(pixmap, ""))
```

**设计要点：**
- 恢复窗口和气泡显示
- 根据是否有文本智能选择发送方式
- 详细的日志记录

#### 3.3.2 PetScreenshotSelector 修改

##### `on_screenshot_captured()`

传递文本参数：

```python
def on_screenshot_captured(self, pixmap, text=""):
    """处理截图结果
    
    参数:
        pixmap: 截图 QPixmap
        text: 用户输入的文本说明（可选）
    """
    self.pet.screenshot_manager.handle_screenshot(pixmap, text)
```

---

## 四、使用示例

### 4.1 发送纯图片

用户操作：
1. 按截图快捷键
2. 选择截图区域
3. 不输入文本，直接点击确认

结果：
```python
# 发送纯图片消息
{
    "type": "image",
    "data": "base64编码的图片数据"
}
```

### 4.2 发送文本+图片

用户操作：
1. 按截图快捷键
2. 选择截图区域
3. 输入文本："这是我的桌面"
4. 点击确认

结果：
```python
# 发送 seglist 复合消息
{
    "type": "seglist",
    "data": [
        {"type": "text", "data": "这是我的桌面"},
        {"type": "image", "data": "base64编码的图片数据"}
    ]
}
```

### 4.3 编程方式使用

#### 发送纯文本

```python
await chat_util.send_text("你好")
```

#### 发送纯图片

```python
from PyQt5.QtGui import QPixmap
pixmap = QPixmap("path/to/image.png")
await chat_util.send_pixmap_with_text(pixmap)
```

#### 发送文本+图片

```python
from PyQt5.QtGui import QPixmap
pixmap = QPixmap("path/to/image.png")
await chat_util.send_pixmap_with_text(pixmap, "这是图片说明")
```

#### 发送自定义 seglist

```python
from maim_message import Seg

# 使用 Seg 对象
await chat_util.send_seglist([
    Seg("text", "第一段文本"),
    Seg("image", "base64..."),
    Seg("text", "第二段文本"),
])

# 使用元组
await chat_util.send_seglist([
    ("text", "你好"),
    ("emoji", "base64..."),
    ("text", "哈哈"),
])
```

---

## 五、技术细节

