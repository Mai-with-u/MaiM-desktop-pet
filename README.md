# MaiM 桌宠

<p align="center">
  <a href="https://github.com/Maple127667/MaiM-desktop-pet">
    <img src="img/small_maimai.png" alt="Logo" width="200">
  </a>
</p>

一个基于 PyQt5 开发的桌宠应用，具有交互式聊天功能和精美的界面设计。其聊天核心为[麦麦Bot](https://github.com/MaiM-with-u/MaiBot)，一款专注于群组聊天的赛博网友（非常专注）QQ BOT。

## 功能特点

- 🎭 可爱的桌宠形象（麦麦）
- 💬 支持实时对话交互
- 🖱️ 支持拖拽移动
- 📌 置顶显示
- 💭 气泡对话框
- 🔔 系统托盘支持
- ✨ 支持静态图片和 Live2D 动画渲染
- 🎨 界面缩放支持
- 📸 截图功能
- 🔄 模块化架构，易于扩展

## 系统要求

- Python 3.8+
- Windows/Linux/MacOS
- PyQt5
- （可选）Live2D 库（用于 Live2D 动画）

## 快速开始

### 方式一：一键运行（推荐）

1. 首次运行会自动创建 `config.toml` 配置文件
2. 编辑 `config.toml` 配置文件，设置 WebSocket 服务器地址
3. 双击 `start.bat` 启动程序

### 方式二：手动部署

```bash
# 1. 创建虚拟环境（推荐）
python -m venv venv

# Windows 激活虚拟环境
venv\Scripts\activate

# Linux/Mac 激活虚拟环境
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

## 配置说明

程序首次运行时会自动从 `config/templates/config.toml.template` 创建 `config.toml` 配置文件。

### 主要配置项

```toml
# WebSocket 服务器地址（必填）
url = "ws://127.0.0.1:8000/ws"

# 桌宠昵称
Nickname = "麦麦"

# 是否隐藏终端窗口
hide_console = true

# 渲染模式：static（静态图片）或 live2d（Live2D 动画）
[render]
mode = "static"

# Live2D 配置（仅在 mode = "live2d" 时生效）
[live2d]
enabled = false
model_path = "./live2d/models/your-model.model3.json"

# 界面缩放（0.5 ~ 3.0）
[interface]
scale_factor = 1.0
```

**注意：** `config.toml` 包含个人配置，已添加到 `.gitignore`，不会被提交到 Git。

## 使用说明

### 桌宠交互

- **左键拖拽**：移动宠物位置
- **双击宠物**：触发互动动作
- **右键点击**：打开功能菜单
  - 隐藏：隐藏宠物
  - 截图：截图并发送给 mmc
  - 聊聊天：打开对话输入框
  - 退出：关闭程序

### 系统托盘

- **显示宠物**：将桌宠显示在桌面上
- **显示/隐藏终端**：默认隐藏终端以优化视觉效果，显示终端以方便调试

## 可能会出现的问题

### 1. Could not load the Qt platform plugin "windows" in ""

参考解决方案：https://blog.csdn.net/weixin_46599926/article/details/132576385

### 2. 配置文件相关问题

- 如果配置文件格式错误，程序会自动从模板重新创建
- 查看 `logs/pet.log` 获取详细错误信息

## 项目结构

```
MaiM-desktop-pet
├── config/                      # 配置系统
│   ├── __init__.py             # 配置模块入口
│   ├── loader.py               # 配置加载器
│   ├── schema.py               # 配置模式定义
│   └── templates/              # 配置模板
│       └── config.toml.template
├── data/                       # 数据目录
├── docs/                       # 文档目录
├── img/                        # 图片资源
│   ├── maim.png
│   ├── maimai.png
│   └── small_maimai.png
├── logs/                       # 日志目录
├── src/                        # 源代码
│   ├── core/                   # 核心业务层
│   │   ├── chat.py            # 聊天核心
│   │   └── router.py          # 路由器
│   ├── database/               # 数据库模块
│   │   ├── base.py            # 数据库基类
│   │   ├── factory.py         # 数据库工厂
│   │   ├── manager.py         # 数据库管理器
│   │   └── sqlite.py         # SQLite 实现
│   ├── frontend/               # 前端模块
│   │   ├── core/              # 前端核心
│   │   │   ├── managers/      # 管理器
│   │   │   │   ├── render_manager.py    # 渲染管理器
│   │   │   │   ├── event_manager.py     # 事件管理器
│   │   │   │   └── state_manager.py     # 状态管理器
│   │   │   ├── render/         # 渲染器
│   │   │   │   ├── interfaces.py        # 渲染器接口
│   │   │   │   ├── static_renderer.py   # 静态渲染器
│   │   │   │   └── live2d_renderer.py   # Live2D 渲染器
│   │   │   └── models/         # 模型
│   │   ├── presentation/        # 表现层
│   │   │   └── refactored_pet.py
│   │   ├── components/         # UI 组件
│   │   │   ├── bubble_input.py # 气泡输入
│   │   │   ├── bubble_menu.py  # 气泡菜单
│   │   │   ├── bubble_speech.py # 气泡显示
│   │   │   └── ScreenshotSelector.py # 截图选择
│   │   ├── style_sheets/      # 样式表
│   │   ├── pet.py            # 主窗口（旧版）
│   │   └── signals.py        # 信号定义
│   ├── shared/                 # 共享模块
│   │   └── models/           # 共享模型
│   └── util/                  # 工具模块
│       ├── except_hook.py     # 异常钩子
│       ├── image_util.py      # 图片工具
│       └── logger.py         # 日志工具
├── tests/                      # 测试目录
├── main.py                     # 程序入口
├── requirements.txt            # 依赖列表
├── start.bat                   # 启动脚本
├── README.md                   # 项目文档
└── .gitignore                 # Git 忽略文件
```

## 开发说明

### 技术栈

- **GUI 框架**：PyQt5
- **聊天核心**：WebSocket（连接到 MaiBot 后端）
- **数据库**：SQLite
- **配置管理**：TOML + Pydantic
- **动画渲染**：静态图片 / Live2D（可选）

### 架构设计

项目采用分层架构设计：

1. **数据层**：负责数据持久化和配置管理
2. **业务层**：核心业务逻辑和渲染引擎
3. **表现层**：UI 组件和用户交互
4. **核心层**：管理器和协调器

### 开发指南

详细的开发指南请查看 `docs/` 目录：

- `docs/LIVE2D_REFACTORING_PLAN.md` - Live2D 重构规划
- `docs/REFACTORING_SUMMARY.md` - 重构总结
- `docs/REFACTORING_TODOLIST.md` - 重构任务清单
- `docs/MIGRATION_GUIDE.md` - 迁移指南

## 注意事项

- ✅ 确保系统已安装 Python 3.8 或更高版本
- ✅ 运行时需要保持网络连接（用于 WebSocket 通信）
- ✅ 建议使用虚拟环境运行项目
- ✅ 配置文件 `config.toml` 包含个人设置，已添加到 `.gitignore`
- ⚠️ 首次运行会自动创建配置文件，请根据需求修改
- ⚠️ 使用 Live2D 功能需要额外安装 Live2D 库

## 更新日志

查看 [CHANGELOG.md](docs/CHANGELOG.md) 了解详细的版本更新历史。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。


## 联系方式

- 项目地址：https://github.com/MaiM-with-u/MaiM-desktop-pet
- 问题反馈：https://github.com/MaiM-with-u/MaiM-desktop-pet/issues

---

