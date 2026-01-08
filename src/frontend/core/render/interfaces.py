"""
渲染器接口定义
定义所有渲染器必须实现的通用接口
"""

from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget


class IRenderer(ABC):
    """
    渲染器接口 - 定义所有渲染器的通用行为
    
    所有渲染器（静态图片、Live2D、视频等）都必须实现这个接口
    这样可以保证渲染器之间的一致性，并且易于切换和扩展
    """
    
    @abstractmethod
    def initialize(self):
        """
        初始化渲染器
        
        在这个方法中应该：
        - 加载必要的资源（图片、模型、纹理等）
        - 初始化渲染上下文
        - 设置初始状态
        
        Raises:
            Exception: 初始化失败时抛出异常
        """
        pass
    
    @abstractmethod
    def attach(self, parent: QWidget):
        """
        将渲染器附加到父控件
        
        Args:
            parent: 父控件，通常是 QWidget 或其子类
            
        在这个方法中应该：
        - 创建渲染所需的控件（QLabel、QOpenGLWidget 等）
        - 将控件添加到父控件中
        - 设置控件的布局和大小
        - 监听父控件的大小变化事件（如果需要）
        """
        pass
    
    def update_size(self, width: int, height: int):
        """
        更新渲染器大小
        
        Args:
            width: 新的宽度
            height: 新的高度
            
        在这个方法中应该：
        - 调整渲染控件的大小
        - 根据新的尺寸调整缩放比例
        - 调整模型的显示位置和偏移
        
        注意：
        - 这是一个可选方法，默认实现为空
        - Live2D 渲染器应该重写此方法以动态调整模型大小
        - 静态渲染器可以实现此方法以重新缩放图片
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        清理资源
        
        在这个方法中应该：
        - 释放所有加载的资源
        - 清理渲染上下文
        - 删除创建的控件
        
        注意：这个方法会在渲染器不再使用时调用
        """
        pass
    
    @abstractmethod
    def set_animation_state(self, state: str):
        """
        设置动画状态
        
        Args:
            state: 动画状态名称（如 "idle", "happy", "sad", "talking" 等）
            
        对于静态渲染器，可以记录警告或不做任何操作
        对于 Live2D 渲染器，应该播放对应的动作
        """
        pass
    
    @abstractmethod
    def set_expression(self, expression: str):
        """
        设置表情
        
        Args:
            expression: 表情名称（如 "normal", "happy", "sad", "angry" 等）
            
        对于静态渲染器，可以记录警告或不做任何操作
        对于 Live2D 渲染器，应该切换对应的表情
        """
        pass
    
    @abstractmethod
    def on_mouse_move(self, x: float, y: float):
        """
        鼠标移动回调
        
        Args:
            x: 鼠标相对位置 X（0.0 到 1.0）
            y: 鼠标相对位置 Y（0.0 到 1.0）
            
        用于实现鼠标追踪效果：
        - 静态渲染器：通常不需要实现
        - Live2D 渲染器：可以实现注视效果，让模型的眼睛跟随鼠标
        """
        pass
