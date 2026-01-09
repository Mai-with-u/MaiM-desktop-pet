# pet.py 解构重构任务清单

**创建日期：** 2026-01-10  
**最后更新：** 2026-01-10

---

## 一、当前代码分析

### 1.1 代码统计

| 指标 | 数值 |
|------|------|
| 总行数 | ~400 行 |
| 类数量 | 2 个（DesktopPet, PetScreenshotSelector） |
| 方法数量 | ~30 个 |
| 职责数量 | 10+ 个 |

### 1.2 当前职责清单

`DesktopPet` 类承担了以下职责：

1. **UI 初始化** - 窗口属性设置、大小计算、位置设置
2. **托盘图标管理** - 托盘菜单创建、终端控制、锁定控制
3. **气泡系统集成** - 消息气泡、输入气泡、右键菜单
4. **截图功能** - 区域截图、截图处理、回调
5. **移动管理** - 鼠标拖动、工作线程、位置同步
6. **交互事件处理** - 鼠标点击、双击、右键菜单
7. **窗口锁定** - 锁定/解锁、状态管理
8. **窥屏功能** - 定时截图、窥屏控制
9. **缩放功能** - 动态缩放、配置更新
10. **动画渲染** - 静态图片显示（当前仅支持静态）

### 1.3 外部依赖

```
├── PyQt5 (UI 框架)
│   ├── QtWidgets
│   ├── QtCore
│   └── QtGui
├── src.core.chat (聊天工具)
├── src.frontend.signals (信号总线)
├── src.frontend.bubble_* (气泡组件)
│   ├── bubble_menu.py
│   ├── bubble_speech.py
│   └── bubble_input.py
├── src.frontend.ScreenshotSelector (截图组件)
├── src.util.logger (日志)
├── src.util.image_util (图片工具)
├── config (配置加载)
├── asyncio (异步)
├── platform (平台检测)
├── tomli/tomli_w (配置文件读写)
└── win32gui (Windows 特定功能)
```

---

## 二、重构目标

### 2.1 核心目标

1. **职责分离** - 将 10+ 个职责拆分为独立的管理器
2. **代码解耦** - 减少类之间的依赖关系
3. **可扩展性** - 支持未来添加 Live2D 等高级功能
4. **可测试性** - 提高单元测试覆盖率
5. **可维护性** - 降低代码复杂度，提高可读性

### 2.2 架构设计

```
DesktopPet (主窗口 - 简化版)
├── RenderManager (渲染管理器)
│   ├── StaticRenderer (静态图片渲染器)
│   └── Live2DRenderer (Live2D 渲染器 - 未来)
├── EventManager (事件管理器)
│   ├── 鼠标事件处理
│   ├── 键盘事件处理
│   └── 事件分发
├── StateManager (状态管理器)
│   ├── 窗口状态（锁定/解锁）
│   ├── 终端状态
│   └── 窥屏状态
├── BubbleSystem (气泡系统)
│   ├── 消息气泡管理
│   ├── 输入气泡管理
│   └── 右键菜单
├── TrayManager (托盘管理器)
│   ├── 托盘图标
│   ├── 托盘菜单
│   └── 状态同步
├── ScreenshotSystem (截图系统)
│   ├── 区域截图
│   ├── 截图处理
│   └── 回调管理
└── ScaleManager (缩放管理器)
    ├── 动态缩放
    └── 配置更新
```

---

## 三、重构实施计划

### 阶段 0：准备工作（预计 1-2 天）

#### 任务 0.1：备份现有代码
- [ ] 创建 `src/frontend/pet.py.backup` 备份文件
- [ ] 创建 `git commit` 保存当前状态
- [ ] 编写回归测试用例

#### 任务 0.2：创建新的目录结构
```
src/frontend/
├── core/                    # 核心业务层
│   ├── __init__.py
│   ├── managers/            # 管理器
│   │   ├── __init__.py
│   │   ├── render_manager.py
│   │   ├── event_manager.py
│   │   ├── state_manager.py
│   │   ├── tray_manager.py
│   │   ├── bubble_system.py
│   │   ├── screenshot_system.py
│   │   └── scale_manager.py
│   └── render/              # 渲染器
│       ├── __init__.py
│       ├── interfaces.py
│       ├── static_renderer.py
│       └── live2d_renderer.py (未来)
├── presentation/            # UI 层
│   ├── __init__.py
│   └── refactored_pet.py
├── components/              # 现有组件（保持不变）
│   ├── bubble_menu.py
│   ├── bubble_speech.py
│   ├── bubble_input.py
│   └── ScreenshotSelector.py
└── legacy/                  # 旧代码（保留）
    └── pet.py
```

#### 任务 0.3：准备基础框架
- [ ] 创建 `core/managers/__init__.py`
- [ ] 创建 `core/render/__init__.py`
- [ ] 创建 `presentation/__init__.py`
- [ ] 编写接口定义文件

#### 任务 0.4：编写单元测试框架
- [ ] 安装 pytest
- [ ] 创建 `tests/` 目录结构
- [ ] 编写测试配置文件 `pytest.ini`

---

### 阶段 1：渲染层重构（预计 2-3 天）

#### 任务 1.1：创建渲染器接口
**文件：** `src/frontend/core/render/interfaces.py`

**任务清单：**
- [ ] 定义 `IRenderer` 抽象基类
  - [ ] `initialize()` - 初始化渲染器
  - [ ] `attach(parent)` - 附加到父控件
  - [ ] `cleanup()` - 清理资源
  - [ ] `set_animation_state(state)` - 设置动画状态
  - [ ] `set_expression(expression)` - 设置表情
  - [ ] `on_mouse_move(x, y)` - 鼠标移动回调
  - [ ] `set_scale(scale)` - 设置缩放比例
  - [ ] `set_offset(x, y)` - 设置位置偏移

**验收标准：**
- 接口定义清晰
- 所有方法都有文档字符串
- 通过类型检查

#### 任务 1.2：实现静态图片渲染器
**文件：** `src/frontend/core/render/static_renderer.py`

**任务清单：**
- [ ] 实现 `StaticRenderer` 类
  - [ ] `__init__(image_path, scale_factor)`
  - [ ] `initialize()` - 加载图片
  - [ ] `attach(parent)` - 创建 QLabel 并附加
  - [ ] `cleanup()` - 清理 QLabel
  - [ ] `set_scale(scale)` - 更新缩放
  - [ ] `set_offset(x, y)` - 更新偏移
  - [ ] 其他方法返回空实现或警告

**验收标准：**
- 可以正确显示静态图片
- 支持缩放和偏移
- 资源正确清理

#### 任务 1.3：实现渲染管理器
**文件：** `src/frontend/core/managers/render_manager.py`

**任务清单：**
- [ ] 实现 `RenderManager` 类
  - [ ] `__init__(parent, config)`
  - [ ] `load_config()` - 加载配置
  - [ ] `create_renderer()` - 创建渲染器
  - [ ] `attach_to(parent)` - 附加到父控件
  - [ ] `switch_mode(mode)` - 切换渲染模式
  - [ ] `set_animation_state(state)` - 设置动画状态
  - [ ] `set_expression(expression)` - 设置表情
  - [ ] `handle_mouse_move(x, y)` - 处理鼠标移动
  - [ ] `set_scale(scale)` - 设置缩放
  - [ ] `set_offset(x, y)` - 设置偏移

**验收标准：**
- 可以正确创建和管理渲染器
- 支持模式切换（静态/Live2D）
- 配置加载正确

#### 任务 1.4：编写渲染层单元测试
**文件：** `tests/test_render_layer.py`

**任务清单：**
- [ ] 测试 `IRenderer` 接口
- [ ] 测试 `StaticRenderer` 功能
  - [ ] 初始化测试
  - [ ] 缩放测试
  - [ ] 偏移测试
  - [ ] 资源清理测试
- [ ] 测试 `RenderManager` 功能
  - [ ] 创建渲染器测试
  - [ ] 模式切换测试
  - [ ] 配置加载测试

**验收标准：**
- 测试覆盖率 > 90%
- 所有测试通过

---

### 阶段 2：管理器重构（预计 3-4 天）

#### 任务 2.1：实现状态管理器
**文件：** `src/frontend/core/managers/state_manager.py`

**任务清单：**
- [ ] 实现 `StateManager` 类
  - [ ] `__init__(parent)`
  - [ ] `is_locked()` - 检查锁定状态
  - [ ] `is_visible()` - 检查可见状态
  - [ ] `is_console_visible()` - 检查终端状态
  - [ ] `is_peeking()` - 检查窥屏状态
  - [ ] `lock_window()` - 锁定窗口
  - [ ] `unlock_window()` - 解锁窗口
  - [ ] `toggle_lock()` - 切换锁定
  - [ ] `show_console()` - 显示终端
  - [ ] `hide_console()` - 隐藏终端
  - [ ] `toggle_console()` - 切换终端
  - [ ] `start_peeking()` - 开始窥屏
  - [ ] `stop_peeking()` - 停止窥屏
  - [ ] `toggle_peeking()` - 切换窥屏

**验收标准：**
- 所有状态管理正确
- 窗口属性切换正确
- 终端控制正确（Windows 平台）
- 窥屏功能正常

#### 任务 2.2：实现事件管理器
**文件：** `src/frontend/core/managers/event_manager.py`

**任务清单：**
- [ ] 实现 `EventManager` 类
  - [ ] `__init__(parent, render_manager, state_manager)`
  - [ ] `handle_mouse_press(event)` - 鼠标按下
  - [ ] `handle_mouse_release(event)` - 鼠标释放
  - [ ] `handle_mouse_move(event)` - 鼠标移动
  - [ ] `handle_mouse_double_click(event)` - 鼠标双击
  - [ ] `handle_context_menu(event)` - 右键菜单
  - [ ] `start_move_worker()` - 启动移动线程
  - [ ] `stop_move_worker()` - 停止移动线程

**迁移清单：**
- [ ] 迁移 `mousePressEvent` 逻辑
- [ ] 迁移 `mouseReleaseEvent` 逻辑
- [ ] 迁移 `mouseMoveEvent` 逻辑
- [ ] 迁移 `mouseDoubleClickEvent` 逻辑
- [ ] 迁移 `contextMenuEvent` 逻辑
- [ ] 迁移 `MoveWorker` 线程逻辑

**验收标准：**
- 所有事件处理正确
- 鼠标拖动流畅
- 双击功能正常
- 右键菜单正常显示

#### 任务 2.3：实现托盘管理器
**文件：** `src/frontend/core/managers/tray_manager.py`

**任务清单：**
- [ ] 实现 `TrayManager` 类
  - [ ] `__init__(parent)`
  - [ ] `init_tray_icon()` - 初始化托盘图标
  - [ ] `create_tray_menu()` - 创建托盘菜单
  - [ ] `update_terminal_menu_state()` - 更新终端按钮
  - [ ] `update_lock_menu_state()` - 更新锁定按钮
  - [ ] `toggle_console()` - 切换终端显示
  - [ ] `toggle_lock()` - 切换锁定状态
  - [ ] `show_pet()` - 显示宠物
  - [ ] `hide_pet()` - 隐藏宠物
  - [ ] `safe_quit()` - 安全退出

**迁移清单：**
- [ ] 迁移 `init_tray_icon` 逻辑
- [ ] 迁移终端控制逻辑
- [ ] 迁移锁定控制逻辑
- [ ] 迁移退出逻辑

**验收标准：**
- 托盘图标正常显示
- 托盘菜单功能正常
- 终端控制正常
- 锁定控制正常

#### 任务 2.4：实现气泡系统
**文件：** `src/frontend/core/managers/bubble_system.py`

**任务清单：**
- [ ] 实现 `BubbleSystem` 类
  - [ ] `__init__(parent)`
  - [ ] `show_message(text, type, pixmap)` - 显示消息
  - [ ] `show_input()` - 显示输入框
  - [ ] `hide_all()` - 隐藏所有气泡
  - [ ] `update_position()` - 更新气泡位置
  - [ ] `handle_user_input(text)` - 处理用户输入

**迁移清单：**
- [ ] 迁移 `chat_bubbles` 管理
- [ ] 迁移 `bubble_menu` 管理
- [ ] 迁移 `bubble_input` 管理
- [ ] 迁移 `show_message` 逻辑
- [ ] 迁移 `show_chat_input` 逻辑
- [ ] 迁移 `handle_user_input` 逻辑
- [ ] 迁移右键菜单创建逻辑

**验收标准：**
- 消息气泡正常显示
- 输入气泡正常显示
- 右键菜单正常显示
- 用户输入处理正确
- 位置同步正确

#### 任务 2.5：实现截图系统
**文件：** `src/frontend/core/managers/screenshot_system.py`

**任务清单：**
- [ ] 实现 `ScreenshotSystem` 类
  - [ ] `__init__(parent, bubble_system)`
  - [ ] `start_screenshot()` - 启动截图
  - [ ] `handle_screenshot(pixmap)` - 处理截图结果
  - [ ] `on_screenshot_captured(pixmap)` - 截图回调

**迁移清单：**
- [ ] 迁移 `start_screenshot` 逻辑
- [ ] 迁移 `handle_screenshot` 逻辑
- [ ] 迁移 `PetScreenshotSelector` 逻辑
- [ ] 迁移窥屏逻辑

**验收标准：**
- 区域截图功能正常
- 截图显示正常
- 窥屏功能正常
- 截图发送正常

#### 任务 2.6：实现缩放管理器
**文件：** `src/frontend/core/managers/scale_manager.py`

**任务清单：**
- [ ] 实现 `ScaleManager` 类
  - [ ] `__init__(parent, render_manager)`
  - [ ] `change_scale(new_scale)` - 改变缩放倍率
  - [ ] `get_current_scale()` - 获取当前缩放
  - [ ] `_update_config(new_scale)` - 更新配置文件

**迁移清单：**
- [ ] 迁移 `change_scale` 逻辑
- [ ] 迁移配置文件更新逻辑

**验收标准：**
- 缩放功能正常
- 配置文件更新正确
- 缩放菜单显示正确

#### 任务 2.7：编写管理器单元测试
**文件：** `tests/test_managers.py`

**任务清单：**
- [ ] 测试 `StateManager` 功能
- [ ] 测试 `EventManager` 功能
- [ ] 测试 `TrayManager` 功能
- [ ] 测试 `BubbleSystem` 功能
- [ ] 测试 `ScreenshotSystem` 功能
- [ ] 测试 `ScaleManager` 功能

**验收标准：**
- 测试覆盖率 > 80%
- 所有测试通过

---

### 阶段 3：主窗口重构（预计 2-3 天）

#### 任务 3.1：创建简化版主窗口
**文件：** `src/frontend/presentation/refactored_pet.py`

**任务清单：**
- [ ] 实现 `DesktopPet` 类（重构版）
  - [ ] `__init__()` - 初始化
  - [ ] `init_window()` - 初始化窗口属性
  - [ ] `init_managers()` - 初始化管理器
  - [ ] `init_ui()` - 初始化 UI 布局
  - [ ] `show()` - 显示窗口
  - [ ] `hide()` - 隐藏窗口

**事件委托：**
- [ ] `mousePressEvent(event)` - 委托给 EventManager
- [ ] `mouseReleaseEvent(event)` - 委托给 EventManager
- [ ] `mouseMoveEvent(event)` - 委托给 EventManager
- [ ] `mouseDoubleClickEvent(event)` - 委托给 EventManager
- [ ] `contextMenuEvent(event)` - 委托给 EventManager

**信号连接：**
- [ ] 连接 `signals_bus.message_received` 到 `bubble_system.show_message`
- [ ] 连接 `signals_bus.position_changed` 到 `_on_position_changed`
- [ ] 连接快捷键到 `screenshot_system.start_screenshot`

**验收标准：**
- 主窗口正常显示
- 所有事件正确委托
- 所有信号正确连接

#### 任务 3.2：更新主入口文件
**文件：** `main.py`

**任务清单：**
- [ ] 更新导入路径
  - [ ] 从 `src/frontend/pet.py` 改为 `src/frontend/presentation/refactored_pet.py`
- [ ] 更新实例化代码
- [ ] 添加配置验证

**验收标准：**
- 程序正常启动
- 所有功能正常

#### 任务 3.3：编写集成测试
**文件：** `tests/test_integration.py`

**任务清单：**
- [ ] 测试主窗口初始化
- [ ] 测试管理器集成
- [ ] 测试事件流转
- [ ] 测试信号连接
- [ ] 测试完整功能流程

**验收标准：**
- 所有集成测试通过
- 功能回归测试通过

---

### 阶段 4：清理和优化（预计 1-2 天）

#### 任务 4.1：清理旧代码
**任务清单：**
- [ ] 移动 `pet.py` 到 `legacy/` 目录
- [ ] 更新所有导入引用
- [ ] 清理未使用的代码
- [ ] 更新文档

#### 任务 4.2：性能优化
**任务清单：**
- [ ] 分析性能瓶颈
- [ ] 优化渲染性能
- [ ] 优化事件处理
- [ ] 优化资源管理
- [ ] 减少内存占用

**验收标准：**
- CPU 占用 < 15%
- 内存占用 < 100MB
- 帧率稳定在 60FPS

#### 任务 4.3：完善文档
**任务清单：**
- [ ] 更新 `a1-LIVE2D_REFACTORING_PLAN.md`
- [ ] 创建 `README_REFACTORING.md`
- [ ] 更新代码注释
- [ ] 创建架构图
- [ ] 编写迁移指南

#### 任务 4.4：全面测试
**任务清单：**
- [ ] 单元测试（覆盖率 > 90%）
- [ ] 集成测试
- [ ] 性能测试
- [ ] 兼容性测试（Windows/macOS/Linux）
- [ ] 用户体验测试

**验收标准：**
- 所有测试通过
- 无已知 Bug
- 用户体验良好

---

### 阶段 5：发布准备（预计 1 天）

#### 任务 5.1：准备发布
**任务清单：**
- [ ] 更新 `CHANGELOG.md`
- [ ] 创建发布说明
- [ ] 准备版本标签
- [ ] 更新配置模板

#### 任务 5.2：代码审查
**任务清单：**
- [ ] 自我代码审查
- [ ] 团队代码审查（如果有）
- [ ] 修复审查问题
- [ ] 代码格式化

#### 任务 5.3：发布
**任务清单：**
- [ ] 提交代码到 Git
- [ ] 创建发布版本
- [ ] 更新文档
- [ ] 通知用户

---

## 四、风险管理

### 4.1 高风险项

| 风险项 | 影响 | 概率 | 应对措施 |
|--------|------|------|----------|
| 功能回归 | 高 | 中 | 完善的单元测试和集成测试 |
| 性能下降 | 高 | 低 | 持续性能监控和优化 |
| 兼容性问题 | 中 | 中 | 在多个平台测试 |
| 开发周期延长 | 中 | 中 | 严格执行阶段计划 |

### 4.2 回滚策略

**触发条件：**
- 阶段 3（主窗口重构）无法按时完成
- 发现重大设计缺陷
- 功能回归无法修复

**回滚步骤：**
1. 保留阶段 1 和阶段 2 的成果
2. 回退到 `pet.py.backup`
3. 修复因重构引入的问题
4. 发布基于旧代码的版本

---

## 五、验收标准

### 5.1 功能验收

- [ ] 所有现有功能正常工作
- [ ] 无功能回归
- [ ] 新增功能符合设计要求

### 5.2 性能验收

- [ ] CPU 占用 < 15%
- [ ] 内存占用 < 100MB
- [ ] 帧率稳定在 60FPS
- [ ] 启动时间 < 3秒

### 5.3 质量验收

- [ ] 单元测试覆盖率 > 90%
- [ ] 所有测试通过
- [ ] 代码符合 PEP 8 规范
- [ ] 文档完整

### 5.4 可维护性验收

- [ ] 代码结构清晰
- [ ] 职责分离明确
- [ ] 易于扩展新功能
- [ ] 易于编写测试

---

## 六、后续计划

### 6.1 短期计划（1-2 周）

- [ ] 完成 Live2D 渲染器实现
- [ ] 添加更多动画效果
- [ ] 优化交互体验
- [ ] 添加配置界面

### 6.2 中期计划（1-2 月）

- [ ] 多模型支持
- [ ] 语音识别
- [ ] 语音合成
- [ ] AI 对话集成

### 6.3 长期计划（3-6 月）

- [ ] 插件系统
- [ ] 社区模型库
- [ ] 跨平台支持完善
- [ ] 商业化功能

---

## 七、附录

### A. 参考资料

- [PEP 8 - Python 代码风格指南](https://pep.python.org/pep-0008/)
- [PyQt5 官方文档](https://doc.qt.io/qt-5/)
- [Python 架构模式](https://refactoring.guru/design-patterns/python)

### B. 工具推荐

- **代码分析：** pylint, black, isort
- **测试框架：** pytest, pytest-cov, pytest-qt
- **性能分析：** py-spy, memory_profiler
- **文档工具：** Sphinx, MkDocs

### C. 联系方式

如有问题或建议，请联系：
- 项目地址：https://github.com/MaiM-with-u/MaiM-desktop-pet
- 问题反馈：https://github.com/MaiM-with-u/MaiM-desktop-pet/issues

---

**文档结束**