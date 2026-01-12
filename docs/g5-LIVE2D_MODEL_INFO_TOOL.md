# Live2D 模型信息提取工具

## 概述

`Live2DModelInfoExtractor` 是一个用于从 Live2D 模型配置文件（`.model3.json`）中提取模型信息的工具。它可以自动解析模型文件，提取出模型支持的动作、表情、点击区域、参数分组等信息。

**文件位置：** `src/frontend/core/models/live2d_model_info.py`

## 功能特性

### 核心功能

1. **动作信息提取**
   - 提取所有动作分组（Idle、Tap、Flick 等）
   - 获取每个动作的详细信息（名称、持续时间、帧率、是否循环）
   - 支持获取特定类型的动作（待机、点击、滑动）

2. **模型资源信息**
   - 模型版本信息
   - 资源文件路径（Moc、纹理、物理、姿势文件）
   - 点击区域定义
   - 参数分组信息

3. **便捷查询方法**
   - `get_idle_motions()` - 获取待机动作
   - `get_tap_motions()` - 获取点击动作
   - `get_flick_motions()` - 获取滑动动作
   - `get_all_motions()` - 获取所有动作
   - `get_motion_groups()` - 获取所有动作分组

## 数据结构

### MotionInfo

动作信息数据类：

```python
@dataclass
class MotionInfo:
    group: str              # 动作分组名称
    file: str               # 动作文件路径
    name: str               # 动作名称（从文件名提取）
    duration: Optional[float] = None  # 动作持续时间（秒）
    fps: Optional[float] = None      # 帧率
    loop: bool = False               # 是否循环
    sound: Optional[str] = None      # 关联的声音文件
```

### Live2DModelInfo

模型信息数据类：

```python
@dataclass
class Live2DModelInfo:
    model_path: str  # 模型配置文件路径
    version: int  # Live2D 版本
    motions: Dict[str, List[MotionInfo]]  # 动作分组
    parameters: List[ParameterInfo]  # 参数列表
    hit_areas: List[HitAreaInfo]  # 点击区域
    groups: Dict[str, List[str]]  # 参数分组
    
    # 资源文件路径
    moc_file: Optional[str]
    texture_files: List[str]
    physics_file: Optional[str]
    pose_file: Optional[str]
    display_info_file: Optional[str]
```

## 使用方法

### 基本用法

```python
from src.frontend.core.models.live2d_model_info import Live2DModelInfoExtractor

# 创建提取器实例
extractor = Live2DModelInfoExtractor("path/to/model.model3.json")

# 提取模型信息
model_info = extractor.extract()

# 打印摘要信息
extractor.print_summary()
```

### 获取特定类型的动作

```python
# 获取所有待机动作
idle_motions = extractor.get_idle_motions()
for motion in idle_motions:
    print(f"动作名称: {motion.name}")
    print(f"持续时间: {motion.duration}秒")
    print(f"是否循环: {motion.loop}")

# 获取所有点击动作
tap_motions = extractor.get_tap_motions()

# 获取所有滑动动作
flick_motions = extractor.get_flick_motions()

# 获取所有动作
all_motions = extractor.get_all_motions()
```

### 获取动作分组

```python
# 获取所有动作分组
groups = extractor.get_motion_groups()
print(f"动作分组: {groups}")

# 获取指定分组的所有动作
tap_motions = extractor.get_motions_by_group("Tap")
```

### 查询模型信息

```python
from src.frontend.core.models.live2d_model_info import extract_model_info

# 使用便捷函数
model_info = extract_model_info("path/to/model.model3.json")

# 访问模型信息
print(f"Live2D 版本: {model_info.version}")
print(f"动作分组数: {len(model_info.motions)}")
print(f"点击区域数: {len(model_info.hit_areas)}")
print(f"纹理文件数: {len(model_info.texture_files)}")
```

## 测试

项目包含完整的测试套件，位于 `tests/test_live2d_model_info.py`。

### 运行测试

```bash
python tests/test_live2d_model_info.py
```

### 测试内容

测试套件包含以下测试：

1. **Hiyori 模型测试** - 测试 Hiyori Pro 模型的信息提取
2. **Mao 模型测试** - 测试 Mao Pro 模型的信息提取
3. **模型对比测试** - 对比两个模型的信息差异

### 测试输出示例

```
======================================================================
Live2D 模型信息
======================================================================
模型路径: data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json
Live2D 版本: 3

动作分组 (7 个):
  - Idle: 3 个动作
    • hiyori_m01: 4.70s (循环)
    • hiyori_m02: 5.93s (循环)
    • hiyori_m05: 8.57s (循环)
  - Tap: 2 个动作
    • hiyori_m07: 1.90s (循环)
    • hiyori_m08: 2.10s (循环)

参数分组 (2 个):
  - LipSync: ParamMouthOpenY
  - EyeBlink: ParamEyeLOpen, ParamEyeROpen

点击区域 (1 个):
  - Body (HitArea)
```

## 测试模型对比

工具可以对比不同模型之间的差异：

```
📊 模型对比:
  项目                   Hiyori          Mao
  -------------------- --------------- ---------------
  Live2D 版本            3               3
  动作分组数                7               2
  总动作数                 10              7
  点击区域数                1               2
  参数分组数                2               2

📋 动作分组对比:
  共有分组: Idle
  Hiyori 独有: FlickUp, Flick@Body, FlickDown, Tap@Body, Tap, Flick
  Mao 独有:
```

## 实际应用场景

### 场景 1：渲染器集成

在 Live2D 渲染器中使用：

```python
from src.frontend.core.models.live2d_model_info import Live2DModelInfoExtractor

class Live2DRenderer:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.extractor = Live2DModelInfoExtractor(model_path)
        self.model_info = self.extractor.extract()
        
        # 获取待机动作列表
        self.idle_motions = self.extractor.get_idle_motions()
        
        # 随机选择一个待机动作
        self.current_idle_motion = random.choice(self.idle_motions)
    
    def play_idle_motion(self):
        """播放待机动作"""
        if self.idle_motions:
            motion = random.choice(self.idle_motions)
            self.play_motion(motion.file)
```

### 场景 2：交互系统

在交互系统中根据点击区域选择动作：

```python
def on_tap(self, position: QPoint, hit_area: str):
    """处理点击事件"""
    if hit_area == "Body":
        # 获取点击身体动作
        tap_motions = self.extractor.get_motions_by_group("Tap@Body")
        if tap_motions:
            motion = random.choice(tap_motions)
            self.play_motion(motion.file)
```

### 场景 3：状态切换

根据应用状态切换动作：

```python
def set_pet_state(self, state: str):
    """设置宠物状态"""
    if state == "happy":
        motions = self.extractor.get_motions_by_group("Tap")
    elif state == "talking":
        motions = self.extractor.get_motions_by_group("Idle")
    else:
        motions = self.extractor.get_idle_motions()
    
    if motions:
        self.play_motion(motions[0].file)
```

### 场景 4：模型验证

在加载模型前验证模型完整性：

```python
def validate_model(model_path: str) -> bool:
    """验证模型是否完整"""
    extractor = Live2DModelInfoExtractor(model_path)
    model_info = extractor.extract()
    
    # 检查是否有待机动作
    idle_motions = extractor.get_idle_motions()
    if not idle_motions:
        print("警告: 模型没有待机动作")
        return False
    
    # 检查纹理文件
    if not model_info.texture_files:
        print("警告: 模型没有纹理文件")
        return False
    
    return True
```

## 高级用法

### 自定义动作过滤

```python
def get_long_motions(extractor: Live2DModelInfoExtractor, min_duration: float = 5.0):
    """获取持续时间大于指定值的动作"""
    long_motions = []
    for motion in extractor.get_all_motions():
        if motion.duration and motion.duration >= min_duration:
            long_motions.append(motion)
    return long_motions

# 使用
extractor = Live2DModelInfoExtractor("model.model3.json")
extractor.extract()

long_motions = get_long_motions(extractor, min_duration=5.0)
for motion in long_motions:
    print(f"{motion.name}: {motion.duration}秒")
```

### 按名称搜索动作

```python
def find_motion_by_name(extractor: Live2DModelInfoExtractor, name_pattern: str):
    """按名称模式搜索动作"""
    import re
    pattern = re.compile(name_pattern, re.IGNORECASE)
    return [m for m in extractor.get_all_motions() if pattern.search(m.name)]

# 使用
extractor = Live2DModelInfoExtractor("model.model3.json")
extractor.extract()

# 查找所有包含 "special" 的动作
special_motions = find_motion_by_name(extractor, "special")
```

## 性能考虑

1. **缓存机制** - 模型信息提取后可以缓存，避免重复解析
2. **延迟加载** - 动作详细信息（如持续时间）按需加载
3. **错误处理** - 文件读取失败时不会中断程序，而是输出警告

## 注意事项

1. **模型文件路径** - 必须提供 `.model3.json` 文件的完整路径
2. **文件编码** - 模型文件必须使用 UTF-8 编码
3. **动作文件** - 动作详细信息（.motion3.json）必须是有效的 JSON 格式
4. **相对路径** - 动作文件路径是相对于模型文件所在目录的

## 错误处理

工具内置了完善的错误处理机制：

```python
try:
    extractor = Live2DModelInfoExtractor("model.model3.json")
    model_info = extractor.extract()
except FileNotFoundError:
    print("模型文件不存在")
except json.JSONDecodeError:
    print("模型文件格式错误")
except Exception as e:
    print(f"未知错误: {e}")
```

## 扩展开发

### 添加新的数据类

```python
@dataclass
class ExpressionInfo:
    """表情信息"""
    id: str
    name: str
    file: str

@dataclass
class Live2DModelInfo:
    # ... 现有字段 ...
    expressions: List[ExpressionInfo] = field(default_factory=list)
```

### 添加新的提取方法

```python
class Live2DModelInfoExtractor:
    # ... 现有方法 ...
    
    def _extract_expressions(self, model_data: dict):
        """提取表情信息"""
        expressions_data = model_data.get('FileReferences', {}).get('Expressions', [])
        
        for expr_item in expressions_data:
            expr_info = ExpressionInfo(
                id=expr_item.get('Id', ''),
                name=expr_item.get('Name', ''),
                file=expr_item.get('File', '')
            )
            self.model_info.expressions.append(expr_info)
```

## 参考文档

- [Live2D Cubism 文档](https://docs.live2d.com/)
- [Live2D 模型规范](https://docs.live2d.com/cubism-sdk-manual/advanced/how-to-specify-model-ja/)
- [Python dataclass 文档](https://docs.python.org/3/library/dataclasses.html)

## 版本历史

### v1.0.0 (2026-01-13)

初始版本，包含以下功能：
- ✅ 基本模型信息提取
- ✅ 动作信息解析
- ✅ 资源文件路径提取
- ✅ 点击区域和参数分组提取
- ✅ 完整的测试套件
- ✅ 两个模型（Hiyori 和 Mao）的测试

## 贡献指南

如需添加新功能或修复问题，请：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本工具遵循项目的许可证。
