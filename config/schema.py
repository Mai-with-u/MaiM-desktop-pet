"""
配置模式定义
使用 Pydantic 进行配置验证
"""

from pydantic import BaseModel
from typing import Optional


class InterfaceConfig(BaseModel):
    """界面配置模型"""
    scale_factor: Optional[float] = 1.0


class RenderConfig(BaseModel):
    """渲染配置模型"""
    mode: Optional[str] = "static"
    allow_switch: Optional[bool] = True


class Live2DConfig(BaseModel):
    """Live2D 配置模型"""
    enabled: Optional[bool] = False
    model_path: Optional[str] = ""
    model_name: Optional[str] = ""
    physics_enabled: Optional[bool] = True
    render_quality: Optional[str] = "medium"
    gpu_acceleration: Optional[bool] = True
    custom_scale: Optional[float] = 0.0
    custom_offset_x: Optional[float] = 0.0
    custom_offset_y: Optional[float] = 0.0


class AnimationConfig(BaseModel):
    """动画配置模型"""
    default_state: Optional[str] = "idle"
    default_expression: Optional[str] = "normal"
    fps: Optional[int] = 60
    breathing_enabled: Optional[bool] = True


class PerformanceConfig(BaseModel):
    """性能配置模型"""
    max_fps: Optional[int] = 60
    vsync: Optional[bool] = True
    texture_cache_size: Optional[int] = 256


class DatabaseConfig(BaseModel):
    """数据库配置模型"""
    type: Optional[str] = "sqlite"
    path: Optional[str] = "data/chat.db"


class StateConfig(BaseModel):
    """状态配置模型"""
    locked: Optional[bool] = False
    position_x: Optional[int] = 100
    position_y: Optional[int] = 100


class Config(BaseModel):
    """主配置模型"""
    
    # 基础配置
    url: Optional[str] = None
    Nickname: Optional[str] = None
    userNickname: Optional[str] = None
    platform: str = "desktop-pet"
    hide_console: bool = True
    Screenshot_shortcuts: Optional[str] = None
    allow_multiple_source_conversion: bool = False  # 多桌宠连接适配，默认为关
    
    # 嵌套配置
    interface: Optional[InterfaceConfig] = None
    render: Optional[RenderConfig] = None
    live2d: Optional[Live2DConfig] = None
    animation: Optional[AnimationConfig] = None
    performance: Optional[PerformanceConfig] = None
    database: Optional[DatabaseConfig] = None
    state: Optional[StateConfig] = None
    
    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True