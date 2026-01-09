"""
渲染管理器
负责管理所有渲染相关的功能
"""

import logging
import os
from typing import Optional

from ..render.interfaces import IRenderer
from ..render.static_renderer import StaticRenderer
from ..render.live2d_renderer import Live2DRenderer

logger = logging.getLogger(__name__)


class RenderManager:
    """
    渲染管理器 - 负责所有渲染相关功能
    
    职责：
    - 创建和管理渲染器
    - 切换渲染模式
    - 设置动画状态和表情
    - 处理鼠标移动事件
    """
    
    def __init__(self, parent):
        """
        初始化渲染管理器
        
        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.renderer: Optional[IRenderer] = None
        self.current_mode: str = None
        
        # 配置参数
        self.use_live2d: bool = False
        self.live2d_model_path: str = ""
        self.allow_switch: bool = True
        
        # Live2D 自定义缩放和偏移参数
        self.custom_scale: float = 0.0
        self.custom_offset_x: float = 0.0
        self.custom_offset_y: float = 0.0
        
        # 加载配置
        self.load_config()
        
        # 创建渲染器
        self.create_renderer()
    
    def load_config(self):
        """加载渲染配置"""
        try:
            from config import load_config
            config = load_config()
            
            # 使用属性访问配置
            render_config = getattr(config, 'render', None)
            live2d_config = getattr(config, 'live2d', None)
            
            # 获取渲染配置
            if render_config:
                render_mode = getattr(render_config, 'mode', 'static')
                self.allow_switch = getattr(render_config, 'allow_switch', True)
                
                # 判断是否使用 Live2D
                self.use_live2d = (render_mode == 'live2d')
            else:
                self.use_live2d = False
                self.allow_switch = True
            
            # 获取 Live2D 配置
            if live2d_config:
                self.live2d_model_path = getattr(live2d_config, 'model_path', '')
                # 覆盖使用 Live2D 的设置（优先使用 live2d.enabled）
                self.use_live2d = getattr(live2d_config, 'enabled', self.use_live2d)
                # 加载自定义缩放和偏移参数
                self.custom_scale = getattr(live2d_config, 'custom_scale', 0.0)
                self.custom_offset_x = getattr(live2d_config, 'custom_offset_x', 0.0)
                self.custom_offset_y = getattr(live2d_config, 'custom_offset_y', 0.0)
            else:
                self.live2d_model_path = ""
                self.custom_scale = 0.0
                self.custom_offset_x = 0.0
                self.custom_offset_y = 0.0
            
            logger.info(f"加载渲染配置: use_live2d={self.use_live2d}, "
                       f"model_path={self.live2d_model_path}, "
                       f"allow_switch={self.allow_switch}, "
                       f"custom_scale={self.custom_scale}, "
                       f"custom_offset=({self.custom_offset_x}, {self.custom_offset_y})")
        except Exception as e:
            logger.error(f"加载渲染配置失败: {e}")
            # 使用默认配置
            self.use_live2d = False
            self.live2d_model_path = ""
            self.allow_switch = True
    
    def create_renderer(self):
        """创建渲染器"""
        # 检查是否使用 Live2D
        if self.use_live2d and self.live2d_model_path:
            # 检查模型文件是否存在
            if os.path.exists(self.live2d_model_path):
                # 检查 Live2D 库是否可用
                if Live2DRenderer.is_available():
                    try:
                        self.renderer = Live2DRenderer(
                            self.live2d_model_path,
                            custom_scale=self.custom_scale,
                            custom_offset_x=self.custom_offset_x,
                            custom_offset_y=self.custom_offset_y
                        )
                        self.current_mode = "live2d"
                        logger.info("使用 Live2D 渲染器")
                        return
                    except Exception as e:
                        logger.error(f"创建 Live2D 渲染器失败: {e}")
                        logger.info("降级到静态图片渲染器")
                else:
                    logger.warning("Live2D 库不可用，使用静态图片渲染器")
            else:
                logger.warning(f"Live2D 模型文件不存在: {self.live2d_model_path}")
                logger.info("使用静态图片渲染器")
        
        # 使用静态图片渲染器
        self.renderer = StaticRenderer()
        self.current_mode = "static"
        logger.info("使用静态图片渲染器")
        
        # 初始化渲染器
        try:
            self.renderer.initialize()
        except Exception as e:
            logger.error(f"初始化渲染器失败: {e}")
            raise
    
    def attach_to(self, parent):
        """
        将渲染器附加到父控件
        
        Args:
            parent: 父控件
        """
        if self.renderer:
            self.renderer.attach(parent)
            logger.info(f"渲染器已附加到父控件")
        else:
            logger.error("渲染器未创建，无法附加")
    
    def switch_mode(self, mode: str):
        """
        切换渲染模式
        
        Args:
            mode: 目标模式（"static" 或 "live2d"）
        """
        if not self.allow_switch:
            logger.warning("不允许切换渲染模式")
            return
        
        if mode == self.current_mode:
            logger.info(f"已经是 {mode} 模式，无需切换")
            return
        
        logger.info(f"切换渲染模式: {self.current_mode} -> {mode}")
        
        # 销毁旧渲染器
        if self.renderer:
            self.renderer.cleanup()
            self.renderer = None
        
        # 创建新渲染器
        try:
            if mode == "live2d":
                if not self.live2d_model_path:
                    raise ValueError("Live2D 模型路径未配置")
                
                if not Live2DRenderer.is_available():
                    raise ImportError("Live2D 库不可用")
                
                self.renderer = Live2DRenderer(
                    self.live2d_model_path,
                    custom_scale=self.custom_scale,
                    custom_offset_x=self.custom_offset_x,
                    custom_offset_y=self.custom_offset_y
                )
            elif mode == "static":
                self.renderer = StaticRenderer()
            else:
                raise ValueError(f"未知的渲染模式: {mode}")
            
            self.current_mode = mode
            self.renderer.initialize()
            
            # 附加到父控件
            if hasattr(self.parent, 'render_container'):
                self.renderer.attach(self.parent.render_container)
            
            logger.info(f"渲染模式切换成功: {mode}")
        except Exception as e:
            logger.error(f"切换渲染模式失败: {e}")
            # 恢复到静态模式
            self.renderer = StaticRenderer()
            self.current_mode = "static"
            self.renderer.initialize()
            if hasattr(self.parent, 'render_container'):
                self.renderer.attach(self.parent.render_container)
            logger.info("已恢复到静态图片模式")
    
    def set_animation_state(self, state: str):
        """
        设置动画状态
        
        Args:
            state: 动画状态名称
        """
        if self.renderer:
            try:
                self.renderer.set_animation_state(state)
            except Exception as e:
                logger.error(f"设置动画状态失败: {e}")
        else:
            logger.warning("渲染器未创建，无法设置动画状态")
    
    def set_expression(self, expression: str):
        """
        设置表情
        
        Args:
            expression: 表情名称
        """
        if self.renderer:
            try:
                self.renderer.set_expression(expression)
            except Exception as e:
                logger.error(f"设置表情失败: {e}")
        else:
            logger.warning("渲染器未创建，无法设置表情")
    
    def handle_mouse_move(self, x: float, y: float):
        """
        处理鼠标移动（用于 Live2D 注视效果）
        
        Args:
            x: 鼠标相对位置 X（0.0 到 1.0）
            y: 鼠标相对位置 Y（0.0 到 1.0）
        """
        if self.renderer and self.current_mode == "live2d":
            try:
                self.renderer.on_mouse_move(x, y)
            except Exception as e:
                logger.error(f"处理鼠标移动失败: {e}")
    
    def set_live2d_parameters(self, head_angle_x: float = 0.0, head_angle_y: float = 0.0,
                             eye_angle_x: float = 0.0, eye_angle_y: float = 0.0,
                             body_angle_x: float = 0.0):
        """
        设置 Live2D 头部和眼睛跟踪参数
        
        Args:
            head_angle_x: 头部 X 轴旋转角度（度）
            head_angle_y: 头部 Y 轴旋转角度（度）
            eye_angle_x: 眼睛 X 轴旋转角度（度）
            eye_angle_y: 眼睛 Y 轴旋转角度（度）
            body_angle_x: 身体 X 轴旋转角度（度）
        """
        if self.renderer and self.current_mode == "live2d":
            try:
                # 检查渲染器是否支持参数设置
                if hasattr(self.renderer, 'set_parameters'):
                    self.renderer.set_parameters(
                        head_angle_x=head_angle_x,
                        head_angle_y=head_angle_y,
                        eye_angle_x=eye_angle_x,
                        eye_angle_y=eye_angle_y,
                        body_angle_x=body_angle_x
                    )
                else:
                    logger.debug("Live2D 渲染器不支持参数设置")
            except Exception as e:
                logger.error(f"设置 Live2D 参数失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        if self.renderer:
            self.renderer.cleanup()
            self.renderer = None
            logger.info("渲染管理器已清理")
