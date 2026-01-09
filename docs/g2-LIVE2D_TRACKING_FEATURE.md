# Live2D 头部和眼睛跟踪功能文档

## 功能概述

Live2D 头部和眼睛跟踪功能允许 Live2D 模型根据鼠标移动做出自然的响应，包括头部转动、眼睛注视和身体微调。

## 功能特性

### 1. 平滑跟踪
- 使用线性插值实现平滑过渡
- 可配置的平滑因子（0.01-1.0）
- 60 FPS 更新频率确保流畅体验

### 2. 多维度控制   
- **头部旋转**：X 轴和 Y 轴独立控制
- **眼睛转动**：眼球跟随鼠标移动
- **身体微调**：身体轻微跟随头部转动

### 3. 灵敏度调节
- 可独立调节头部、眼睛和身体的灵敏度
- 预设合理的默认值
- 支持运行时动态调整

## 工作原理

### 数据流

```
鼠标移动 → EventManager
         ↓
    计算目标角度
         ↓
    平滑插值更新
         ↓
    RenderManager
         ↓
    Live2DRenderer
         ↓
    Live2DWidget
         ↓
    应用到 Live2D 模型参数
```

### 参数映射

| 参数名称 | 说明 | 范围 | 默认值 |
|---------|------|------|--------|
| `head_angle_x` | 头部 X 轴旋转角度 | -30° 到 30° | 0° |
| `head_angle_y` | 头部 Y 轴旋转角度 | -30° 到 30° | 0° |
| `eye_angle_x` | 眼睛 X 轴旋转角度 | -1.0 到 1.0 | 0° |
| `eye_angle_y` | 眼睛 Y 轴旋转角度 | -1.0 到 1.0 | 0° |
| `body_angle_x` | 身体 X 轴旋转角度 | -15° 到 15° | 0° |

## 使用方法

### 1. 自动启用

跟踪功能默认启用，无需额外配置。当使用 Live2D 渲染模式时，模型会自动跟踪鼠标。

### 2. 控制跟踪功能

```python
# 获取 EventManager 实例
from src.frontend.presentation.refactored_pet import refactored_pet
event_manager = refactored_pet.event_manager

# 禁用跟踪
event_manager.set_tracking_enabled(False)

# 启用跟踪
event_manager.set_tracking_enabled(True)
```

### 3. 调整灵敏度

```python
# 调整头部灵敏度（默认 30.0）
event_manager.set_tracking_sensitivity(head=45.0)

# 调整眼睛灵敏度（默认 1.0）
event_manager.set_tracking_sensitivity(eye=1.5)

# 调整身体灵敏度（默认 0.5）
event_manager.set_tracking_sensitivity(body=0.8)

# 调整平滑因子（默认 0.1，越小越平滑）
event_manager.set_tracking_sensitivity(smooth=0.05)

# 同时调整多个参数
event_manager.set_tracking_sensitivity(
    head=40.0,
    eye=1.2,
    body=0.6,
    smooth=0.08
)
```

### 4. 查看当前状态

```python
# 获取跟踪状态
status = event_manager.get_tracking_status()

print(f"跟踪启用: {status['enabled']}")
print(f"头部角度 X: {status['current_head_angle_x']:.2f}°")
print(f"头部角度 Y: {status['current_head_angle_y']:.2f}°")
print(f"眼睛角度 X: {status['current_eye_angle_x']:.2f}")
print(f"眼睛角度 Y: {status['current_eye_angle_y']:.2f}")
```

## 配置说明

### 灵敏度参数

- **head_sensitivity**: 头部转动灵敏度
  - 范围: 0.0 - 60.0
  - 推荐: 20.0 - 40.0
  - 值越大，头部转动幅度越大

- **eye_sensitivity**: 眼睛转动灵敏度
  - 范围: 0.0 - 5.0
  - 推荐: 0.5 - 2.0
  - 值越大，眼睛转动幅度越大

- **body_sensitivity**: 身体转动灵敏度（相对于头部）
  - 范围: 0.0 - 2.0
  - 推荐: 0.3 - 0.7
  - 通常设为头部灵敏度的 0.5 倍左右

- **smooth_factor**: 平滑因子
  - 范围: 0.01 - 1.0
  - 推荐: 0.05 - 0.15
  - 值越小，过渡越平滑但响应越慢

### 推荐配置

#### 自然模式（默认）
```python
event_manager.set_tracking_sensitivity(
    head=30.0,
    eye=1.0,
    body=0.5,
    smooth=0.1
)
```

#### 灵活模式
```python
event_manager.set_tracking_sensitivity(
    head=45.0,
    eye=1.5,
    body=0.8,
    smooth=0.08
)
```

#### 平静模式
```python
event_manager.set_tracking_sensitivity(
    head=20.0,
    eye=0.7,
    body=0.3,
    smooth=0.15
)
```

#### 快速响应模式
```python
event_manager.set_tracking_sensitivity(
    head=50.0,
    eye=2.0,
    body=1.0,
    smooth=0.05
)
```

## 技术实现

### 1. EventManager

**职责：**
- 监听鼠标移动事件
- 计算目标角度
- 平滑插值更新
- 定时器驱动（60 FPS）

**关键方法：**
```python
def _update_live2d_tracking(self, event):
    """计算目标角度"""
    rel_x = (event.x() / self.parent.width()) * 2.0 - 1.0
    rel_y = (event.y() / self.parent.height()) * 2.0 - 1.0
    
    self._target_head_angle_x = rel_x * self._head_sensitivity
    # ... 其他参数

def _smooth_update_live2d(self):
    """平滑更新角度"""
    self._current_head_angle_x += (
        self._target_head_angle_x - self._current_head_angle_x
    ) * self._smooth_factor
    # ... 其他参数
    
    self.render_manager.set_live2d_parameters(...)
```

### 2. RenderManager

**职责：**
- 接收跟踪参数
- 传递给 Live2D 渲染器

**关键方法：**
```python
def set_live2d_parameters(self, head_angle_x, head_angle_y, 
                          eye_angle_x, eye_angle_y, body_angle_x):
    """设置 Live2D 参数"""
    if self.renderer and self.current_mode == "live2d":
        self.renderer.set_parameters(...)
```

### 3. Live2DRenderer

**职责：**
- 接收参数
- 传递给 Live2DWidget

**关键方法：**
```python
def set_parameters(self, ...):
    """设置头部和眼睛参数"""
    if self.widget:
        self.widget.set_parameters(...)
```

### 4. Live2DWidget

**职责：**
- 存储参数
- 应用到 Live2D 模型

**关键方法：**
```python
def update_model(self):
    """更新模型状态"""
    self._try_set_parameter('ParamAngleX', self.head_angle_x)
    self._try_set_parameter('ParamEyeBallX', self.eye_angle_x)
    # ... 其他参数
```

## 常见问题

### Q1: 为什么模型没有跟踪鼠标？

**可能原因：**
1. 当前使用的是静态图片模式，不是 Live2D 模式
2. Live2D 库未安装或模型未加载
3. 跟踪功能被禁用

**解决方法：**
```python
# 检查渲染模式
print(refactored_pet.render_manager.current_mode)

# 检查 Live2D 是否可用
from src.frontend.core.render.live2d_renderer import Live2DRenderer
print(Live2DRenderer.is_available())

# 检查跟踪是否启用
status = refactored_pet.event_manager.get_tracking_status()
print(status['enabled'])
```

### Q2: 跟踪反应太慢/太快

**解决方法：**
调整平滑因子：
```python
# 反应太慢，减小平滑因子
event_manager.set_tracking_sensitivity(smooth=0.05)

# 反应太快，增大平滑因子
event_manager.set_tracking_sensitivity(smooth=0.2)
```

### Q3: 头部转动幅度太大/太小

**解决方法：**
调整头部灵敏度：
```python
# 转动太大
event_manager.set_tracking_sensitivity(head=20.0)

# 转动太小
event_manager.set_tracking_sensitivity(head=40.0)
```

### Q4: 眼睛转动不明显

**解决方法：**
调整眼睛灵敏度：
```python
event_manager.set_tracking_sensitivity(eye=2.0)
```

### Q5: 如何在代码中集成？

**示例：在聊天机器人中使用**
```python
async def handle_message(message):
    # 发送消息时禁用跟踪，让模型专注对话
    refactored_pet.event_manager.set_tracking_enabled(False)
    
    # 显示消息
    refactored_pet.bubble_manager.show_message(message)
    
    # 3 秒后重新启用跟踪
    await asyncio.sleep(3)
    refactored_pet.event_manager.set_tracking_enabled(True)
```

## 性能优化

### 1. 降低更新频率

如果性能不足，可以降低更新频率：

```python
# 在 EventManager.__init__ 中
self._smooth_timer.start(33)  # 30 FPS（默认 16ms = 60 FPS）
```

### 2. 减少平滑计算

```python
# 增大平滑因子，减少计算量
event_manager.set_tracking_sensitivity(smooth=0.2)
```

### 3. 禁用不必要的参数

```python
# 只启用头部跟踪
class EventManager:
    def _smooth_update_live2d(self):
        # 只更新头部参数
        if self.render_manager:
            self.render_manager.set_live2d_parameters(
                head_angle_x=self._current_head_angle_x,
                head_angle_y=self._current_head_angle_y
            )
```

## 未来扩展

### 计划中的功能

1. **鼠标悬停检测**
   - 检测鼠标是否悬停在特定区域
   - 触发不同反应

2. **多目标跟踪**
   - 支持跟踪多个焦点
   - 实现更自然的注视切换

3. **自动注视**
   - 模型自动看向重要内容
   - 如气泡消息、输入框等

4. **情绪相关跟踪**
   - 根据当前情绪状态调整跟踪行为
   - 开心时更活跃，悲伤时更安静

5. **配置持久化**
   - 保存用户偏好设置
   - 支持不同场景的预设

## 相关文档

- [Live2D 重构计划](./LIVE2D_REFACTORING_PLAN.md)
- [渲染管理器文档](../src/frontend/core/managers/render_manager.py)
- [事件管理器文档](../src/frontend/core/managers/event_manager.py)

## 更新日志

### v1.0.0 (2026-01-10)
- ✨ 初始版本
- ✨ 实现头部、眼睛和身体跟踪
- ✨ 支持平滑过渡
- ✨ 可配置灵敏度参数
- ✨ 支持动态启用/禁用

---

**文档版本：** v1.0.0  
**最后更新：** 2026-01-10  
**维护者：** MaiM Team