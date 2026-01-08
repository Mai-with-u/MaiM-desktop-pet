# 配置系统说明

## 概述

新的配置系统提供了更完善的配置管理功能，包括：
- 自动创建配置文件
- 配置验证
- 配置模板
- 配置更新 API

## 目录结构

```
config/
├── __init__.py           # 配置系统入口
├── schema.py             # 配置模式定义（使用 Pydantic）
├── loader.py             # 配置加载器
├── templates/            # 配置模板
│   └── config.toml.template  # 配置文件模板
└── README.md             # 本文档
```

## 使用方法

### 基本使用

```python
from config import load_config, Config

# 加载配置（会自动确保配置文件存在）
config = load_config()

# 访问配置
print(config.url)
print(config.Nickname)
print(config.live2d['enabled'])
```

### 获取界面缩放倍率

```python
from config import get_scale_factor

scale = get_scale_factor(config)
print(f"缩放倍率: {scale}")
```

### 更新配置

```python
from config import update_config_value

# 更新单个配置项
update_config_value('live2d', 'enabled', False)
update_config_value(None, 'hide_console', True)
```

## 配置文件自动创建

程序首次运行时，如果没有 `config.toml` 文件，会自动：
1. 从 `config/templates/config.toml.template` 复制配置模板
2. 创建 `config.toml` 文件
3. 显示提示信息
4. 暂停程序，等待用户修改配置

## 配置模板

配置模板包含详细的注释说明所有配置项的含义和用法。模板文件位置：
```
config/templates/config.toml.template
```

## 配置验证

使用 Pydantic 进行配置验证，确保配置项的类型正确。如果配置文件格式错误，程序会：
1. 记录错误日志
2. 显示错误信息
3. 退出程序

## 多实例模式

当 `allow_multiple_source_conversion = true` 时，会自动为每个实例生成唯一的平台 ID：

```python
config.platform = "desktop-pet-{uuid}"
```

这样可以让多个桌宠实例同时连接到后端服务器。

## 向后兼容

为了保持向后兼容，旧的 `config.py` 文件仍然存在，但已经改为使用新的配置系统：

```python
# 旧代码仍然可以使用
from config import config, scale_factor

# 但推荐使用新的方式
from config import load_config, get_scale_factor
config = load_config()
scale = get_scale_factor(config)
```

## 常见问题

### Q: 如何重新生成配置文件？

A: 删除 `config.toml` 文件，然后重新运行程序即可。

### Q: 如何修改配置？

A: 直接编辑 `config.toml` 文件，然后重新运行程序。

### Q: 配置文件在哪里？

A: 在项目根目录下，文件名为 `config.toml`。

### Q: 配置文件会被提交到 Git 吗？

A: 不会，`config.toml` 已添加到 `.gitignore` 中，不会提交到版本控制。

## 配置项说明

详细的配置项说明请参考 `config/templates/config.toml.template` 文件。

主要配置项包括：
- **基础配置**: WebSocket 地址、昵称、平台标识等
- **界面配置**: 缩放倍率
- **渲染配置**: 渲染模式（静态/Live2D）
- **Live2D 配置**: 模型路径、物理模拟、渲染质量等
- **动画配置**: 默认动画状态、表情、帧率等
- **性能配置**: 最大帧率、纹理缓存大小等
- **数据库配置**: 数据库类型、路径等
- **状态配置**: 窗口锁定、可见性等

## 开发指南

### 添加新的配置项

1. 在 `config/schema.py` 的 `Config` 类中添加新字段：

```python
class Config(BaseModel):
    # ... 现有字段 ...
    new_field: Optional[str] = None
```

2. 在 `config/templates/config.toml.template` 中添加配置项和说明。

3. 在代码中使用：

```python
config = load_config()
value = config.new_field
```

### 配置验证规则

使用 Pydantic 的类型注解来定义验证规则：

```python
from pydantic import BaseModel, Field

class Config(BaseModel):
    max_fps: int = Field(default=60, ge=30, le=60)
```

## 注意事项

1. **不要提交 `config.toml` 到版本控制**：文件中包含个人配置信息
2. **修改模板后通知用户**：如果修改了模板结构，需要在文档中说明
3. **保持向后兼容**：添加新配置项时提供合理的默认值
4. **测试配置加载**：修改配置系统后务必测试配置加载是否正常

## 相关文件

- `config.toml` - 用户配置文件（不提交到 Git）
- `config/templates/config.toml.template` - 配置模板
- `.gitignore` - Git 忽略规则（包含 config.toml）
- `config.py` - 向后兼容层