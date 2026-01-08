# PyQt5 Live2D Demo 使用说明

## 概述

这是一个在 PyQt5 界面中显示 Live2D 模型的完整示例，展示了如何在桌面应用中集成 Live2D 角色。

## 运行 Demo

```bash
python tests/pyqt5_live2d_demo.py
```

## 功能特性

### 1. Live2D 模型渲染
- 使用 QOpenGLWidget 在 PyQt5 窗口中渲染 Live2D 模型
- 自动加载模型、纹理、动作等资源
- 支持 60 FPS 流畅渲染

### 2. 交互功能
- **眼睛跟随**：鼠标移动时，角色眼睛会跟随鼠标位置
- **自动眨眼**：启用自动眨眼功能，让角色更生动
- **窗口自适应**：调整窗口大小时，模型会自动适配

### 3. 控制面板
- 显示操作说明
- 重置位置按钮
- 退出按钮

## 模型信息

当前使用的模型：**桃濑日和 - PRO** (hiyori_pro_t11)

模型位置：`data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json`

### 已加载的动作

- Idle_0, Idle_1, Idle_2 - 待机动作
- Flick_0 - 点击动作
- FlickDown_0 - 向下滑动
- FlickUp_0 - 向上滑动
- Tap_0, Tap_1 - 点击动作
- Tap@Body_0 - 点击身体
- Flick@Body_0 - 滑动身体

## 依赖要求

已添加到 `requirements.txt`：
- `live2d-py==0.6.0.1` - Live2D Python 绑定
- `PyQt5==5.15.11` - Qt GUI 框架
- `PyOpenGL==3.1.6` - OpenGL 绑定
- `numpy==1.24.3` - 数值计算

## 技术实现

### 核心类

#### Live2DWidget
继承自 `QOpenGLWidget`，负责 Live2D 模型的渲染：

```python
class Live2DWidget(QOpenGLWidget):
    def initializeGL(self):
        """初始化 OpenGL 上下文和 Live2D"""
        live2d_init()
        glInit()
        self.model.LoadModelJson(model_path)
        self.model.CreateRenderer()
    
    def paintGL(self):
        """绘制场景"""
        clearBuffer()
        self.model.Draw()
    
    def update_model(self):
        """更新模型状态（眼睛跟随等）"""
        dx = (self.mouse_x - center_x) / center_x
        dy = (self.mouse_y - center_y) / center_y
        self.model.SetParameterValue('ParamEyeBallX', dx * 30)
        self.model.SetParameterValue('ParamEyeBallY', dy * 30)
        self.model.Update(0.016)
        self.model.UpdateBlink(0.016)
```

#### MainWindow
主窗口类，包含 Live2D Widget 和控制面板：

```python
class MainWindow(QMainWindow):
    def __init__(self, model_path):
        self.live2d_widget = Live2DWidget(model_path)
        self.timer = QTimer()
        self.timer.timeout.connect(self.live2d_widget.update_model)
        self.timer.start(16)  # 60 FPS
```

## 如何更换模型

修改 `tests/pyqt5_live2d_demo.py` 中的 `model_path`：

```python
model_path = "data/live2d/你的模型/runtime/模型文件.model3.json"
```

## 常见问题

### Q: 模型不显示？
A: 确保 model3.json 文件路径正确，并且模型文件完整。

### Q: 眼睛不跟随鼠标？
A: 某些模型参数名可能不同，代码已添加异常处理。

### Q: 性能问题？
A: 可以调整定时器间隔（当前 16ms = 60 FPS），或减少模型复杂度。

## 与主项目集成

这个 demo 展示了如何在 PyQt5 应用中集成 Live2D，可以轻松集成到 MaiM-desktop-pet 项目中：

### 集成步骤

1. 将 Live2DWidget 复制到项目
2. 在主窗口中添加该 widget
3. 添加定时器更新模型
4. 连接鼠标事件实现交互

### 示例代码

```python
from tests.pyqt5_live2d_demo import Live2DWidget

class PetWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建 Live2D widget
        self.live2d = Live2DWidget("data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json")
        self.setCentralWidget(self.live2d)
        
        # 启动更新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.live2d.update_model)
        self.timer.start(16)
```

## 扩展功能

### 1. 播放动作
```python
self.live2d_widget.model.StartMotion("Idle", 0)
```

### 2. 切换表情
```python
self.live2d_widget.model.SetExpression("exp_01")
```

### 3. 缩放模型
```python
self.live2d_widget.model.SetScale(scale_value)
```

### 4. 设置位置
```python
self.live2d_widget.model.SetOffset(x, y)
```

## 参考资料

- [Live2D Cubism SDK](https://www.live2d.com/sdk/)
- [live2d-py](https://github.com/wolfired/live2d-py)
- [PyQt5 文档](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

## 许可证

本 demo 使用的 Live2D 模型遵循 Live2D 示例模型使用许可：
- 普通用户和小规模企业可商业使用
- 中/大型企业只能用于内部试用
- 详见: https://www.live2d.com/zh-CHS/download/sample-data/
