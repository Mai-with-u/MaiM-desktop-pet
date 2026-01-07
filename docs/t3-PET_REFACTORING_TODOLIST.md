# Pet.py 重构实施计划

## 📋 任务概述

根据 `docs/LIVE2D_REFACTORING_PLAN.md` 的规划，对 `src/frontend/pet.py` 进行架构重构，将单一职责违反的 600+ 行代码解耦为清晰的分层架构。

**当前问题：**
- ❌ DesktopPet 类承担过多职责（窗口管理、动画渲染、交互控制、系统托盘等）
- ❌ 代码耦合度高，难以维护和测试
- ❌ 动画渲染架构僵化，无法扩展到 Live2D
- ❌ 子窗口管理混乱

**重构目标：**
- ✅ 分层架构：UI 层、逻辑层、数据层分离
- ✅ 单一职责：每个类只负责一个功能
- ✅ 依赖倒置：高层模块不依赖低层模块
- ✅ 可扩展性：支持静态图片和 Live2D 渲染模式切换

---

## 🎯 重构阶段规划

### 阶段 1：准备工作（已完成）

#### ✅ 已完成项目
- [x] 创建新的目录结构
- [x] 准备配置文件模板（config.toml 已包含 database 配置）
- [x] 创建接口定义文件（src/frontend/core/render/interfaces.py）
- [x] 数据库模块已完成（src/database/）
- [x] 消息模型已完成（src/shared/models/message.py）

**目录结构现状：**
```
src/frontend/
├── core/                    # 核心业务层
│   ├── render/             # 渲染器
│   │   ├── __init__.py
│   │   ├── interfaces.py    # ✅ 渲染器接口
│   │   ├── static_renderer.py  # ✅ 静态渲染器
│   │   └── live2d_renderer.py  # ✅ Live2D 渲染器
│   ├── managers/           # 管理器
│   │   ├── __init__.py
│   │   ├── render_manager.py  # ✅ 渲染管理器
│   │   ├── event_manager.py   # ✅ 事件管理器
│   │   └── state_manager.py   # ✅ 状态管理器
│   ├── workers/            # 工作线程
│   │   ├── __init__.py
│   │   └── move_worker.py     # ✅ 移动工作线程
│   └── models/             # 模型
│       └── __init__.py
├── presentation/           # UI 层
│   ├── __init__.py
│   └── refactored_pet.py  # ✅ 重构后的主窗口（简化版）
├── data/                   # 数据层
│   └── __init__.py
└── components/             # 现有组件
    ├── bubble_menu.py      # ✅ 气泡菜单
    ├── bubble_speech.py    # ✅ 气泡显示
    ├── bubble_input.py     # ✅ 气泡输入
    ├── signals.py          # ✅ 信号总线
    └── ScreenshotSelector.py  # ✅ 截图选择器
```

---

### 阶段 2：数据库集成（进行中）

#### 任务 2.1：在 router.py 中添加接收消息存储
**文件：** `src/core/router.py`

**当前问题：**
- `message_handler` 函数接收消息后只发送到信号总线
- 没有将接收到的消息保存到数据库

**需要添加的功能：**
```python
async def message_handler(message):
    """
    消息处理函数 - 需要添加数据库存储逻辑
    """
    # 1. 记录日志
    logger.info(f"收到消息: {message}")
    
    # 2. 提取消息内容
    message_segment = message.get('message_segment', {})
    message_type = message_segment.get('type', {})
    
    # 3. 将消息保存到数据库
    # TODO: 调用 db_manager.save_message(message)
    
    # 4. 发送到信号总线
    if message_type == "text":
        message_content = str(message_segment.get('data', ""))
        signals_bus.message_received.emit(message_content)
    elif message_type == "seglist":
        seg_list = message_segment.get('data', [])
        for seg in seg_list:
            seg_type = seg.get('type')
            seg_data = seg.get('data')
            if seg_type == "text":
                text_content = str(seg_data)
                signals_bus.message_received.emit(text_content)
```

**任务清单：**
- [ ] 在 router.py 顶部导入 db_manager
- [ ] 在 message_handler 函数中添加数据库存储逻辑
- [ ] 处理存储失败的情况（使用 try-except）
- [ ] 添加日志记录
- [ ] 测试接收消息是否正确保存

---

#### 任务 2.2：在 chat.py 中添加发送消息存储
**文件：** `src/core/chat.py`

**当前问题：**
- `send` 方法发送消息后没有保存到数据库
- 需要在消息发送成功后保存到数据库

**需要添加的功能：**
```python
async def send(self, text: str, msg_type: str = "text", ...) -> bool:
    """
    发送消息 - 需要添加数据库存储逻辑
    """
    try:
        # 1. 创建消息
        message_base = self._create_message(...)
        
        # 2. 发送消息
        await router.send_message(message_base)
        
        # 3. 将消息保存到数据库
        # TODO: 调用 db_manager.save_message(message_base.to_dict())
        
        # 4. 记录日志
        logger.info(f"消息发送成功 - ID: {message_base.message_info.message_id}")
        
        return True
    except Exception as e:
        logger.error(f"消息发送失败: {e}")
        return False
```

**任务清单：**
- [ ] 在 chat.py 顶部导入 db_manager
- [ ] 在 send 方法中添加数据库存储逻辑
- [ ] 在 easy_to_send 方法中也添加存储逻辑
- [ ] 处理存储失败的情况
- [ ] 添加日志记录
- [ ] 测试发送消息是否正确保存

---

#### 任务 2.3：测试数据库功能
**任务清单：**
- [ ] 编写测试脚本测试接收消息存储
- [ ] 编写测试脚本测试发送消息存储
- [ ] 验证数据库中的消息数据格式
- [ ] 测试消息查询功能
- [ ] 测试消息搜索功能
- [ ] 编写测试报告

**测试脚本示例：**
```python
# tests/test_database_integration.py
import asyncio
from src.database import db_manager
from src.shared.models.message import MessageBase

async def test_save_and_query():
    # 初始化数据库
    await db_manager.initialize(db_type='sqlite', path='data/test.db')
    
    # 创建测试消息
    message = MessageBase.create_received_message("测试消息")
    
    # 保存消息
    result = await db_manager.save_message(message.to_dict())
    assert result == True
    
    # 查询消息
    messages = await db_manager.get_messages(limit=10)
    assert len(messages) > 0
    
    print("✓ 数据库集成测试通过")

if __name__ == "__main__":
    asyncio.run(test_save_and_query())
```

---

### 阶段 3：Pet.py 职责分离（核心重构）

#### 任务 3.1：分析并提取 TrayManager 职责
**文件：** `src/frontend/core/managers/tray_manager.py`（新建）

**当前 pet.py 中的代码：**
- `init_tray_icon()` 方法（约 50 行）
- `toggle_console()`, `show_console()`, `hide_console()` 方法（约 30 行）
- `update_terminal_menu_state()` 方法（约 10 行）
- `safe_quit()` 方法（约 5 行）
- `toggle_lock()`, `lock_window()`, `unlock_window()` 方法（约 20 行）
- `update_lock_menu_state()` 方法（约 10 行）
- `_load_tray_menu_style()` 方法（约 30 行）

**需要提取为：**
```python
class TrayManager:
    """系统托盘管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.tray_icon = None
        self.console_visible = True
        self.is_lock = False
        self.console_window = None
        
        self.init_tray_icon()
    
    def init_tray_icon(self):
        """初始化托盘图标"""
        # 移动 init_tray_icon 的代码
        pass
    
    def toggle_console(self):
        """切换终端显示"""
        # 移动 toggle_console 的代码
        pass
    
    def show_console(self):
        """显示终端"""
        # 移动 show_console 的代码
        pass
    
    def hide_console(self):
        """隐藏终端"""
        # 移动 hide_console 的代码
        pass
    
    def update_terminal_menu_state(self):
        """更新终端菜单状态"""
        # 移动 update_terminal_menu_state 的代码
        pass
    
    def toggle_lock(self):
        """切换锁定状态"""
        # 移动 toggle_lock 的代码
        pass
    
    def lock_window(self):
        """锁定窗口"""
        # 移动 lock_window 的代码
        pass
    
    def unlock_window(self):
        """解锁窗口"""
        # 移动 unlock_window 的代码
        pass
    
    def update_lock_menu_state(self):
        """更新锁定菜单状态"""
        # 移动 update_lock_menu_state 的代码
        pass
    
    def safe_quit(self):
        """安全退出"""
        # 移动 safe_quit 的代码
        pass
    
    def _load_tray_menu_style(self, menu):
        """加载托盘菜单样式"""
        # 移动 _load_tray_menu_style 的代码
        pass
```

**任务清单：**
- [ ] 创建 `src/frontend/core/managers/tray_manager.py`
- [ ] 提取托盘相关代码到 TrayManager
- [ ] 修改 pet.py 使用 TrayManager 实例
- [ ] 测试托盘功能（显示/隐藏、锁定/解锁）
- [ ] 测试终端控制功能
- [ ] 编写单元测试

---

#### 任务 3.2：分析并提取 BubbleSystem 职责
**文件：** `src/frontend/core/managers/bubble_system.py`（新建）

**当前 pet.py 中的代码：**
- 气泡初始化：`self.chat_bubbles = SpeechBubbleList(parent=self)`
- 输入框初始化：`self.bubble_input = BubbleInput(parent=self, ...)`
- `show_message()` 方法（约 10 行）
- `del_message_bubble()` 方法（约 5 行）
- `hide_all_bubble()` 方法（约 5 行）
- `show_chat_input()` 方法（约 5 行）
- `handle_user_input()` 方法（约 10 行）

**需要提取为：**
```python
class BubbleSystem:
    """气泡系统管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.chat_bubbles = SpeechBubbleList(parent=parent)
        self.bubble_input = BubbleInput(
            parent=parent, 
            on_send=self.handle_user_input
        )
        self.bubble_input.hide()
        
        # 订阅窗口移动事件
        signals_bus.position_changed.connect(self.on_position_changed)
    
    def show_message(self, text=None, msg_type="received", pixmap=None):
        """显示消息"""
        self.chat_bubbles.add_message(message=text, msg_type=msg_type, pixmap=pixmap)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(25000, self.del_first_message)
    
    def del_first_message(self):
        """删除第一条消息"""
        self.chat_bubbles.del_first_msg()
    
    def hide_all(self):
        """隐藏所有气泡"""
        self.bubble_input.hide()
        self.chat_bubbles.hide()
    
    def show_input(self):
        """显示输入框"""
        self.bubble_input.show()
        self.bubble_input.update_position()
        self.bubble_input.input_field.setFocus()
    
    def handle_user_input(self, text):
        """处理用户输入"""
        print(f"收到用户输入: {text}")
        self.show_message(text=text, msg_type="send")
        import asyncio
        from src.core.chat import chat_util
        asyncio.run(chat_util.easy_to_send(str(text), "text"))
    
    def on_position_changed(self, pos):
        """窗口移动时更新气泡位置"""
        if self.bubble_input.isVisible():
            self.bubble_input.update_position()
        for bubble in self.chat_bubbles._active_bubbles:
            if bubble.isVisible():
                self.chat_bubbles.update_position()
```

**任务清单：**
- [ ] 创建 `src/frontend/core/managers/bubble_system.py`
- [ ] 提取气泡相关代码到 BubbleSystem
- [ ] 修改 pet.py 使用 BubbleSystem 实例
- [ ] 测试消息显示功能
- [ ] 测试输入框功能
- [ ] 编写单元测试

---

#### 任务 3.3：分析并提取 ScreenshotSystem 职责
**文件：** `src/frontend/core/managers/screenshot_system.py`（新建）

**当前 pet.py 中的代码：**
- 截图快捷键初始化（约 5 行）
- `start_screenshot()` 方法（约 10 行）
- `handle_screenshot()` 方法（约 15 行）
- `PetScreenshotSelector` 类（约 10 行）
- `start_peeking()`, `stop_peeking()` 方法（约 20 行）
- `_on_peek_timer()` 方法（约 10 行）

**需要提取为：**
```python
class ScreenshotSystem:
    """截图系统管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.screenshot_selector = None
        self.is_peeking = False
        self.peek_timer = QTimer(parent)
        self.peek_timer.timeout.connect(self._on_peek_timer)
        
        # 初始化快捷键
        self.init_shortcuts()
    
    def init_shortcuts(self):
        """初始化截图快捷键"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        from config import config
        
        if config.Screenshot_shortcuts:
            shortcut = QShortcut(
                QKeySequence(config.Screenshot_shortcuts), 
                self.parent
            )
            shortcut.activated.connect(self.start_screenshot)
    
    def start_screenshot(self):
        """启动区域截图"""
        self.parent.hide()
        for chat_bubble in self.parent.bubble_system.chat_bubbles._active_bubbles:
            chat_bubble.hide()
        
        self.screenshot_selector = PetScreenshotSelector(self.parent, self)
        self.screenshot_selector.show()
    
    def handle_screenshot(self, pixmap):
        """处理截图结果"""
        self.parent.show()
        for chat_bubble in self.parent.bubble_system.chat_bubbles._active_bubbles:
            chat_bubble.show()
        
        print(pixmap)
        self.parent.bubble_system.show_message(pixmap=pixmap, msg_type="sent")
        
        from src.util.image_util import pixmap_to_base64
        from src.core.chat import chat_util
        base64_str = pixmap_to_base64(pixmap)
        import asyncio
        asyncio.run(chat_util.easy_to_send(base64_str, "image"))
    
    def start_peeking(self):
        """开始窥屏"""
        if not self.is_peeking:
            self.is_peeking = True
            import random
            random_time = random.randint(10, 30)
            self.peek_timer.start(random_time * 1000)
            self.parent.bubble_system.show_message("开始窥屏啦~", msg_type="received")
        else:
            self.stop_peeking()
    
    def stop_peeking(self):
        """停止窥屏"""
        if self.is_peeking:
            self.is_peeking = False
            self.peek_timer.stop()
            self.parent.bubble_system.show_message("停止窥屏啦~", msg_type="received")
    
    def _on_peek_timer(self):
        """定时器触发时的截图操作"""
        if self.is_peeking:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0)
            self.handle_screenshot(pixmap)


class PetScreenshotSelector(ScreenshotSelector):
    """自定义截图选择器"""
    
    def __init__(self, pet, screenshot_system):
        super().__init__()
        self.pet = pet
        self.screenshot_system = screenshot_system
    
    def on_screenshot_captured(self, pixmap):
        self.screenshot_system.handle_screenshot(pixmap)
```

**任务清单：**
- [ ] 创建 `src/frontend/core/managers/screenshot_system.py`
- [ ] 提取截图相关代码到 ScreenshotSystem
- [ ] 修改 pet.py 使用 ScreenshotSystem 实例
- [ ] 测试截图功能
- [ ] 测试窥屏功能
- [ ] 编写单元测试

---

#### 任务 3.4：简化 DesktopPet 类
**文件：** `src/frontend/presentation/refactored_pet.py`（已存在，需完善）

**目标：** 将 DesktopPet 类从 600+ 行简化到 200 行以内

**简化后的结构：**
```python
class RefactoredPet(QWidget):
    """重构后的桌面宠物主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化窗口
        self.init_window()
        
        # 初始化管理器
        self.init_managers()
        
        # 初始化子系统
        self.init_subsystems()
        
        # 初始化 UI
        self.init_ui()
        
        # 连接信号
        self.connect_signals()
    
    def init_window(self):
        """初始化窗口属性"""
        # 设置窗口标志
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口大小
        from config import scale_factor
        base_width = 400
        base_height = 600
        scaled_width = int(base_width * scale_factor)
        scaled_height = int(base_height * scale_factor)
        self.setFixedSize(scaled_width, scaled_height)
        
        # 设置初始位置
        screen_geo = QApplication.primaryScreen().availableGeometry()
        x = screen_geo.width() - self.width() - int(20 * scale_factor)
        y = screen_geo.height() - self.height() - int(80 * scale_factor)
        self.move(x, y)
    
    def init_managers(self):
        """初始化管理器"""
        from src.frontend.core.managers.render_manager import RenderManager
        from src.frontend.core.managers.event_manager import EventManager
        from src.frontend.core.managers.state_manager import StateManager
        
        self.render_manager = RenderManager(self)
        self.event_manager = EventManager(self)
        self.state_manager = StateManager(self)
    
    def init_subsystems(self):
        """初始化子系统"""
        from src.frontend.core.managers.tray_manager import TrayManager
        from src.frontend.core.managers.bubble_system import BubbleSystem
        from src.frontend.core.managers.screenshot_system import ScreenshotSystem
        
        self.tray_manager = TrayManager(self)
        self.bubble_system = BubbleSystem(self)
        self.screenshot_system = ScreenshotSystem(self)
    
    def init_ui(self):
        """初始化 UI"""
        # 渲染容器
        self.render_container = QWidget(self)
        self.render_container.setGeometry(0, 0, self.width(), self.height())
        
        # 将渲染管理器附加到容器
        self.render_manager.attach_to(self.render_container)
    
    def connect_signals(self):
        """连接信号"""
        from src.frontend.signals import signals_bus
        signals_bus.message_received.connect(self.bubble_system.show_message)
    
    # 事件委托
    def mousePressEvent(self, event):
        """鼠标按下 - 委托给事件管理器"""
        self.event_manager.handle_mouse_press(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放 - 委托给事件管理器"""
        self.event_manager.handle_mouse_release(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动 - 委托给事件管理器"""
        self.event_manager.handle_mouse_move(event)
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击 - 委托给事件管理器"""
        self.event_manager.handle_mouse_double_click(event)
    
    def contextMenuEvent(self, event):
        """右键菜单 - 委托给事件管理器"""
        self.event_manager.show_context_menu(event)
```

**任务清单：**
- [ ] 完善已存在的 refactored_pet.py
- [ ] 提取所有管理器调用
- [ ] 实现事件委托
- [ ] 测试窗口功能
- [ ] 测试所有子系统
- [ ] 性能测试

---

### 阶段 4：完善 EventManager

#### 任务 4.1：完善事件管理功能
**文件：** `src/frontend/core/managers/event_manager.py`（已存在）

**当前状态：** 已经实现了基本的事件处理框架

**需要完善的功能：**
- [ ] 完善鼠标事件处理
- [ ] 完善右键菜单创建
- [ ] 添加缩放控制菜单
- [ ] 添加窥屏菜单项
- [ ] 测试所有事件处理
- [ ] 编写单元测试

**菜单项列表：**
```python
actions = [
    ("🐾 隐藏", self.parent.hide),
    ("✏️ 聊聊天", self.parent.bubble_system.show_input),
    ("📸 截图", self.parent.screenshot_system.start_screenshot),
    ("👀 麦麦窥屏", self.parent.screenshot_system.start_peeking),
]
```

---

### 阶段 5：完善 StateManager

#### 任务 5.1：完善状态管理功能
**文件：** `src/frontend/core/managers/state_manager.py`（已存在）

**当前状态：** 已经实现了基本的状态管理框架

**需要完善的功能：**
- [ ] 完善窗口锁定/解锁状态管理
- [ ] 完善终端显示/隐藏状态管理
- [ ] 添加窗口显示/隐藏状态管理
- [ ] 添加状态持久化
- [ ] 测试所有状态管理
- [ ] 编写单元测试

---

### 阶段 6：测试和文档

#### 任务 6.1：集成测试
**任务清单：**
- [ ] 测试完整的消息流程（接收→显示→发送→存储）
- [ ] 测试所有窗口交互（拖拽、双击、右键菜单）
- [ ] 测试所有子系统（托盘、气泡、截图）
- [ ] 测试渲染模式切换
- [ ] 测试状态管理
- [ ] 性能测试（内存占用、CPU 占用）
- [ ] 长时间运行测试

#### 任务 6.2：编写文档
**任务清单：**
- [ ] 更新 `docs/README.md`
- [ ] 编写架构文档
- [ ] 编写 API 文档
- [ ] 编写使用指南
- [ ] 编写迁移指南
- [ ] 更新 CHANGELOG

#### 任务 6.3：清理和优化
**任务清单：**
- [ ] 删除未使用的代码
- [ ] 优化导入语句
- [ ] 统一代码风格
- [ ] 添加类型注解
- [ ] 添加文档字符串
- [ ] 性能优化

---

### 阶段 7：发布

#### 任务 7.1：版本发布
**任务清单：**
- [ ] 更新版本号
- [ ] 创建发布标签
- [ ] 编写发布说明
- [ ] 部署到生产环境
- [ ] 监控运行状态
- [ ] 收集用户反馈

---

## 📊 进度追踪

### 完成情况统计
- ✅ 已完成：0 / 60
- 🔄 进行中：0 / 60
- ⏳ 待开始：60 / 60

### 各阶段进度
- 阶段 1（准备工作）：100% ✅
- 阶段 2（数据库集成）：0% ⏳
- 阶段 3（职责分离）：0% ⏳
- 阶段 4（EventManager）：0% ⏳
- 阶段 5（StateManager）：0% ⏳
- 阶段 6（测试和文档）：0% ⏳
- 阶段 7（发布）：0% ⏳

---

## 🔧 技术债务清理

### 代码质量改进
- [ ] 统一导入顺序（PEP 8）
- [ ] 添加类型注解（Type Hints）
- [ ] 完善文档字符串（Docstrings）
- [ ] 添加单元测试覆盖（目标 >80%）
- [ ] 代码格式化（Black, isort）

### 性能优化
- [ ] 优化消息存储性能
- [ ] 优化渲染性能
- [ ] 优化内存占用
- [ ] 减少不必要的信号连接
- [ ] 优化工作线程

---

## 📝 注意事项

### 重要提醒
1. **保持向后兼容**：重构过程中确保旧版本 `pet.py` 仍然可用
2. **逐步迁移**：不要一次性修改所有代码，分步骤进行
3. **充分测试**：每完成一个任务都要进行测试
4. **文档同步**：代码和文档要同步更新
5. **备份代码**：重构前做好代码备份

### 风险控制
- 高风险：核心架构重构
- 中风险：数据库集成
- 低风险：代码提取和优化

### 回滚策略
如果重构遇到严重问题，可以：
1. 回退到上一个稳定版本
2. 使用 main.py 中的 `USE_REFACTORED_ARCHITECTURE = False` 切换回旧架构
3. 保留已完成的模块，逐步修复问题

---

## 🎯 成功标准

### 必须完成
- ✅ 所有任务完成
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试全部通过
- ✅ 文档完整
- ✅ 无已知 Bug

### 期望完成
- ⭐ 性能提升 > 20%
- ⭐ 代码量减少 > 30%
- ⭐ 可维护性显著提升
- ⭐ 用户体验改善

---

**文档版本：** v1.0  
**创建日期：** 2026-01-08  
**最后更新：** 2026-01-08
