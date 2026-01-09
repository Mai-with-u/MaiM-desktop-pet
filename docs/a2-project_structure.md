# 项目文件结构说明

## 文档概述

本文档详细说明了 MaiM-desktop-pet 项目的完整文件结构，并为每个文件夹和文件添加了详细注释。

**创建日期：** 2026-01-08  
**最后更新：** 2026-01-08

---

## 项目根目录

```
MaiM-desktop-pet/
├── .gitignore                          # Git 忽略文件配置，指定不需要版本控制的文件和目录
├── config.py                          # 配置文件加载模块，负责读取和管理应用程序配置
├── config.toml.backup                 # 配置文件备份，用于恢复默认配置
├── main.py                            # 应用程序入口文件，负责初始化和启动桌面宠物
├── README.md                          # 项目说明文档，包含项目介绍、安装和使用指南
├── requirements.txt                    # Python 依赖包列表，用于 pip install 安装项目依赖
├── start.bat                          # Windows 批处理启动脚本，方便快速启动应用
│
├── data/                              # 数据目录，存储应用程序运行时数据
│   └── test_chat.db                  # SQLite 测试数据库文件，存储聊天记录
│
├── docs/                              # 文档目录，包含项目所有相关文档
│   ├── README.md                      # 文档索引，列出所有文档及其用途
│   ├── a1-LIVE2D_REFACTORING_PLAN.md # Live2D 引入重构规划文档，详细分析当前问题和重构方案
│   ├── f1-SCALE_FEATURE.md            # 缩放功能说明文档，介绍界面缩放功能的实现
│   ├── g1-MIGRATION_GUIDE.md          # 迁移指南，指导用户从旧版本升级到新版本
│   ├── l1-CHANGELOG.md               # 变更日志，记录每个版本的更新内容
│   ├── l2-UPDATE_SUMMARY.md          # 更新摘要，概述最新版本的主要变更
│   ├── p1-REFACTORING_COMPLETION_REPORT.md # 重构完成报告，总结重构成果
│   ├── p2-REFACTORING_SUMMARY.md     # 重构摘要，概述重构过程和关键改进
│   ├── t1-TODOLIST.md                # 总体任务清单，记录项目开发的所有待办事项
│   └── t2-PET_REFACTORING_TODOLIST.md # pet.py 解构重构任务清单，详细的重构实施计划
│
├── img/                               # 图片资源目录，存储应用程序使用的图片
│   ├── maim.ico                      # 应用程序图标文件（Windows 图标格式）
│   ├── maim.png                      # 托盘图标图片
│   ├── maimai.png                     # 麦麦完整图片
│   └── small_maimai.png              # 麦麦缩小版图片，用于桌面显示
│
├── logs/                              # 日志目录，存储应用程序运行日志（自动生成）
│
├── src/                               # 源代码目录，包含所有 Python 源代码
│   ├── __init__.py                    # src 包初始化文件
│   │
│   ├── core/                          # 核心业务逻辑目录
│   │   ├── chat.py                   # 聊天核心模块，处理与 AI 的交互和消息发送
│   │   └── router.py                 # 路由模块，处理不同类型消息的路由分发
│   │
│   ├── database/                      # 数据库管理目录
│   │   ├── __init__.py              # database 包初始化文件
│   │   ├── base.py                  # 数据库基类，定义数据库接口规范
│   │   ├── factory.py               # 数据库工厂类，负责创建数据库实例
│   │   ├── manager.py               # 数据库管理器，提供高级数据库操作接口
│   │   ├── README.md               # 数据库模块说明文档
│   │   ├── sqlite.py               # SQLite 数据库实现
│   │   └── test_database.py        # 数据库测试文件，测试数据库功能
│   │
│   ├── frontend/                     # 前端界面目录，包含所有 UI 相关代码
│   │   ├── bubble_input.py          # 气泡输入框组件，提供用户输入界面
│   │   ├── bubble_menu.py           # 右键气泡菜单组件
│   │   ├── bubble_speech.py         # 气泡消息列表组件，显示多条消息气泡
│   │   ├── bubble_speech_usage.md   # 气泡系统使用说明文档
│   │   ├── pet.py                  # 原始桌面宠物主窗口类（已备份）
│   │   ├── pet.py.backup           # pet.py 的备份文件
│   │   ├── ScreenshotSelector.py    # 截图选择器组件，用于区域截图
│   │   └── signals.py              # 全局信号总线，用于组件间通信
│   │
│   │   ├── core/                   # 前端核心业务层目录（重构后的新架构）
│   │   │   ├── __init__.py        # frontend.core 包初始化文件
│   │   │   │
│   │   │   ├── managers/          # 管理器目录，负责各项功能的管理
│   │   │   │   ├── __init__.py   # managers 包初始化文件
│   │   │   │   ├── event_manager.py        # 事件管理器，处理所有用户输入事件
│   │   │   │   ├── render_manager.py      # 渲染管理器，管理渲染器实例和模式切换
│   │   │   │   └── state_manager.py       # 状态管理器，管理窗口和终端状态
│   │   │   │
│   │   │   ├── models/            # 模型目录，定义数据模型
│   │   │   │   └── __init__.py   # models 包初始化文件
│   │   │   │
│   │   │   ├── render/            # 渲染器目录，实现不同的渲染方式
│   │   │   │   ├── __init__.py   # render 包初始化文件
│   │   │   │   ├── interfaces.py # 渲染器接口定义，定义 IRenderer 抽象基类
│   │   │   │   ├── live2d_renderer.py  # Live2D 渲染器实现（框架）
│   │   │   │   └── static_renderer.py   # 静态图片渲染器实现
│   │   │   │
│   │   │   └── workers/           # 工作线程目录，处理后台任务
│   │   │       ├── __init__.py   # workers 包初始化文件
│   │   │       └── move_worker.py        # 移动工作线程，处理窗口拖动逻辑
│   │   │
│   │   ├── data/                   # 数据层目录（重构后的新架构）
│   │   │   └── __init__.py       # data 包初始化文件
│   │   │
│   │   ├── presentation/           # 表现层目录（重构后的新架构）
│   │   │   ├── __init__.py       # presentation 包初始化文件
│   │   │   └── refactored_pet.py # 重构后的桌面宠物主窗口类
│   │   │
│   │   └── style_sheets/         # 样式表目录，存储 CSS 样式文件
│   │       ├── bubble_input.css   # 输入框样式表
│   │       ├── bubble_menu.css    # 右键菜单样式表
│   │       └── pet.css           # 主窗口样式表
│   │
│   ├── shared/                       # 共享模块目录，存放跨模块使用的代码
│   │   └── models/                # 共享数据模型目录
│   │       ├── __init__.py        # models 包初始化文件
│   │       ├── message.py         # 消息数据模型，定义消息的结构和属性
│   │       └── README.md         # 模型模块说明文档
│   │
│   └── util/                        # 工具模块目录，存放通用工具函数
│       ├── except_hook.py          # 异常钩子，全局异常处理和错误捕获
│       ├── image_util.py           # 图片工具，提供图片处理和转换功能
│       └── logger.py              # 日志工具，提供统一的日志记录接口
│
└── tests/                            # 测试目录，包含所有测试代码
    └── test_message_update.py       # 消息更新测试，测试消息功能
```

---

## 目录详细说明

### 根目录文件

| 文件名 | 说明 | 优先级 |
|--------|------|--------|
| `.gitignore` | Git 版本控制忽略文件配置 | P3 |
| `config.py` | 配置加载模块，提供统一的配置访问接口 | P0 |
| `config.toml.backup` | 配置文件备份，用于配置恢复 | P2 |
| `main.py` | 应用程序入口，负责初始化和启动 | P0 |
| `README.md` | 项目说明文档，包含安装和使用指南 | P0 |
| `requirements.txt` | Python 依赖包列表 | P0 |
| `start.bat` | Windows 启动脚本 | P2 |

### data/ - 数据目录

存放应用程序运行时生成的数据文件。

| 文件/目录 | 说明 |
|-----------|------|
| `test_chat.db` | SQLite 数据库文件，存储聊天记录（开发测试用） |

### docs/ - 文档目录

存放项目所有相关文档，按功能分类：

| 分类 | 前缀 | 说明 |
|------|------|------|
| 架构规划 | a1- | Live2D 重构规划文档 |
| 功能说明 | f1- | 缩放功能说明文档 |
| 迁移指南 | g1- | 版本迁移指南 |
| 变更日志 | l1-, l2- | 变更日志和更新摘要 |
| 完成报告 | p1-, p2- | 重构完成报告和摘要 |
| 任务清单 | t1-, t2- | 总体任务清单和具体重构任务 |

### img/ - 图片资源目录

存放应用程序使用的所有图片资源。

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `maim.ico` | Windows 图标 | 应用程序图标 |
| `maim.png` | 托盘图标 | 系统托盘显示 |
| `maimai.png` | 麦麦完整图片 | 备用资源 |
| `small_maimai.png` | 麦麦缩小版 | 桌面显示 |

### src/ - 源代码目录

项目的核心源代码，按功能模块组织。

#### src/core/ - 核心业务逻辑

| 文件 | 说明 | 职责 |
|------|------|------|
| `chat.py` | 聊天核心模块 | AI 交互、消息发送、聊天逻辑 |
| `router.py` | 路由模块 | 消息路由、事件分发 |

#### src/database/ - 数据库模块

| 文件 | 说明 | 职责 |
|------|------|------|
| `base.py` | 数据库基类 | 定义数据库接口 |
| `factory.py` | 数据库工厂 | 创建数据库实例 |
| `manager.py` | 数据库管理器 | 高级数据库操作 |
| `sqlite.py` | SQLite 实现 | SQLite 数据库具体实现 |
| `test_database.py` | 数据库测试 | 单元测试 |

#### src/frontend/ - 前端界面

**旧架构文件（待迁移或废弃）：**
| 文件 | 说明 | 状态 |
|------|------|------|
| `pet.py` | 原始主窗口 | 已备份 |
| `pet.py.backup` | 主窗口备份 | 保留 |
| `bubble_input.py` | 输入框组件 | 使用中 |
| `bubble_menu.py` | 菜单组件 | 使用中 |
| `bubble_speech.py` | 消息列表组件 | 使用中 |
| `ScreenshotSelector.py` | 截图选择器 | 使用中 |
| `signals.py` | 信号总线 | 使用中 |

**新架构文件（重构后）：**

##### src/frontend/core/ - 前端核心业务层

**managers/ - 管理器模块**
| 文件 | 说明 | 职责 |
|------|------|------|
| `event_manager.py` | 事件管理器 | 处理鼠标事件、右键菜单、窗口移动 |
| `render_manager.py` | 渲染管理器 | 管理渲染器、切换渲染模式 |
| `state_manager.py` | 状态管理器 | 管理窗口状态、终端状态 |

**render/ - 渲染器模块**
| 文件 | 说明 | 职责 |
|------|------|------|
| `interfaces.py` | 渲染器接口 | 定义 IRenderer 抽象基类 |
| `static_renderer.py` | 静态渲染器 | 实现静态图片显示 |
| `live2d_renderer.py` | Live2D 渲染器 | 实现 Live2D 动画显示（框架） |

**workers/ - 工作线程模块**
| 文件 | 说明 | 职责 |
|------|------|------|
| `move_worker.py` | 移动工作线程 | 处理窗口拖动逻辑 |

**models/** - 模型模块
| 文件 | 说明 |
|------|------|
| `__init__.py` | 模块初始化文件（预留） |

**data/** - 数据层
| 文件 | 说明 |
|------|------|
| `__init__.py` | 模块初始化文件（预留） |

**presentation/** - 表现层
| 文件 | 说明 | 职责 |
|------|------|------|
| `refactored_pet.py` | 重构后的主窗口 | 简化的主窗口类 |

**style_sheets/** - 样式表
| 文件 | 说明 | 用途 |
|------|------|------|
| `bubble_input.css` | 输入框样式 | 美化输入框 |
| `bubble_menu.css` | 菜单样式 | 美化右键菜单 |
| `pet.css` | 主窗口样式 | 美化主窗口 |

#### src/shared/ - 共享模块

| 文件 | 说明 | 职责 |
|------|------|------|
| `models/message.py` | 消息数据模型 | 定义消息结构 |
| `models/README.md` | 模型说明文档 | 模型使用说明 |

#### src/util/ - 工具模块

| 文件 | 说明 | 职责 |
|------|------|------|
| `except_hook.py` | 异常钩子 | 全局异常处理 |
| `image_util.py` | 图片工具 | 图片处理、格式转换 |
| `logger.py` | 日志工具 | 统一日志记录 |

### tests/ - 测试目录

存放所有测试代码。

| 文件 | 说明 |
|------|------|
| `test_message_update.py` | 消息更新测试 |

---

## 架构分层说明

### 整体架构

```
┌─────────────────────────────────────────────┐
│         Presentation Layer (UI 层)          │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ DesktopPet│  │BubbleSys │  │TrayMgr  │ │
│  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────┘
                    │
┌───────────────────┴───────────────────────┐
│      Presentation Layer (Core)             │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │RenderMgr │  │EventMgr  │  │StateMgr │ │
│  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────┘
                    │
┌───────────────────┴───────────────────────┐
│         Business Layer (业务层)            │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │Renderer  │  │Workers   │  │Models   │ │
│  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────┘
                    │
┌───────────────────┴───────────────────────┐
│          Data Layer (数据层)              │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │Database  │  │Config    │  │Resources│ │
│  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────┘
```

### 模块依赖关系

```
main.py
  │
  ├─> src/frontend/presentation/refactored_pet.py (主窗口)
  │       │
  │       ├─> src/frontend/core/managers/* (管理器)
  │       │       │
  │       │       ├─> render_manager.py
  │       │       │       ├─> src/frontend/core/render/interfaces.py (接口)
  │       │       │       ├─> src/frontend/core/render/static_renderer.py (静态)
  │       │       │       └─> src/frontend/core/render/live2d_renderer.py (Live2D)
  │       │       │
  │       │       ├─> event_manager.py
  │       │       │       └─> src/frontend/core/workers/move_worker.py
  │       │       │
  │       │       └─> state_manager.py
  │       │
  │       ├─> src/frontend/bubble_*.py (气泡组件)
  │       ├─> src/frontend/ScreenshotSelector.py (截图)
  │       └─> src/frontend/signals.py (信号总线)
  │
  ├─> src/core/chat.py (聊天逻辑)
  │       └─> src/core/router.py (路由)
  │
  ├─> src/database/* (数据库)
  │
  ├─> config.py (配置)
  │
  └─> src/util/* (工具)
          ├─> logger.py (日志)
          ├─> image_util.py (图片)
          └─> except_hook.py (异常)
```

---

## 重构前后对比

### 旧架构（pet.py）

```
src/frontend/
├── pet.py (600+ 行，包含所有功能)
├── bubble_input.py
├── bubble_menu.py
├── bubble_speech.py
├── ScreenshotSelector.py
└── signals.py
```

**问题：**
- 单一类承担过多职责
- 代码耦合度高
- 难以维护和测试
- 无法扩展 Live2D

### 新架构（重构后）

```
src/frontend/
├── presentation/           # UI 层
│   └── refactored_pet.py   # 简化的主窗口
│
└── core/                  # 核心业务层
    ├── managers/          # 管理器
    │   ├── event_manager.py
    │   ├── render_manager.py
    │   └── state_manager.py
    │
    ├── render/            # 渲染器
    │   ├── interfaces.py
    │   ├── static_renderer.py
    │   └── live2d_renderer.py
    │
    ├── workers/           # 工作线程
    │   └── move_worker.py
    │
    └── models/           # 数据模型
```

**优势：**
- 职责清晰分离
- 低耦合高内聚
- 易于维护和测试
- 支持多种渲染模式

---

## 关键文件说明

### 核心入口文件

#### main.py
- **作用**：应用程序入口
- **职责**：
  - 初始化 QApplication
  - 加载配置
  - 创建主窗口实例
  - 启动事件循环
- **依赖**：config.py, refactored_pet.py

#### config.py
- **作用**：配置管理
- **职责**：
  - 加载 config.toml
  - 提供配置访问接口
  - 处理配置热更新
- **依赖**：tomli

### 核心管理器

#### event_manager.py
- **作用**：事件处理管理
- **职责**：
  - 鼠标事件处理
  - 右键菜单显示
  - 窗口移动管理
- **依赖**：move_worker.py, refactored_pet.py

#### render_manager.py
- **作用**：渲染管理
- **职责**：
  - 创建渲染器实例
  - 切换渲染模式
  - 设置动画状态
- **依赖**：interfaces.py, static_renderer.py, live2d_renderer.py

#### state_manager.py
- **作用**：状态管理
- **职责**：
  - 窗口锁定/解锁
  - 窗口显示/隐藏
  - 终端控制
  - 状态持久化
- **依赖**：config.toml, win32gui (Windows)

### 渲染器

#### static_renderer.py
- **作用**：静态图片渲染
- **职责**：
  - 加载和显示图片
  - 处理图片缩放
- **依赖**：PyQt5.QtGui.QPixmap

#### live2d_renderer.py
- **作用**：Live2D 动画渲染
- **职责**：
  - 加载 Live2D 模型
  - 播放动画
  - 处理交互
- **依赖**：live2d-py（可选）

---

## 文件命名规范

### 前缀规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| a1- | Architecture (架构) | a1-LIVE2D_REFACTORING_PLAN.md |
| f1- | Feature (功能) | f1-SCALE_FEATURE.md |
| g1- | Guide (指南) | g1-MIGRATION_GUIDE.md |
| l1-, l2- | Log (日志) | l1-CHANGELOG.md, l2-UPDATE_SUMMARY.md |
| p1-, p2- | Progress/Report (进度/报告) | p1-REFACTORING_COMPLETION_REPORT.md |
| t1-, t2- | Todo (任务) | t1-TODOLIST.md, t2-PET_REFACTORING_TODOLIST.md |

### 代码文件命名

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| 模块 | 小写+下划线 | `event_manager.py` |
| 类 | 大驼峰 | `EventManager` |
| 函数 | 小写+下划线 | `handle_mouse_press()` |
| 常量 | 全大写+下划线 | `MAX_FPS` |

---

## 文件依赖关系图

```
config.py
  └─> config.toml

main.py
  ├─> config.py
  ├─> refactored_pet.py
  └─> logger.py

refactored_pet.py
  ├─> event_manager.py
  ├─> render_manager.py
  ├─> state_manager.py
  ├─> bubble_system.py
  ├─> screenshot_manager.py
  ├─> tray_manager.py
  └─> signals.py

event_manager.py
  ├─> move_worker.py
  └─> signals.py

render_manager.py
  ├─> interfaces.py
  ├─> static_renderer.py
  └─> live2d_renderer.py

state_manager.py
  └─> config.toml

chat.py
  ├─> router.py
  └─> database/*
```

---

## 开发规范

### 代码组织原则

1. **单一职责原则**：每个类只负责一个功能
2. **依赖倒置原则**：高层模块不依赖低层模块
3. **开闭原则**：对扩展开放，对修改关闭
4. **接口隔离原则**：使用明确的接口定义

### 文件组织规范

1. **分层架构**：UI 层、业务层、数据层分离
2. **模块化**：功能相关代码放在同一目录
3. **命名清晰**：文件名和类名要能清楚表达其用途
4. **注释完整**：每个文件都要有文档字符串

---

## 维护指南

### 添加新功能

1. **确定功能类型**
   - UI 功能 → `src/frontend/presentation/`
   - 业务逻辑 → `src/frontend/core/`
   - 数据相关 → `src/database/`
   - 工具函数 → `src/util/`

2. **创建文件**
   - 使用小写+下划线命名
   - 添加完整的文档字符串
   - 遵循 PEP 8 代码规范

3. **更新依赖**
   - 在 `requirements.txt` 中添加新依赖
   - 在相关文件中导入新模块

4. **编写测试**
   - 在 `tests/` 目录创建测试文件
   - 确保测试覆盖率

### 修改现有功能

1. **备份原始文件**
   - 复制原始文件为 `.backup`

2. **理解现有代码**
   - 阅读相关文档
   - 理解代码架构

3. **谨慎修改**
   - 小步快跑
   - 每次修改后测试

4. **更新文档**
   - 更新相关文档
   - 记录变更内容

---

## 附录

### A. 参考资源

- [PyQt5 官方文档](https://doc.qt.io/qt-5/)
- [Python PEP 8 代码风格指南](https://pep.python.org/pep-0008/)
- [Python 架构模式](https://refactoring.guru/design-patterns/python)

### B. 相关文档

- [docs/README.md](./docs/README.md) - 文档索引
- [README.md](../README.md) - 项目说明
- [a1-LIVE2D_REFACTORING_PLAN.md](./docs/a1-LIVE2D_REFACTORING_PLAN.md) - 重构规划

### C. 联系方式

如有问题或建议，请联系：
- 项目地址：https://github.com/MaiM-with-u/MaiM-desktop-pet
- 问题反馈：https://github.com/MaiM-with-u/MaiM-desktop-pet/issues

---

**文档结束**
