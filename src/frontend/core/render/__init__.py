"""
渲染器模块
包含渲染器接口和各种渲染器实现
"""

from .interfaces import IRenderer
from .static_renderer import StaticRenderer
from .live2d_renderer import Live2DRenderer

__all__ = [
    'IRenderer',
    'StaticRenderer',
    'Live2DRenderer'
]
