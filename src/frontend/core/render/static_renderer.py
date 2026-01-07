"""
静态图片渲染器
负责显示静态图片的渲染实现
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import logging

from .interfaces import IRenderer
from src.util.image_util import get_scale_factor

logger = logging.getLogger(__name__)


class StaticRenderer(IRenderer):
    """
    静态图片渲染器
    
    使用 QLabel 显示静态图片，不支持动画和交互效果
    这是最简单但最稳定的渲染方式
    """
    
    def __init__(self, image_path: str = "./img/small_maimai.png"):
        """
        初始化静态渲染器
        
        Args:
            image_path: 图片文件路径
        """
        self.label: QLabel = None
        self.image_path = image_path
        self.scale_factor = get_scale_factor()
        self.pixmap: QPixmap = None
        
    def initialize(self):
        """初始化渲染器"""
        logger.info(f"初始化静态图片渲染器: {self.image_path}")
        
        # 加载图片
        self.pixmap = QPixmap(self.image_path)
        
        if self.pixmap.isNull():
            raise FileNotFoundError(f"图片文件不存在或损坏: {self.image_path}")
        
        logger.info(f"图片加载成功: {self.pixmap.width()}x{self.pixmap.height()}")
    
    def attach(self, parent):
        """
        附加到父控件
        
        Args:
            parent: 父控件（QWidget）
        """
        self.label = QLabel(parent)
        
        # 应用缩放
        if self.scale_factor != 1.0:
            scaled_pixmap = self.pixmap.scaled(
                int(self.pixmap.width() * self.scale_factor),
                int(self.pixmap.height() * self.scale_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            scaled_pixmap = self.pixmap
        
        self.label.setPixmap(scaled_pixmap)
        self.label.resize(scaled_pixmap.size())
        self.label.setAlignment(Qt.AlignCenter)
        self.label.show()
        
        logger.info(f"静态图片已附加到父控件: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
    
    def cleanup(self):
        """清理资源"""
        if self.label:
            self.label.deleteLater()
            self.label = None
        
        self.pixmap = None
        logger.info("静态图片渲染器已清理")
    
    def set_animation_state(self, state: str):
        """
        设置动画状态
        
        静态渲染器不支持动画，这里记录警告
        
        Args:
            state: 动画状态名称
        """
        logger.warning(f"静态渲染器不支持设置动画状态: {state}")
    
    def set_expression(self, expression: str):
        """
        设置表情
        
        静态渲染器不支持表情，这里记录警告
        
        Args:
            expression: 表情名称
        """
        logger.warning(f"静态渲染器不支持设置表情: {expression}")
    
    def on_mouse_move(self, x: float, y: float):
        """
        鼠标移动回调
        
        静态渲染器不需要响应鼠标移动
        
        Args:
            x: 鼠标相对位置 X（0.0 到 1.0）
            y: 鼠标相对位置 Y（0.0 到 1.0）
        """
        # 静态渲染器不需要处理鼠标移动
        pass
    
    def update_image(self, new_path: str):
        """
        更新显示的图片
        
        Args:
            new_path: 新图片路径
        """
        self.image_path = new_path
        new_pixmap = QPixmap(new_path)
        
        if new_pixmap.isNull():
            logger.error(f"无法加载新图片: {new_path}")
            return
        
        # 应用缩放
        if self.scale_factor != 1.0:
            scaled_pixmap = new_pixmap.scaled(
                int(new_pixmap.width() * self.scale_factor),
                int(new_pixmap.height() * self.scale_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            scaled_pixmap = new_pixmap
        
        self.pixmap = new_pixmap
        
        if self.label:
            self.label.setPixmap(scaled_pixmap)
            self.label.resize(scaled_pixmap.size())
        
        logger.info(f"图片已更新: {new_path}")
