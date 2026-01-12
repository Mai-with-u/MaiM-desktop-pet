# Live2D 动画调度器使用指南

## 文档概述

本文档详细介绍了 Live2D 动画调度器的使用方法、配置选项和最佳实践。

**文档版本：** v1.0  
**创建日期：** 2026-01-13  
**最后更新：** 2026-01-13

---

## 一、功能简介

### 1.1 什么是动画调度器？

动画调度器（AnimationScheduler）是一个自动化的 Live2D 动画管理系统，可以：

- ✅ 自动在待机动作和随机动作之间切换
- ✅ 可配置的时间间隔和动作持续时间
- ✅ 支持动作组权重（控制动作出现概率）
- ✅ 支持白名单/黑名单（限制可用动作）
- ✅ 实时监听动作切换信号

### 1.2 使用场景

- **桌面待机**：长时间显示时，自动切换不同动作保持活力
- **聊天互动**：在聊天间隙播放随机动作增加趣味性
- **游戏陪玩**：根据游戏场景自动切换动作

### 1.3 工作原理

```
[待机动作] → [等待 30-90 秒] → [随机动作] → [持续 5 秒] → [返回待机]
    ↑                                                              │
    └──────────────────────────────────────────────────────────────┘
```

---

## 二、快速开始

### 2.1 基础使用

**启用动画调度器：**

在 `config.toml` 中设置：

```toml
[animation_scheduler]
enabled = true
```

**配置时间参数：**

```toml
[animation_scheduler]
# 待机间隔（秒）
idle_interval_min = 30.0  # 最小等待时间
idle_interval_max = 90.0  # 最大等待时间

# 随机动作持续时间（秒）
random_motion_duration = 5.0
```

**运行程序：**

```bash
python main.py
```

动画调度器会自动启动，在待机动作和随机动作之间切换。

---

## 三、配置详解

### 3.1 基础配置

#### enabled（是否启用）

```toml
[animation_scheduler]
enabled = true  # 启用调度器
# enabled = false  # 禁用调度器（使用手动控制）
```

**说明：**
- `true`：启用自动随机动画切换
- `false`：禁用调度器，使用手动控制（通过 `set_animation_state` 方法）

---

#### idle_interval_min / idle_interval_max（待机间隔）

```toml
[animation_scheduler]
idle_interval_min = 30.0  # 最小 30 秒
idle_interval_max = 90.0  # 最大 90 秒
```

**说明：**
- 播放待机动作后，等待随机时间（30-90 秒）再切换到随机动作
- 值越大，待机动作持续越久
- `idle_interval_min` 必须小于 `idle_interval_max`

**推荐配置：**

| 场景 | 最小间隔 | 最大间隔 |
|------|----------|----------|
| 桌面待机 | 30 秒 | 90 秒 |
| 聊天陪玩 | 10 秒 | 30 秒 |
| 游戏陪玩 | 5 秒 | 15 秒 |

---

#### random_motion_duration（随机动作持续时间）

```toml
[animation_scheduler]
random_motion_duration = 5.0  # 随机动作持续 5 秒
```

**说明：**
- 播放随机动作后，持续指定时间后返回待机动作
- 值越大，随机动作播放越久

**推荐配置：**

| 场景 | 持续时间 |
|------|----------|
| 桌面待机 | 5 秒 |
| 聊天陪玩 | 3 秒 |
| 游戏陪玩 | 2 秒 |

---

### 3.2 高级配置

#### 动作组权重

```toml
[animation_scheduler.group_weights]
Tap = 2.0        # 点击动作权重 2.0（更容易被选中）
Flick = 1.5      # 滑动动作权重 1.5
Idle = 1.0       # 待机动作权重 1.0
```

**说明：**
- 权重值越大，该组动作被选中的概率越高
- 留空则所有动作组权重相同（平均分配）

**示例：**

假设有以下动作组：
- Tap：3 个动作，权重 2.0
- Flick：2 个动作，权重 1.5
- Idle：1 个动作，权重 1.0

则每个动作被选中的概率：
- Tap 动作：\( \frac{2.0 \times 3}{2.0 \times 3 + 1.5 \times 2 + 1.0 \times 1} = \frac{6}{6 + 3 + 1} = \frac{6}{10} = 60\% \)
- Flick 动作：\( \frac{1.5 \times 2}{10} = \frac{3}{10} = 30\% \)
- Idle 动作：\( \frac{1.0 \times 1}{10} = \frac{1}{10} = 10\% \)

---

#### 动作组白名单

```toml
[animation_scheduler]
whitelist = ["Tap", "Flick"]  # 只使用 Tap 和 Flick 动作
```

**说明：**
- 如果设置白名单，只使用白名单中的动作组
- 留空则使用所有动作组（排除待机动作）

**使用场景：**
- 只想显示点击和滑动动作
- 某些动作不适合当前场景

---

#### 动作组黑名单

```toml
[animation_scheduler]
blacklist = ["Special", "Rare"]  # 排除 Special 和 Rare 动作
```

**说明：**
- 如果设置黑名单，排除黑名单中的动作组
- 留空则不排除任何动作组

**使用场景：**
- 排除特殊动作（如战斗、受伤等）
- 排除稀有动作（不想频繁出现）

---

## 四、代码示例

### 4.1 基础使用

```python
from src.frontend.core.managers.animation_scheduler import AnimationScheduler

# 创建调度器
scheduler = AnimationScheduler(model_path="data/live2d/model.model3.json")

# 配置时间参数
scheduler.set_idle_interval(30.0, 90.0)
scheduler.set_random_motion_duration(5.0)

# 启动调度器
scheduler.start()

# ... 程序运行 ...

# 清理资源
scheduler.cleanup()
```

---

### 4.2 使用信号

```python
from PyQt5.QtCore import QObject, pyqtSignal

# 创建调度器
scheduler = AnimationScheduler(model_path)

# 连接动作切换信号
scheduler.motion_changed.connect(
    lambda group, file: print(f"动作切换: {group} -> {file}")
)

# 连接状态切换信号
scheduler.state_changed.connect(
    lambda state: print(f"状态切换: {state}")  # "idle" 或 "random"
)

# 启动调度器
scheduler.start()
```

---

### 4.3 设置权重

```python
scheduler = AnimationScheduler(model_path)

# 设置动作组权重
scheduler.set_group_weights({
    "Tap": 2.0,      # 点击动作权重 2.0
    "Flick": 1.5,    # 滑动动作权重 1.5
    "Idle": 1.0,     # 待机动作权重 1.0
})

# 启动调度器
scheduler.start()
```

---

### 4.4 设置白名单

```python
scheduler = AnimationScheduler(model_path)

# 设置白名单（只使用 Tap 和 Flick 动作）
scheduler.set_group_whitelist(["Tap", "Flick"])

# 启动调度器
scheduler.start()
```

---

### 4.5 设置黑名单

```python
scheduler = AnimationScheduler(model_path)

# 设置黑名单（排除 Special 和 Rare 动作）
scheduler.set_group_blacklist(["Special", "Rare"])

# 启动调度器
scheduler.start()
```

---

### 4.6 在 Live2D 渲染器中使用

```python
from src.frontend.core.render.live2d_renderer import Live2DRenderer

# 创建渲染器（自动启用动画调度器）
renderer = Live2DRenderer(
    model_path="data/live2d/model.model3.json",
    enable_animation_scheduler=True  # 默认启用
)

# 初始化
renderer.initialize()

# 获取动画调度器
scheduler = renderer.get_animation_scheduler()

if scheduler:
    # 配置调度器
    scheduler.set_idle_interval(30.0, 90.0)
    
    # 连接信号
    scheduler.motion_changed.connect(
        lambda group, file: print(f"动作切换: {group}")
    )
```

---

### 4.7 动态控制

```python
scheduler = AnimationScheduler(model_path)

# 启动调度器
scheduler.start()

# ... 运行一段时间 ...

# 暂停调度器
scheduler.pause()

# ... 做其他事情 ...

# 恢复调度器
scheduler.resume()

# 停止调度器
scheduler.stop()
```

---

## 五、最佳实践

### 5.1 时间间隔选择

**原则：**
- 待机间隔不要太短（避免频繁切换）
- 随机动作持续时间不要太长（避免单调）

**推荐配置：**

```toml
[animation_scheduler]
# 桌面待机场景
idle_interval_min = 30.0
idle_interval_max = 90.0
random_motion_duration = 5.0

# 聊天陪玩场景
# idle_interval_min = 10.0
# idle_interval_max = 30.0
# random_motion_duration = 3.0

# 游戏陪玩场景
# idle_interval_min = 5.0
# idle_interval_max = 15.0
# random_motion_duration = 2.0
```

---

### 5.2 权重设置技巧

**原则：**
- 主要动作权重高
- 次要动作权重低
- 待机动作权重最低

**示例：**

```toml
[animation_scheduler.group_weights]
# 主要动作：点击、滑动
Tap = 2.0
Flick = 2.0

# 次要动作：其他互动
Pinch = 1.5
Shake = 1.5

# 待机动作
Idle = 1.0
```

---

### 5.3 白名单/黑名单使用

**场景 1：只使用简单动作**

```toml
[animation_scheduler]
whitelist = ["Tap", "Flick", "Idle"]
```

**场景 2：排除特殊动作**

```toml
[animation_scheduler]
blacklist = ["Special", "Rare", "Battle"]
```

**场景 3：配合权重使用**

```toml
[animation_scheduler.group_weights]
Tap = 2.0
Flick = 1.5
Idle = 1.0

[animation_scheduler]
blacklist = ["Special", "Rare"]
```

---

### 5.4 性能优化

**1. 避免频繁切换**

```toml
[animation_scheduler]
# 不好的配置：切换太频繁
# idle_interval_min = 1.0
# idle_interval_max = 3.0

# 好的配置：合理间隔
idle_interval_min = 30.0
idle_interval_max = 90.0
```

**2. 减少动作数量**

```toml
[animation_scheduler]
# 使用白名单减少可用动作
whitelist = ["Tap", "Flick", "Idle"]
```

**3. 低功耗模式**

```toml
[animation_scheduler]
# 延长待机间隔
idle_interval_min = 60.0
idle_interval_max = 120.0

# 缩短随机动作持续时间
random_motion_duration = 3.0
```

---

## 六、故障排查

### 6.1 动画不切换

**可能原因：**
1. 动画调度器未启用
2. 模型没有待机动作或随机动作
3. 时间间隔设置过大

**解决方法：**

```python
# 检查是否启用
print(scheduler.is_running())

# 查看可用动作
idle_motions = scheduler.get_idle_motions()
random_motions = scheduler.get_random_motions()
print(f"待机动作: {len(idle_motions)}")
print(f"随机动作: {len(random_motions)}")

# 缩短时间间隔测试
scheduler.set_idle_interval(5.0, 10.0)
```

---

### 6.2 某些动作不播放

**可能原因：**
1. 动作在黑名单中
2. 白名单设置不当
3. 权重设置过低

**解决方法：**

```python
# 检查白名单和黑名单
print(f"白名单: {scheduler.group_whitelist}")
print(f"黑名单: {scheduler.group_blacklist}")

# 检查权重
print(f"权重: {scheduler.group_weights}")

# 清空白名单和黑名单
scheduler.set_group_whitelist([])
scheduler.set_group_blacklist([])
```

---

### 6.3 动作切换不均匀

**可能原因：**
1. 权重设置不合理
2. 某个动作组动作数量过多

**解决方法：**

```python
# 查看每个动作组的动作数量
from collections import Counter
groups = Counter(m.group for m in scheduler.random_motions)
print(groups)

# 调整权重
scheduler.set_group_weights({
    "Tap": 1.0,      # 降低权重
    "Flick": 1.0,
    "Idle": 1.0,
})
```

---

## 七、测试

### 7.1 运行测试脚本

```bash
# 基础测试
python tests/test_animation_scheduler.py

# 测试带权重
# 修改 tests/test_animation_scheduler.py，取消注释 test_scheduler_with_weights()
python tests/test_animation_scheduler.py

# 测试带白名单
# 修改 tests/test_animation_scheduler.py，取消注释 test_scheduler_with_whitelist()
python tests/test_animation_scheduler.py
```

### 7.2 预期输出

```
======================================================================
动画调度器测试
======================================================================

✓ 模型文件存在: data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json

1. 创建动画调度器...
✓ 调度器创建成功

2. 模型信息:
  待机动作: 4 个
    - Idle_01 (4.0s)
    - Idle_02 (3.5s)
    - Idle_03 (4.2s)
    - Idle_04 (3.8s)
  随机动作: 12 个
    Tap: 4 个
    Flick: 3 个
    Pinch: 2 个
    Shake: 3 个

3. 配置调度器...
✓ 配置完成:
  待机间隔: 5-10 秒（测试用，实际为 30-90 秒）
  随机动作持续时间: 3 秒

4. 连接信号...
✓ 信号连接成功

5. 启动调度器...
✓ 调度器已启动

6. 观察动画切换（30 秒）...
   你应该看到动作在待机和随机动作之间自动切换

📊 状态切换: idle
📢 动作切换: Idle -> Idle_01.motion3.json
...
📊 状态切换: random
📢 动作切换: Tap -> Tap_01.motion3.json
...
📊 状态切换: idle
📢 动作切换: Idle -> Idle_02.motion3.json

7. 清理资源...
✓ 清理完成

======================================================================
测试完成！
======================================================================
```

---

## 八、常见问题

### Q1: 如何完全禁用动画调度器？

**方法 1：配置文件禁用**

```toml
[animation_scheduler]
enabled = false
```

**方法 2：代码禁用**

```python
renderer = Live2DRenderer(
    model_path="data/live2d/model.model3.json",
    enable_animation_scheduler=False  # 禁用调度器
)
```

---

### Q2: 如何手动控制动画？

**禁用调度器后，使用手动控制：**

```python
renderer = Live2DRenderer(
    model_path="data/live2d/model.model3.json",
    enable_animation_scheduler=False
)

renderer.initialize()
renderer.attach(parent)

# 手动设置动画状态
renderer.set_animation_state("happy")  # 播放 happy 动作
renderer.set_animation_state("idle")   # 播放 idle 动作
```

---

### Q3: 如何在运行时动态调整时间间隔？

```python
scheduler = renderer.get_animation_scheduler()

if scheduler:
    # 调整时间间隔
    scheduler.set_idle_interval(20.0, 60.0)
    scheduler.set_random_motion_duration(4.0)
```

---

### Q4: 如何监听动作切换？

```python
scheduler = renderer.get_animation_scheduler()

if scheduler:
    # 连接信号
    scheduler.motion_changed.connect(
        lambda group, file: print(f"动作切换: {group} -> {file}")
    )
    
    scheduler.state_changed.connect(
        lambda state: print(f"状态切换: {state}")
    )
```

---

### Q5: 动画调度器会影响性能吗？

**影响很小：**

- 调度器使用定时器，占用极少 CPU
- 切换动作时可能有短暂卡顿（取决于模型复杂度）
- 合理配置时间间隔可以进一步降低影响

**优化建议：**

```toml
[animation_scheduler]
# 延长待机间隔
idle_interval_min = 60.0
idle_interval_max = 120.0

# 缩短随机动作持续时间
random_motion_duration = 3.0

# 减少可用动作
whitelist = ["Tap", "Flick", "Idle"]
```

---

## 九、总结

### 9.1 核心功能

✅ 自动在待机动作和随机动作之间切换  
✅ 可配置的时间间隔和持续时间  
✅ 支持动作组权重  
✅ 支持白名单/黑名单  
✅ 实时监听动作切换信号  

### 9.2 使用建议

1. **初次使用**：使用默认配置，观察效果
2. **调整间隔**：根据使用场景调整时间参数
3. **优化动作**：使用权重、白名单/黑名单优化动作选择
4. **性能优化**：合理配置时间间隔和动作数量

### 9.3 下一步

- 查看完整配置示例：`config/templates/config.toml.template`
- 运行测试脚本：`python tests/test_animation_scheduler.py`
- 阅读源代码：`src/frontend/core/managers/animation_scheduler.py`

---

## 附录

### A. 配置示例

```toml
# 完整的动画调度器配置示例
[animation_scheduler]
# 是否启用
enabled = true

# 时间参数
idle_interval_min = 30.0
idle_interval_max = 90.0
random_motion_duration = 5.0

# 动作组权重
[animation_scheduler.group_weights]
Tap = 2.0
Flick = 1.5
Idle = 1.0

# 白名单
whitelist = []

# 黑名单
blacklist = ["Special", "Rare"]
```

### B. API 参考

#### AnimationScheduler

**初始化：**

```python
AnimationScheduler(model_path: str)
```

**配置方法：**

```python
set_idle_interval(min_seconds: float, max_seconds: float)
set_random_motion_duration(seconds: float)
set_group_weights(weights: dict[str, float])
set_group_whitelist(groups: list[str])
set_group_blacklist(groups: list[str])
```

**控制方法：**

```python
start()
pause()
resume()
stop()
cleanup()
```

**获取信息：**

```python
get_idle_motions() -> list[Motion]
get_random_motions() -> list[Motion]
is_running() -> bool
```

**信号：**

```python
motion_changed: pyqtSignal(str, str)  # (group_name, motion_file)
state_changed: pyqtSignal(str)      # # ("idle" | "random")
```

### C. 相关文档

- [Live2D 重构规划](./LIVE2D_REFACTORING_PLAN.md)
- [Live2D 模型信息工具](./g5-LIVE2D_MODEL_INFO_TOOL.md)
- [Pet 重构 TodoList](./t2-PET_REFACTORING_TODOLIST.md)

---

**文档结束**
