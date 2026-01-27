# 消息从 LLM 返回后的完整处理流程

本文档详细说明消息从 LLM 返回后，经过协议层、路由器、信号总线，最终显示在用户界面上的完整处理流程。

---

## 一、消息接收流程概览

```
LLM 响应
    ↓
OpenAIProtocol._call_openai_api()
    ↓
消息处理器回调
    ↓
router.message_handler()
    ↓
保存到数据库
    ↓
发送 Qt 信号
    ↓
DesktopPet.show_message()
    ↓
BubbleManager.show_message()
    ↓
SpeechBubbleList.add_message()
    ↓
创建并显示气泡
```

---

## 二、详细处理步骤

### 步骤 1: LLM 响应接收

**位置**: `src/core/protocols/openai_protocol.py`

```python
async def _call_openai_api(self, messages: List[Dict[str, Any]]) -> str:
    """调用 OpenAI API"""
    # ... 发送请求到 LLM ...
    
    # 收到响应
    full_response = ""
    async for chunk in response:
        full_response += chunk
    
    # 构造消息对象
    simulated_message = {
        'user_id': '1',  # 0 表示自己发送，1 表示接收
        'message_segment': {
            'type': 'text',
            'data': full_response
        },
        'timestamp': int(time.time())
    }
    
    # 触发消息处理器
    if self._message_handler:
        await self._message_handler(simulated_message)
    
    return full_response
```

**关键点**:
- LLM 响应是流式接收的（async for chunk）
- 将响应包装成统一的消息格式
- 消息格式包含 `user_id`、`message_segment`、`timestamp` 字段
- `user_id = '0'` 表示自己发送，`'1'` 表示接收的消息
- 通过 `self._message_handler` 回调传递消息

---

### 步骤 2: 路由器消息处理

**位置**: `src/core/router.py`

```python
async def message_handler(message):
    """
    消息处理函数
    从协议层收到的消息将会进入此函数
    """
    # 提取消息内容
    logger.info(f"收到消息: {message}")
    
    # 1. 保存到数据库（异步）
    try:
        if db_manager.is_initialized():
            save_success = await db_manager.save_message(message)
            if save_success:
                logger.debug(f"接收消息已保存到数据库")
    except Exception as e:
        logger.error(f"保存接收消息到数据库时出错: {e}", exc_info=True)
    
    # 2. 解析消息内容
    message_segment = message.get('message_segment', {})
    
    if not message_segment:
        logger.warning(f"消息格式错误，缺少 message_segment: {message}")
        return
    
    message_type = message_segment.get('type', '')
    message_data = message_segment.get('data', '')
    
    # 3. 发送 Qt 信号（跨线程安全）
    if message_type == "text":
        message_content = str(message_data)
        signals_bus.message_received.emit(message_content)
    else:
        logger.warning(f"不支持的消息格式: {message_type}")
```

**关键点**:
- **异步保存到数据库**: 使用 `await db_manager.save_message(message)`，不阻塞后续流程
- **消息格式解析**: 从统一的消息格式中提取 `message_segment`
- **类型检查**: 目前只支持 `type = "text"` 的消息
- **Qt 信号发送**: `signals_bus.message_received.emit(message_content)` - 这是跨线程安全的

---

### 步骤 3: 信号总线

**位置**: `src/frontend/signals.py`

```python
class GlobalSignals(QObject):
    # 定义全局信号
    message_received = pyqtSignal(str)  # 参数类型: str
    position_changed = pyqtSignal(QPoint)

# 创建全局信号总线实例
signals_bus = GlobalSignals()
```

**关键点**:
- 使用 PyQt5 的 `pyqtSignal` 实现跨线程通信
- `message_received` 信号传递一个 `str` 类型的消息内容
- Qt 信号是线程安全的，可以从后台线程安全地发送到主线程

---

### 步骤 4: 信号连接

**位置**: `src/frontend/presentation/pet.py` - `DesktopPet.__init__()`

```python
class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        # ... 其他初始化代码 ...
        
        # 连接信号
        signals_bus.message_received.connect(self.show_message)
```

**关键点**:
- 在主窗口初始化时，将 `message_received` 信号连接到 `self.show_message` 槽函数
- 当信号被 emit 时，主线程的 `show_message` 函数会被调用

---

### 步骤 5: 消息显示

**位置**: `src/frontend/presentation/pet.py`

```python
class DesktopPet(QWidget):
    def show_message(self, text=None, msg_type: Literal["received", "sent"] = "received", pixmap=None):
        """显示消息
        
        参数:
            text: 文本消息内容
            msg_type: 消息类型，"received" 表示接收，"sent" 表示发送
            pixmap: 图片消息（可选）
        """
        self.bubble_manager.show_message(text, msg_type, pixmap)
```

**关键点**:
- `show_message` 是槽函数，在主线程中执行
- `msg_type` 默认为 `"received"`，因为 `router.message_handler` 处理的都是接收的消息
- 委托给 `BubbleManager` 处理具体的气泡显示

---

### 步骤 6: 气泡管理器

**位置**: `src/frontend/presentation/pet.py`

```python
class BubbleManager:
    """气泡管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.chat_bubbles = None
        self.bubble_input = None
    
    def set_widgets(self, chat_bubbles, bubble_input):
        """设置气泡组件"""
        self.chat_bubbles = chat_bubbles
        self.bubble_input = bubble_input
    
    def show_message(self, text=None, msg_type: Literal["received", "sent"] = "received", pixmap=None):
        """显示消息"""
        if self.chat_bubbles:
            self.chat_bubbles.add_message(text, msg_type, pixmap)
            # 25秒后删除第一条消息
            QTimer.singleShot(25000, self.del_first_msg)
```

**关键点**:
- `BubbleManager` 管理气泡组件
- 将消息传递给 `SpeechBubbleList.add_message()`
- 设置定时器，25秒后自动删除最旧的消息

---

### 步骤 7: 气泡列表

**位置**: `src/frontend/bubble_speech.py`

```python
class SpeechBubbleList():
    def __init__(self, parent=None, use_database: bool = True):
        self.parent = parent
        self._active_bubbles = []  # 保存所有活动气泡
        self.use_database = use_database  # 是否使用数据库存储
    
    def add_message(self, 
                  message: str | MessageBase = "", 
                  msg_type: Literal["received", "sent"] = "received",
                  pixmap: Optional[QPixmap] = None,
                  save_to_db: bool = True):
        """添加新消息"""
        # 1. 提取文本内容
        if isinstance(message, MessageBase):
            text_content = message.message_content
            # 从 MessageBase 对象确定消息类型
            if message.user_id == "0":
                msg_type = "sent"
            else:
                msg_type = "received"
        else:
            text_content = message
        
        # 2. 创建气泡对象
        new_bubble = SpeechBubble(
            parent=self.parent,
            bubble_type=msg_type,
            text=text_content,
            pixmap=pixmap
        )
        
        # 3. 添加到活动气泡列表
        self._active_bubbles.append(new_bubble)
        
        # 4. 显示气泡
        new_bubble.show_message()
        self.update_position()
        
        # 5. 异步保存到数据库（避免重复保存）
        if self.use_database and save_to_db:
            if message_obj:
                self._async_save(self._save_to_database(message_obj))
            else:
                self._async_save(self._save_message_to_db(text_content, msg_type))
```

**关键点**:
- **气泡创建**: 创建 `SpeechBubble` 对象
- **显示气泡**: 调用 `show_message()` 显示气泡
- **位置更新**: 调用 `update_position()` 自动排列气泡
- **数据库保存**: 注意这里会再次尝试保存，但消息已在 `router.message_handler` 中保存过，所以 `save_to_db` 参数控制是否重复保存

---

### 步骤 8: 气泡渲染

**位置**: `src/frontend/bubble_speech.py`

```python
class SpeechBubble(QLabel):
    def __init__(self, parent=None, bubble_type="received", text: str = "", pixmap: Optional[QPixmap] = None):
        super().__init__(parent)
        
        # 窗口属性
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 数据
        self.text_data = text
        self.original_pixmap = pixmap
        self.bubble_type = bubble_type  # "received" 或 "sent"
        
        # 根据气泡类型设置样式
        if bubble_type == "received":
            self.bg_color = QColor(240, 248, 255)  # 爱丽丝蓝
            self.follow_offset = QPoint(-100, -30)  # 向左偏移
        else:
            self.bg_color = QColor(200, 255, 200)  # 浅绿色
            self.follow_offset = QPoint(100, -30)   # 向右偏移
        
        # 字体设置
        self.setFont(QFont("Microsoft YaHei", 12))
        
        # ... 其他样式设置 ...
    
    def paintEvent(self, event):
        """绘制气泡"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 绘制圆角矩形主体
        body_rect = self.rect().adjusted(0, 0, 0, -self.arrow_height)
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(body_rect, self.corner_radius, self.corner_radius)
        
        # 2. 绘制箭头
        # 根据气泡类型决定箭头方向
        
        # 3. 绘制内容（图片和/或文字）
        # ... 绘制代码 ...
```

**关键点**:
- **无框窗口**: 使用 `Qt.ToolTip | Qt.FramelessWindowHint` 创建无边框窗口
- **透明背景**: 使用 `Qt.WA_TranslucentBackground` 实现透明背景
- **样式区分**: 
  - `received` 气泡: 爱丽丝蓝 (240, 248, 255)，箭头在左侧
  - `sent` 气泡: 浅绿色 (200, 255, 200)，箭头在右侧
- **自定义绘制**: 通过 `paintEvent` 自定义绘制气泡形状和内容

---

### 步骤 9: 气泡位置排列

**位置**: `src/frontend/bubble_speech.py` - `SpeechBubbleList.update_position()`

```python
def update_position(self):
    """更新所有活动气泡的位置，自动排列并处理边界情况"""
    # 1. 获取屏幕和父对象几何信息
    screen_geo = QApplication.primaryScreen().availableGeometry()
    parent_rect = self.parent.geometry()
    
    # 2. 计算基准位置
    center_x = parent_rect.center().x()
    base_y = parent_rect.top() - 30  # 初始Y位置
    
    # 3. 从下往上排列气泡
    total_height = 0
    visible_bubbles = [b for b in self._active_bubbles if b.isVisible()]
    
    for bubble in reversed(visible_bubbles):
        # 根据气泡类型确定水平位置
        if bubble.bubble_type == "received":
            # 接收气泡：左侧对齐
            x_pos = center_x - 160 - bubble_width//2
        else:
            # 发送气泡：右侧对齐
            x_pos = center_x + 160 - bubble_width//2
        
        # 计算垂直位置(从下往上排列)
        y_pos = base_y - total_height - bubble_height
        
        # 4. 检查边界并调整
        if y_pos < screen_geo.top():
            # 上方空间不足，改为显示在下方
            y_pos = parent_rect.bottom() + total_height + 30
            bubble.arrow_height = -abs(bubble.arrow_height)  # 箭头朝下
        
        # 5. 应用新位置
        bubble.move(int(x_pos), int(y_pos))
        
        # 6. 更新累计高度
        total_height += bubble_height + self._vertical_spacing
        
        # 7. 如果超过屏幕高度1/3，移除最旧的气泡
        if total_height > screen_geo.height() // 3:
            self.del_first_msg()
```

**关键点**:
- **从下往上排列**: 最新的消息在最下方
- **左右分开**: `received` 在左侧，`sent` 在右侧
- **边界检测**: 自动检测屏幕上方空间，不足时显示在下方
- **自动清理**: 超过屏幕高度1/3时自动删除最旧的消息

---

### 步骤 10: 气泡消失动画

**位置**: `src/frontend/bubble_speech.py`

```python
class SpeechBubble(QLabel):
    def fade_out(self):
        """淡出并移除气泡"""
        if self.animation_group.state() == QPropertyAnimation.Running:
            self.animation_group.stop()
        
        self.animation_group.clear()
        
        # 创建淡出动画
        fade_anim = QPropertyAnimation(self, b"windowOpacity")
        fade_anim.setDuration(500)  # 500ms
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.0)
        fade_anim.finished.connect(self.deleteLater)  # 动画完成后删除对象
        
        self.animation_group.addAnimation(fade_anim)
        self.animation_group.start()
```

**关键点**:
- **透明度动画**: 使用 `QPropertyAnimation` 实现淡出效果
- **自动清理**: 动画完成后调用 `deleteLater()` 删除对象
- **定时触发**: 25秒后自动触发 `fade_out()`

---

## 三、数据库存储流程

### 存储时机

消息在 **两个地方** 尝试存储到数据库：

1. **第一次存储**: `router.message_handler()` 中
   - 接收到消息后立即保存
   - 使用原始消息格式（包含完整字段）

2. **第二次尝试**: `SpeechBubbleList.add_message()` 中
   - 创建气泡时再次尝试保存
   - 通过 `save_to_db` 参数控制是否重复保存
   - 默认 `save_to_db=True`，但可以通过 `save_to_db=False` 跳过

### 存储实现

**位置**: `src/database/manager.py`

```python
async def save_message(self, message: Dict[str, Any] | MessageBase) -> bool:
    """保存消息到数据库
    
    参数:
        message: 消息字典或 MessageBase 对象
    
    返回:
        是否保存成功
    """
    # 1. 转换为 MessageBase 对象（如果是字典）
    if isinstance(message, dict):
        message = MessageBase.from_dict(message)
    
    # 2. 验证消息
    if not message.validate():
        logger.error("消息验证失败")
        return False
    
    # 3. 写入数据库
    try:
        async with self.db_pool.acquire() as db:
            await db.execute(
                """
                INSERT INTO messages (
                    message_id, user_id, user_nickname,
                    message_content, timestamp
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message.message_id,
                    message.user_id,
                    message.user_nickname,
                    message.message_content,
                    message.timestamp
                )
            )
        return True
    except Exception as e:
        logger.error(f"保存消息失败: {e}", exc_info=True)
        return False
```

---

## 四、完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│ 1. OpenAIProtocol._call_openai_api()                        │
│    - 发送请求到 LLM API                                      │
│    - 流式接收响应                                            │
│    - 构造消息对象:                                           │
│      {                                                      │
│        'user_id': '1',                                       │
│        'message_segment': {                                  │
│          'type': 'text',                                    │
│          'data': 'LLM响应内容'                              │
│        },                                                    │
│        'timestamp': 1234567890                              │
│      }                                                      │
│    - 调用 self._message_handler(message)                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. router.message_handler(message)                          │
│    - 提取消息内容                                            │
│    - 保存到数据库 (await db_manager.save_message)           │
│    - 解析 message_segment                                   │
│    - 发送 Qt 信号:                                           │
│      signals_bus.message_received.emit(message_content)      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. signals_bus.message_received                             │
│    - PyQt5 跨线程信号                                       │
│    - 从后台线程安全地传递到主线程                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. DesktopPet.show_message(text, msg_type="received")       │
│    - 主线程中执行的槽函数                                    │
│    - msg_type 默认为 "received"                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. BubbleManager.show_message(text, msg_type, pixmap)       │
│    - 委托给 chat_bubbles.add_message()                      │
│    - 设置 25 秒后删除定时器                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. SpeechBubbleList.add_message()                          │
│    - 创建 SpeechBubble 对象                                │
│    - 添加到 _active_bubbles 列表                           │
│    - 调用 new_bubble.show_message()                        │
│    - 调用 update_position() 更新位置                        │
│    - (可选) 再次保存到数据库                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. SpeechBubble.show_message()                             │
│    - 计算气泡大小 (calculate_bubble_size)                   │
│    - 调用 resize(size) 调整窗口大小                         │
│    - 调用 show() 显示窗口                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. SpeechBubbleList.update_position()                      │
│    - 计算每个气泡的位置                                      │
│    - received 气泡在左侧，sent 气泡在右侧                    │
│    - 从下往上排列                                           │
│    - 检查边界并调整                                          │
│    - 应用位置: bubble.move(x, y)                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. SpeechBubble.paintEvent()                                │
│    - 绘制圆角矩形背景                                         │
│    - 绘制箭头                                                │
│    - 绘制图片（如果有）                                       │
│    - 绘制文字                                                │
│    - received: 爱丽丝蓝 (240, 248, 255)                     │
│    - sent: 浅绿色 (200, 255, 200)                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    气泡显示在屏幕上
```

---

## 五、关键数据结构

### 1. 消息对象（从 LLM 返回）

```python
message = {
    'user_id': '1',  # '0' = 发送, '1' = 接收
    'message_segment': {
        'type': 'text',  # 目前只支持 'text'
        'data': '实际的文本内容'
    },
    'timestamp': 1234567890  # Unix 时间戳
}
```

### 2. MessageBase 对象

**位置**: `src/shared/models/message.py`

```python
class MessageBase:
    message_id: str  # UUID
    user_id: str     # '0' 或 '1'
    user_nickname: str
    message_content: str
    timestamp: int
```

### 3. 气泡类型

```python
msg_type: Literal["received", "sent"]
```

- `"received"`: 接收的消息，爱丽丝蓝，左侧显示
- `"sent"`: 发送的消息，浅绿色，右侧显示

---

## 六、异步处理机制

### 1. 协议层（后台线程）

```python
# 在 ProtocolManager 的独立线程中运行
async def run_protocol_manager_async():
    await protocol_manager.initialize(protocol_configs)
    
    while True:
        await asyncio.sleep(1)  # 保持运行
```

### 2. 路由器（后台线程）

```python
async def message_handler(message):
    # 1. 异步保存到数据库
    await db_manager.save_message(message)
    
    # 2. 发送 Qt 信号（跨线程安全）
    signals_bus.message_received.emit(message_content)
```

### 3. UI 层（主线程）

```python
# 信号连接在主线程中执行
signals_bus.message_received.connect(self.show_message)

# 槽函数在主线程中执行
def show_message(self, text, msg_type="received"):
    self.bubble_manager.show_message(text, msg_type)
```

### 跨线程通信机制

- **从后台线程到主线程**: 使用 `pyqtSignal`
- **信号发送**: `signals_bus.message_received.emit(message_content)`
- **信号接收**: 主线程自动调用槽函数
- **线程安全**: PyQt5 信号机制保证跨线程安全

---

## 七、注意事项

### 1. 消息保存的时机

- 消息在 `router.message_handler()` 中第一次保存
- 在 `SpeechBubbleList.add_message()` 中可能再次保存（通过 `save_to_db` 参数控制）
- 避免重复保存应该设置 `save_to_db=False`

### 2. 消息类型的确定

- 在 `OpenAIProtocol._call_openai_api()` 中，`user_id` 设置为 `'1'` 表示接收
- 在 `DesktopPet.show_message()` 中，`msg_type` 默认为 `"received"`
- 两者对应关系：`user_id='1'` ↔ `msg_type='received'`

### 3. 气泡的自动清理

- 25秒后自动删除最旧的消息
- 超过屏幕高度1/3时自动删除最旧的消息
- 删除时使用淡出动画（500ms）

### 4. 数据库的使用

- 数据库操作都是异步的（`await`）
- 不会阻塞 UI 线程
- 保存失败会记录错误日志，但不影响消息显示

---

## 八、相关文件清单

| 文件路径 | 作用 |
|---------|------|
| `src/core/protocols/openai_protocol.py` | LLM API 调用，响应接收 |
| `src/core/router.py` | 消息处理器，数据库保存，信号发送 |
| `src/frontend/signals.py` | 全局信号总线 |
| `src/frontend/presentation/pet.py` | 主窗口，信号连接，消息显示入口 |
| `src/frontend/bubble_speech.py` | 气泡组件，气泡列表，气泡渲染 |
| `src/database/manager.py` | 数据库管理，消息保存 |

---

## 九、总结

消息从 LLM 返回后的处理流程是一个典型的**异步消息处理 + Qt 跨线程通信**架构：

1. **协议层**: 在后台线程中接收 LLM 响应
2. **路由器**: 处理消息，保存数据库，发送信号
3. **信号总线**: 跨线程安全地传递消息
4. **UI 层**: 接收信号，创建气泡，显示在主线程

整个流程**完全异步**，不会阻塞 UI 线程，用户体验流畅。