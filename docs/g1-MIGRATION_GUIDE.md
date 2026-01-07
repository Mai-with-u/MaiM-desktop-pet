# 架构重构迁移指南

## 概述

本文档指导如何从旧的 `pet.py` 迁移到新的重构架构。

**文档版本：** v1.0  
**创建日期：** 2026-01-07

---

## 一、架构对比

### 1.1 旧架构

```
src/frontend/pet.py (单一文件，约 600+ 行)
├── DesktopPet 类
│   ├── UI 初始化
│   ├── 托盘图标管理
│   ├── 气泡系统集成
│   ├── 截图功能
│   ├── 移动管理 (MoveWorker)
│   ├── 交互事件处理
│   └── 静态图片渲染
```

**问题：**
- 单一类承担过多职责
- 代码耦合度高
- 难以维护和测试
- 无法扩展到 Live2D

### 1.2 新架构

```
src/frontend/
├── core/                          # 核心业务层
│   ├── render/                     # 渲染模块
│   │   ├── interfaces.py          # 渲染器接口
│   │   ├── static_renderer.py     # 静态图片渲染器
│   │   └── live2d_renderer.py     # Live2D 渲染器
│   ├── managers/                   # 管理器模块
│   │   ├── render_manager.py      # 渲染管理器
│   │   ├── event_manager.py       # 事件管理器
│   │   └── state_manager.py       # 状态管理器
│   └── workers/                    # 工作线程
│       └── move_worker.py         # 移动工作线程
├── presentation/                   # UI 层
│   └── refactored_pet.py         # 重构后的主窗口
└── components/                     # 现有组件（保持不变）
    ├── bubble_menu.py
    ├── bubble_speech.py
    ├── bubble_input.py
    └── ScreenshotSelector.py
```

**优势：**
- 清晰的分层架构
- 单一职责原则
- 易于维护和测试
- 支持动态切换渲染模式

---

## 二、迁移步骤

### 步骤 1：备份现有代码

```bash
# 创建备份
cp src/frontend/pet.py src/frontend/pet.py.backup
cp config.toml config.toml.backup

# 或者使用 git
git add .
git commit -m "备份：重构前的代码"
```

### 步骤 2：更新配置文件

在 `config.toml` 中添加新的配置项：

```toml
[render]
# 渲染模式: static | live2d
mode = "static"
# 是否支持运行时切换
allow_switch = true

[live2d]
# 是否启用 Live2D
enabled = false
# 模型文件路径（.model3.json）
model_path = "./live2d/models/maotai/maotai.model3.json"
```

### 步骤 3：测试新架构

创建测试脚本 `test_refactored.py`：

```python
"""
测试重构后的架构
"""

import sys
from PyQt5.QtWidgets import QApplication

# 使用重构后的宠物
from src.frontend.presentation.refactored_pet import refactored_pet

def main():
    app = QApplication(sys.argv)
    
    # 显示宠物
    refactored_pet.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

运行测试：

```bash
python test_refactored.py
```

### 步骤 4：功能验证清单

- [ ] 窗口正常显示
- [ ] 可以拖动窗口
- [ ] 双击触发交互
- [ ] 右键菜单正常
- [ ] 聊天输入框正常
- [ ] 消息气泡正常
- [ ] 截图功能正常
- [ ] 托盘图标正常
- [ ] 锁定/解锁功能正常
- [ ] 终端显示/隐藏正常

### 步骤 5：逐步替换

#### 5.1 替换主窗口导入

**旧代码：**
```python
from src.frontend.pet import DesktopPet
```

**新代码：**
```python
from src.frontend.presentation.refactored_pet import RefactoredDesktopPet
```

#### 5.2 替换实例创建

**旧代码：**
```python
chat_pet = DesktopPet()
```

**新代码：**
```python
chat_pet = RefactoredDesktopPet()
```

#### 5.3 更新 main.py

**旧代码：**
```python
from src.frontend.pet import chat_pet

if __name__ == "__main__":
    chat_pet.show()
    sys.exit(app.exec_())
```

**新代码：**
```python
from src.frontend.presentation.refactored_pet import refactored_pet

if __name__ == "__main__":
    refactored_pet.show()
    sys.exit(app.exec_())
```

---

## 三、API 变更

### 3.1 保持兼容的 API

以下 API 保持不变，无需修改：

```python
# 显示消息
pet.show_message(text="你好", type="received")
pet.show_message(pixmap=qpixmap, type="sent")

# 处理用户输入
pet.handle_user_input("用户消息")

# 安全退出
pet.safe_quit()
```

### 3.2 新增的 API

```python
# 渲染管理器
pet.render_manager.switch_mode("live2d")  # 切换到 Live2D
pet.render_manager.switch_mode("static")   # 切换到静态图片
pet.render_manager.set_animation_state("happy")  # 设置动画状态
pet.render_manager.set_expression("happy")       # 设置表情

# 状态管理器
pet.state_manager.lock_window()    # 锁定窗口
pet.state_manager.unlock_window()  # 解锁窗口
pet.state_manager.toggle_lock()    # 切换锁定状态
pet.state_manager.show_console()   # 显示终端
pet.state_manager.hide_console()   # 隐藏终端
```

### 3.3 已删除的 API

以下 API 已被管理器替代：

```python
# ❌ 旧 API（已删除）
pet.is_lock
pet.console_window
pet.toggle_lock()
pet.hide_console()
pet.show_console()

# ✅ 新 API（使用状态管理器）
pet.state_manager.is_locked()
pet.state_manager.toggle_lock()
pet.state_manager.hide_console()
pet.state_manager.show_console()
```

---

## 四、自定义扩展

### 4.1 添加新的渲染器

如果需要添加新的渲染器（例如 GIF、视频等）：

1. 创建新的渲染器类：

```python
# src/frontend/core/render/gif_renderer.py

from .interfaces import IRenderer
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QMovie

class GifRenderer(IRenderer):
    def __init__(self, gif_path):
        self.gif_path = gif_path
        self.label = None
        self.movie = None
    
    def initialize(self):
        """初始化"""
        print("初始化 GIF 渲染器")
    
    def attach(self, parent):
        """附加到父控件"""
        self.label = QLabel(parent)
        self.movie = QMovie(self.gif_path)
        self.label.setMovie(self.movie)
        self.movie.start()
        self.label.show()
    
    def cleanup(self):
        """清理"""
        if self.movie:
            self.movie.stop()
        if self.label:
            self.label.deleteLater()
    
    def set_animation_state(self, state):
        """设置动画状态"""
        pass
    
    def set_expression(self, expression):
        """设置表情"""
        pass
    
    def on_mouse_move(self, x, y):
        """鼠标移动回调"""
        pass
```

2. 在 `render/__init__.py` 中导出：

```python
from .gif_renderer import GifRenderer

__all__ = [
    'IRenderer',
    'StaticRenderer',
    'Live2DRenderer',
    'GifRenderer'
]
```

3. 在 `render_manager.py` 中添加支持：

```python
from .gif_renderer import GifRenderer

def create_renderer(self):
    """创建渲染器"""
    if self.use_live2d and self.live2d_model_path:
        # ... Live2D 逻辑
    elif self.use_gif and self.gif_path:
        self.renderer = GifRenderer(self.gif_path)
        self.current_mode = "gif"
    else:
        self.renderer = StaticRenderer()
        self.current_mode = "static"
```

### 4.2 添加新的状态

如果需要添加新的状态管理：

```python
# 在 StateManager 中添加新状态

class StateManager(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self._is_muted = False  # 新状态：静音
    
    def is_muted(self) -> bool:
        """是否静音"""
        return self._is_muted
    
    def toggle_mute(self):
        """切换静音状态"""
        self._is_muted = not self._is_muted
        # 发送信号通知其他组件
        signals_bus.mute_state_changed.emit(self._is_muted)
```

---

## 五、常见问题

### Q1: 迁移后程序无法启动

**可能原因：**
- 导入路径错误
- 缺少依赖库
- 配置文件格式错误

**解决方法：**
```python
# 检查导入
from src.frontend.presentation.refactored_pet import RefactoredDesktopPet

# 检查配置文件
import tomli
with open("config.toml", "rb") as f:
    config = tomli.load(f)
    print(config)
```

### Q2: 气泡位置不正确

**可能原因：**
- 气泡管理器未正确初始化
- 位置更新信号未连接

**解决方法：**
```python
# 确保在 init_subsystems 中正确初始化
self.chat_bubbles = SpeechBubbleList(parent=self)
self.bubble_input = BubbleInput(parent=self, on_send=self.handle_user_input)

# 确保连接位置变化信号
signals_bus.position_changed.connect(self._on_position_changed)
```

### Q3: 事件处理无响应

**可能原因：**
- 事件管理器未正确委托
- 管理器之间的引用未设置

**解决方法：**
```python
# 确保设置管理器之间的引用
self.event_manager.set_managers(
    render_manager=self.render_manager,
    state_manager=self.state_manager,
    bubble_manager=self.bubble_manager,
    screenshot_manager=self.screenshot_manager
)
```

### Q4: 渲染器切换失败

**可能原因：**
- Live2D 库未安装
- 模型文件路径错误
- 渲染器未正确清理

**解决方法：**
```python
# 检查 Live2D 是否可用
from src.frontend.core.render.live2d_renderer import Live2DRenderer
print(f"Live2D 可用: {Live2DRenderer.is_available()}")

# 检查模型文件
import os
model_path = "./live2d/models/maotai/maotai.model3.json"
print(f"模型文件存在: {os.path.exists(model_path)}")
```

---

## 六、回滚方案

如果迁移过程中遇到问题，可以快速回滚到旧版本：

### 6.1 使用备份文件

```bash
# 恢复旧代码
cp src/frontend/pet.py.backup src/frontend/pet.py
cp config.toml.backup config.toml

# 恢复 main.py
git checkout HEAD -- main.py
```

### 6.2 使用 Git 回滚

```bash
# 回滚到重构前的提交
git log --oneline  # 查看提交历史
git checkout <commit-hash>  # 切换到指定提交

# 或者回滚上一个提交
git reset --hard HEAD~1
```

### 6.3 混合使用

如果新架构有问题，可以暂时使用旧架构：

```python
# 在 main.py 中选择使用哪个版本
USE_REFACTORED = False  # 设置为 False 使用旧版本

if USE_REFACTORED:
    from src.frontend.presentation.refactored_pet import refactored_pet
    pet = refactored_pet
else:
    from src.frontend.pet import DesktopPet
    pet = DesktopPet()
```

---

## 七、最佳实践

### 7.1 使用管理器而不是直接访问组件

**❌ 不推荐：**
```python
# 直接访问组件
self.chat_bubbles.add_message("消息")
```

**✅ 推荐：**
```python
# 通过管理器访问
self.bubble_manager.show_message("消息")
```

### 7.2 使用信号进行组件通信

**❌ 不推荐：**
```python
# 直接调用方法
self.parent.screenshot_manager.start_screenshot()
```

**✅ 推荐：**
```python
# 使用信号
signals_bus.screenshot_requested.emit()
```

### 7.3 保持单一职责

**❌ 不推荐：**
```python
class DesktopPet:
    def handle_event(self, event):
        # 事件处理
        if event.button() == Qt.LeftButton:
            self.move_window()
            self.update_render()
            self.save_state()
        # ... 混合了多个职责
```

**✅ 推荐：**
```python
class EventManager:
    def handle_event(self, event):
        if event.button() == Qt.LeftButton:
            self.event_manager.handle_mouse_press(event)

class RenderManager:
    def update_render(self):
        # 渲染逻辑
        pass

class StateManager:
    def save_state(self):
        # 状态保存逻辑
        pass
```

---

## 八、后续优化

### 8.1 性能优化

- [ ] 实现渲染器资源缓存
- [ ] 优化事件处理频率
- [ ] 减少不必要的重绘

### 8.2 功能增强

- [ ] 实现渲染模式热切换
- [ ] 添加更多动画效果
- [ ] 支持自定义主题

### 8.3 测试完善

- [ ] 添加单元测试
- [ ] 添加集成测试
- [ ] 添加性能测试

---

## 九、总结

### 迁移收益

| 方面 | 改善 |
|------|------|
| 可维护性 | ⭐⭐⭐⭐⭐ 显著提升 |
| 可扩展性 | ⭐⭐⭐⭐⭐ 显著提升 |
| 代码质量 | ⭐⭐⭐⭐⭐ 显著提升 |
| 可测试性 | ⭐⭐⭐⭐ 中等提升 |

### 关键要点

1. **备份代码**：迁移前务必备份
2. **逐步验证**：每一步都要测试
3. **保持兼容**：尽量保持 API 兼容
4. **文档同步**：及时更新文档
5. **收集反馈**：及时处理问题

### 下一步

- [ ] 完成迁移测试
- [ ] 收集用户反馈
- [ ] 修复发现的问题
- [ ] 优化性能
- [ ] 准备 Live2D 集成

---

**文档结束**
