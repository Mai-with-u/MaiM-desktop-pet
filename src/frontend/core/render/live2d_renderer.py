"""
Live2D 渲染器实现
负责 Live2D 模型的渲染和交互
"""

from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QSurfaceFormat
import logging
import os

from .interfaces import IRenderer

logger = logging.getLogger(__name__)


class Live2DRenderer(IRenderer):
    """
    Live2D 渲染器
    
    使用 live2d-py 库在 QOpenGLWidget 中渲染 Live2D 模型
    """
    
    # Live2D 库是否可用
    _live2d_available = None
    _live2d_initialized = False
    
    def __init__(self, model_path: str):
        """
        初始化 Live2D 渲染器
        
        Args:
            model_path: Live2D 模型文件路径（.model3.json）
        """
        self.model_path = model_path
        self.widget: Live2DWidget = None
        self.timer: QTimer = None
        
        # 检查 Live2D 库是否可用
        if Live2DRenderer._live2d_available is None:
            Live2DRenderer._live2d_available = self._check_live2d_available()
    
    @staticmethod
    def _check_live2d_available() -> bool:
        """
        检查 Live2D 库是否可用
        
        Returns:
            bool: Live2D 库是否可用
        """
        try:
            import live2d.v3
            logger.info("Live2D 库可用 (live2d-py)")
            return True
        except ImportError as e:
            logger.warning(f"Live2D 库导入失败: {e}")
            logger.warning("请运行: pip install live2d-py PyOpenGL")
            return False
    
    @classmethod
    def is_available(cls) -> bool:
        """
        检查 Live2D 渲染器是否可用
        
        Returns:
            bool: 是否可用
        """
        if cls._live2d_available is None:
            cls._live2d_available = cls._check_live2d_available()
        return cls._live2d_available
    
    def initialize(self):
        """初始化渲染器"""
        if not self.is_available():
            raise ImportError("Live2D 库不可用，无法初始化 Live2D 渲染器")
        
        # 检查模型文件是否存在
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Live2D 模型文件不存在: {self.model_path}")
        
        logger.info(f"初始化 Live2D 渲染器: {self.model_path}")
        
        # 设置 OpenGL 格式（抗锯齿）
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        QSurfaceFormat.setDefaultFormat(fmt)
    
    def attach(self, parent):
        """
        附加到父控件
        
        Args:
            parent: 父控件（QWidget）
        """
        if not self.is_available():
            raise ImportError("Live2D 库不可用，无法附加 Live2D 渲染器")
        
        logger.info(f"附加 Live2D 渲染器到父控件，初始大小: {parent.width()}x{parent.height()}")
        
        # 创建 Live2D Widget
        self.widget = Live2DWidget(self.model_path, parent)
        
        # 设置初始大小
        self.update_size(parent.width(), parent.height())
        self.widget.show()
        
        # 监听父窗口大小变化
        parent.resizeEvent = self._on_parent_resize
        
        # 启动更新定时器（60 FPS）
        self.timer = QTimer()
        self.timer.timeout.connect(self.widget.update_model)
        self.timer.start(16)
        
        logger.info("Live2D 渲染器已附加并启动更新循环")
    
    def _on_parent_resize(self, event):
        """
        父窗口大小变化回调
        
        Args:
            event: QResizeEvent
        """
        # 调用原始的 resizeEvent
        if hasattr(event, 'oldSize'):
            old_size = event.oldSize()
            new_size = event.size()
            logger.debug(f"父窗口大小变化: {old_size.width()}x{old_size.height()} -> {new_size.width()}x{new_size.height()}")
        
        # 更新 Live2D 渲染器大小
        if self.widget:
            self.update_size(event.size().width(), event.size().height())
        
        # 接受事件
        event.accept()
    
    def update_size(self, width: int, height: int):
        """
        更新渲染器大小
        
        Args:
            width: 新宽度
            height: 新高度
        """
        if not self.widget:
            return
        
        # 更新 widget 几何信息
        self.widget.setGeometry(0, 0, width, height)
        
        # 更新模型的视口和缩放
        if self.widget.model:
            # 调整视口大小
            self.widget.model.Resize(width, height)
            
            # 根据窗口大小动态计算缩放比例
            scale_factor = self._calculate_scale_factor(width, height)
            self.widget.model.SetScale(scale_factor)
            
            # 调整垂直偏移以适应不同高度
            offset_y = self._calculate_offset_y(height)
            self.widget.model.SetOffset(0, offset_y)
            
            logger.debug(f"Live2D 渲染器大小更新: {width}x{height}, 缩放: {scale_factor}, 偏移: {offset_y}")
    
    def _calculate_scale_factor(self, width: int, height: int) -> float:
        """
        根据窗口大小计算合适的缩放比例
        
        Args:
            width: 窗口宽度
            height: 窗口高度
            
        Returns:
            float: 缩放比例
        """
        # 基准尺寸（根据实际模型调整）
        base_width = 400
        base_height = 600
        
        # 计算宽度和高度的缩放比例
        width_scale = width / base_width
        height_scale = height / base_height
        
        # 使用较小的缩放比例以保持模型完整显示
        scale_factor = min(width_scale, height_scale)
        
        # 添加一些边距（0.9 表示留 10% 的边距）
        scale_factor *= 0.9
        
        # 限制缩放范围
        scale_factor = max(0.5, min(3.0, scale_factor))
        
        return scale_factor
    
    def _calculate_offset_y(self, height: int) -> float:
        """
        根据窗口高度计算垂直偏移
        
        Args:
            height: 窗口高度
            
        Returns:
            float: 垂直偏移值
        """
        # 基准高度
        base_height = 600
        
        # 高度越大，向上偏移越多
        offset_y = -0.2 * (height / base_height)
        
        # 限制偏移范围
        offset_y = max(-0.5, min(0.0, offset_y))
        
        return offset_y
    
    def cleanup(self):
        """清理资源"""
        logger.info("清理 Live2D 渲染器资源")
        
        if self.timer:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
        
        if self.widget:
            self.widget.cleanup()
            self.widget.deleteLater()
            self.widget = None
        
        logger.info("Live2D 渲染器已清理")
    
    def update(self):
        """更新动画（由定时器自动调用）"""
        # 更新逻辑在 widget.update_model() 中处理
        pass
    
    def set_animation_state(self, state: str):
        """
        设置动画状态
        
        Args:
            state: 动画状态名称（如 "idle", "happy", "sad", "talking" 等）
        """
        if not self.widget or not self.widget.model:
            logger.warning(f"Live2D 模型未加载，无法设置动画状态: {state}")
            return
        
        # 根据状态映射到对应的动作组
        motion_group = self._map_state_to_motion_group(state)
        if motion_group:
            try:
                self.widget.model.StartMotion(motion_group, 0)
                logger.info(f"切换 Live2D 动作: {state} -> {motion_group}")
            except Exception as e:
                logger.warning(f"播放动作失败 {motion_group}: {e}")
    
    def set_expression(self, expression: str):
        """
        设置表情
        
        Args:
            expression: 表情名称（如 "normal", "happy", "sad", "angry" 等）
        """
        if not self.widget or not self.widget.model:
            logger.warning(f"Live2D 模型未加载，无法设置表情: {expression}")
            return
        
        # 尝试设置表情
        try:
            self.widget.model.SetExpression(expression)
            logger.info(f"切换 Live2D 表情: {expression}")
        except Exception as e:
            logger.warning(f"设置表情失败 {expression}: {e}")
    
    def on_mouse_move(self, x: float, y: float):
        """
        鼠标移动回调（用于注视效果）
        
        Args:
            x: 鼠标相对位置 X（0.0 到 1.0）
            y: 鼠标相对位置 Y（0.0 到 1.0）
        """
        if self.widget:
            # 将归一化的坐标转换为像素坐标
            self.widget.mouse_x = x * self.widget.width()
            self.widget.mouse_y = y * self.widget.height()
    
    def _map_state_to_motion_group(self, state: str) -> str:
        """
        将状态名称映射到 Live2D 动作组
        
        Args:
            state: 状态名称
            
        Returns:
            str: 动作组名称
        """
        # 映射表 - 根据实际模型的动作组调整
        motion_map = {
            "idle": "Idle",
            "normal": "Idle",
            "happy": "Idle",  # 如果没有 happy 动作，用 idle
            "sad": "Idle",    # 如果没有 sad 动作，用 idle
            "talking": "Tap", # 使用点击动作
            "tap": "Tap",
            "flick": "Flick",
            "flick_down": "FlickDown",
            "flick_up": "FlickUp",
        }
        
        return motion_map.get(state.lower(), "Idle")


class Live2DWidget(QOpenGLWidget):
    """
    Live2D OpenGL Widget
    
    负责实际的 Live2D 模型渲染
    """
    
    def __init__(self, model_path: str, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.model = None
        self.initialized = False
        self.mouse_x = 400
        self.mouse_y = 300
    
    def initializeGL(self):
        """初始化 OpenGL 上下文"""
        if self.initialized:
            return
        
        # 导入 Live2D 库
        from live2d.v3 import Model, glInit, init as live2d_init
        
        # 全局只初始化一次
        if not Live2DRenderer._live2d_initialized:
            live2d_init()
            glInit()
            Live2DRenderer._live2d_initialized = True
            logger.info("Live2D 框架已全局初始化")
        
        # 加载模型
        self.model = Model()
        self.model.LoadModelJson(self.model_path)
        self.model.CreateRenderer()
        
        # 设置模型显示位置和大小
        self.model.SetScale(1.5)
        self.model.SetOffset(0, -0.2)
        
        # 启用自动眨眼
        self.model.SetAutoBlink(True)
        
        self.initialized = True
        logger.info("Live2D 模型初始化成功")
    
    def paintGL(self):
        """绘制场景"""
        if not self.model:
            return
        
        from live2d.v3 import clearBuffer
        
        # 清除缓冲区
        clearBuffer()
        
        # 绘制模型
        self.model.Draw()
    
    def resizeGL(self, width, height):
        """调整窗口大小"""
        if self.model:
            self.model.Resize(width, height)
    
    def update_model(self):
        """更新模型状态"""
        if not self.model:
            return
        
        # 计算鼠标相对于中心的偏移
        center_x = self.width() / 2
        center_y = self.height() / 2
        dx = (self.mouse_x - center_x) / center_x
        dy = (self.mouse_y - center_y) / center_y
        
        # 设置眼睛跟随
        try:
            self.model.SetParameterValue('ParamEyeBallX', dx * 30)
        except:
            pass
        try:
            self.model.SetParameterValue('ParamEyeBallY', dy * 30)
        except:
            pass
        
        # 更新模型
        delta_time = 0.016  # 约 60 FPS
        self.model.Update(delta_time)
        self.model.UpdateBlink(delta_time)
        
        # 重绘
        self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()
    
    def cleanup(self):
        """清理资源"""
        if self.model:
            try:
                from live2d.v3 import glRelease
                glRelease()
            except:
                pass
            self.model = None
        self.initialized = False
