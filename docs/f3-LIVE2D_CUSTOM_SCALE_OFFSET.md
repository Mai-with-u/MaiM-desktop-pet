# Live2D 自定义缩放和偏移功能

## 功能概述

Live2D 渲染器支持自定义缩放比例和偏移位置，让你能够精确控制 Live2D 模型在窗口中的显示效果。

## 配置参数

在 `config.toml` 的 `[live2d]` 部分添加以下配置：

```toml
[live2d]
# ... 其他配置 ...

# 自定义缩放比例
# 范围：0.5 ~ 3.0
# 留空或 0 表示自动根据窗口大小计算（默认行为）
# 示例：1.5 表示放大 1.5 倍
custom_scale = 0.0

# 自定义水平偏移
# 范围：-1.0 ~ 1.0
# 负值向左偏移，正值向右偏移
# 留空或 0 表示使用默认值
# 示例：0.1 表示向右偏移 10%
custom_offset_x = 0.0

# 自定义垂直偏移
# 范围：-1.0 ~ 1.0
# 负值向上偏移，正值向下偏移
# 留空或 0 表示使用默认值
# 示例：-0.2 表示向上偏移 20%
custom_offset_y = 0.0
```

## 参数说明

### 1. custom_scale（自定义缩放）

控制 Live2D 模型的整体缩放比例。

**参数范围：** `0.5` ~ `3.0`  
**默认值：** `0.0`（自动计算）

**使用建议：**

| 值 | 效果 | 适用场景 |
|----|------|----------|
| `0.0` | 自动计算（推荐） | 大多数情况，自动适应窗口大小 |
| `0.5` | 缩小到 50% | 需要显示更多背景 |
| `1.0` | 原始大小 | 标准 Live2D 模型 |
| `1.5` | 放大到 150% | 需要突出模型 |
| `2.0` | 放大到 200% | 大屏幕显示 |

**自动计算逻辑：**
- 根据窗口宽度和高度自动计算合适的缩放比例
- 确保模型完整显示在窗口内
- 保留 10% 的边距

### 2. custom_offset_x（水平偏移）

控制 Live2D 模型在水平方向的位置。

**参数范围：** `-1.0` ~ `1.0`  
**默认值：** `0.0`（居中）

**使用建议：**

| 值 | 效果 | 适用场景 |
|----|------|----------|
| `-0.5` | 向左偏移 50% | 模型偏右显示 |
| `-0.2` | 向左偏移 20% | 微调位置 |
| `0.0` | 居中（推荐） | 标准显示 |
| `0.2` | 向右偏移 20% | 微调位置 |
| `0.5` | 向右偏移 50% | 模型偏左显示 |

**方向说明：**
- **负值**：向左偏移
- **正值**：向右偏移
- **0**：居中显示

### 3. custom_offset_y（垂直偏移）

控制 Live2D 模型在垂直方向的位置。

**参数范围：** `-1.0` ~ `1.0`  
**默认值：** `0.0`（自动计算）

**使用建议：**

| 值 | 效果 | 适用场景 |
|----|------|----------|
| `-0.5` | 向上偏移 50% | 模型靠下显示 |
| `-0.2` | 向上偏移 20% | 微调位置 |
| `0.0` | 自动计算（推荐） | 根据高度自动调整 |
| `0.2` | 向下偏移 20% | 模型靠上显示 |
| `0.5` | 向下偏移 50% | 模型顶部显示 |

**自动计算逻辑（当 custom_offset_y = 0.0 时）：**
- 根据窗口高度自动调整垂直位置
- 窗口越高，向上偏移越多
- 确保模型头部始终可见

**方向说明：**
- **负值**：向上偏移
- **正值**：向下偏移
- **0**：自动计算（推荐）

## 配置示例

### 示例 1：默认配置（推荐）

```toml
[live2d]
custom_scale = 0.0      # 自动缩放
custom_offset_x = 0.0   # 水平居中
custom_offset_y = 0.0   # 垂直自动调整
```

**效果：** 自动适应窗口大小，居中显示

### 示例 2：放大显示

```toml
[live2d]
custom_scale = 1.5      # 放大 1.5 倍
custom_offset_x = 0.0   # 水平居中
custom_offset_y = -0.1  # 向上微调
```

**效果：** 模型放大 1.5 倍，略向上偏移

### 示例 3：左下角显示

```toml
[live2d]
custom_scale = 1.2      # 放大 1.2 倍
custom_offset_x = -0.3  # 向左偏移 30%
custom_offset_y = 0.3   # 向下偏移 30%
```

**效果：** 模型显示在左下角

### 示例 4：右上角显示

```toml
[live2d]
custom_scale = 1.0      # 原始大小
custom_offset_x = 0.3   # 向右偏移 30%
custom_offset_y = -0.2  # 向上偏移 20%
```

**效果：** 模型显示在右上角

### 示例 5：精确微调

```toml
[live2d]
custom_scale = 0.0      # 自动缩放
custom_offset_x = 0.05  # 向右微调 5%
custom_offset_y = -0.05 # 向上微调 5%
```

**效果：** 自动缩放，位置微调

## 实现细节

### 1. 参数加载流程

```
config.toml
    ↓
RenderManager.load_config()
    ↓
加载 custom_scale, custom_offset_x, custom_offset_y
    ↓
传递给 Live2DRenderer.__init__()
    ↓
保存为实例属性
    ↓
update_size() 中使用
```

### 2. 缩放和偏移逻辑

```python
# 在 update_size() 方法中
def update_size(self, width: int, height: int):
    # 更新模型视口
    self.widget.model.Resize(width, height)
    
    # 使用自定义缩放或自动计算
    if self.custom_scale > 0:
        scale_factor = self.custom_scale
    else:
        scale_factor = self._calculate_scale_factor(width, height)
    
    self.widget.model.SetScale(scale_factor)
    
    # 使用自定义偏移或自动计算
    if self.custom_offset_x != 0 or self.custom_offset_y != 0:
        offset_x = self.custom_offset_x
        offset_y = self.custom_offset_y
    else:
        offset_x = 0.0
        offset_y = self._calculate_offset_y(height)
    
    self.widget.model.SetOffset(offset_x, offset_y)
```

### 3. 自动计算逻辑

#### 自动缩放计算

```python
def _calculate_scale_factor(self, width: int, height: int) -> float:
    """根据窗口大小计算缩放比例"""
    base_width = 400   # 基准宽度
    base_height = 600  # 基准高度
    
    # 计算宽度和高度的缩放比例
    width_scale = width / base_width
    height_scale = height / base_height
    
    # 使用较小的缩放比例以保持模型完整
    scale_factor = min(width_scale, height_scale)
    
    # 添加边距（90%）
    scale_factor *= 0.9
    
    # 限制范围
    scale_factor = max(0.5, min(3.0, scale_factor))
    
    return scale_factor
```

#### 自动偏移计算

```python
def _calculate_offset_y(self, height: int) -> float:
    """根据窗口高度计算垂直偏移"""
    base_height = 600  # 基准高度
    
    # 高度越大，向上偏移越多
    offset_y = -0.2 * (height / base_height)
    
    # 限制范围
    offset_y = max(-0.5, min(0.0, offset_y))
    
    return offset_y
```

## 调试技巧

### 1. 查看当前配置

启动程序后，查看日志文件 `logs/pet.log`：

```
加载渲染配置: use_live2d=True, model_path=data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json, allow_switch=True, custom_scale=1.5, custom_offset=(0.1, -0.2)
Live2D 渲染器大小更新: 400x600, 缩放: 1.5, 偏移: (0.1, -0.2)
```

### 2. 逐步调整

1. **先调整缩放**：从 `custom_scale = 0.0` 开始，逐步调整到合适大小
2. **再调整水平偏移**：调整 `custom_offset_x`，观察模型位置
3. **最后调整垂直偏移**：调整 `custom_offset_y`，微调位置

### 3. 参数范围测试

建议在以下范围内测试：

```toml
# 安全范围
custom_scale = 0.5 ~ 2.0    # 避免过大或过小
custom_offset_x = -0.4 ~ 0.4  # 避免完全移出屏幕
custom_offset_y = -0.4 ~ 0.4  # 避免完全移出屏幕
```

## 常见问题

### Q1: 模型显示不完整

**原因：** 缩放比例过大或偏移过度

**解决方法：**
- 减小 `custom_scale` 的值
- 调整 `custom_offset_x` 和 `custom_offset_y` 使模型居中
- 或设置为 `custom_scale = 0.0` 使用自动缩放

### Q2: 模型太小看不清

**原因：** 缩放比例过小

**解决方法：**
- 增大 `custom_scale` 的值（建议 1.2 ~ 1.8）
- 或设置为 `custom_scale = 0.0` 使用自动缩放

### Q3: 模型位置偏左/偏右

**原因：** 水平偏移设置不当

**解决方法：**
- 向左偏移：使用负值（如 `custom_offset_x = -0.2`）
- 向右偏移：使用正值（如 `custom_offset_x = 0.2`）
- 居中显示：设置为 `custom_offset_x = 0.0`

### Q4: 模型位置偏上/偏下

**原因：** 垂直偏移设置不当

**解决方法：**
- 向上偏移：使用负值（如 `custom_offset_y = -0.2`）
- 向下偏移：使用正值（如 `custom_offset_y = 0.2`）
- 自动调整：设置为 `custom_offset_y = 0.0`

### Q5: 配置修改后没有生效

**原因：** 程序未重启或配置文件格式错误

**解决方法：**
1. 检查 `config.toml` 文件格式是否正确
2. 重启程序使配置生效
3. 查看 `logs/pet.log` 确认配置是否正确加载

## 最佳实践

### 1. 推荐配置

大多数情况下，使用自动计算即可：

```toml
[live2d]
custom_scale = 0.0
custom_offset_x = 0.0
custom_offset_y = 0.0
```

### 2. 微调配置

如果需要微调位置，建议：

```toml
[live2d]
custom_scale = 0.0      # 自动缩放
custom_offset_x = 0.05  # 小幅度调整
custom_offset_y = -0.05 # 小幅度调整
```

### 3. 特殊布局配置

如果需要特殊的布局效果：

```toml
[live2d]
custom_scale = 1.2      # 略微放大
custom_offset_x = -0.3  # 向左偏移
custom_offset_y = 0.2   # 向下偏移
```

## 相关文档

- [Live2D 跟踪功能文档](./LIVE2D_TRACKING_FEATURE.md)
- [动态大小渲染文档](./DYNAMIC_SIZE_RENDERING.md)
- [配置文件说明](../config/README.md)

## 更新日志

- **2026-01-10**: 添加 Live2D 自定义缩放和偏移功能
  - 支持自定义缩放比例（custom_scale）
  - 支持自定义水平偏移（custom_offset_x）
  - 支持自定义垂直偏移（custom_offset_y）
  - 保持自动计算的默认行为