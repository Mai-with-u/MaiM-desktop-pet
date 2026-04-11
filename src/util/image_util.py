"""
图片处理工具
提供 QPixmap 相关的转换和处理功能
"""

from PyQt5.QtCore import QBuffer, QIODevice, QByteArray
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import base64
import logging

logger = logging.getLogger(__name__)

# 默认缩放倍率（避免循环导入）
_DEFAULT_SCALE_FACTOR = 1.0


def get_scale_factor() -> float:
    """
    获取界面缩放倍率（延迟导入，避免循环依赖）

    Returns:
        float: 缩放倍率
    """
    try:
        from config import load_config, get_scale_factor as _get_scale_factor
        config = load_config()
        if config is None:
            return _DEFAULT_SCALE_FACTOR
        return _get_scale_factor(config)
    except ImportError:
        logger.warning("config 模块未加载，使用默认缩放倍率")
        return _DEFAULT_SCALE_FACTOR
    except Exception as e:
        logger.warning(f"获取缩放倍率失败: {e}，使用默认值")
        return _DEFAULT_SCALE_FACTOR


def pixmap_to_base64(
    pixmap: QPixmap,
    format: str = "PNG",
    add_header: bool = False,
    scale_size: tuple = None
) -> str:
    """
    将QPixmap转换为base64字符串

    Args:
        pixmap: 要转换的QPixmap
        format: 图片格式(PNG/JPG/BMP等)
        add_header: 是否添加data:image前缀
        scale_size: 可选，缩放尺寸(width, height)

    Returns:
        base64编码字符串

    Raises:
        ValueError: 如果 pixmap 无效
    """
    # 验证 pixmap
    if pixmap is None:
        raise ValueError("pixmap 参数不能为 None")

    if pixmap.isNull():
        raise ValueError("pixmap 为空图片，无法转换")

    try:
        # 验证缩放尺寸
        if scale_size:
            if not isinstance(scale_size, (tuple, list)) or len(scale_size) != 2:
                logger.warning(f"scale_size 格式错误: {scale_size}，忽略缩放")
            elif scale_size[0] <= 0 or scale_size[1] <= 0:
                logger.warning(f"scale_size 值无效: {scale_size}，忽略缩放")
            else:
                pixmap = pixmap.scaled(
                    scale_size[0], scale_size[1],
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)

        if not buffer.open(QIODevice.WriteOnly):
            raise ValueError("无法打开 QBuffer 进行写入")

        # 保存图片到 buffer
        if not pixmap.save(buffer, format):
            buffer.close()
            raise ValueError(f"无法将 pixmap 保存为 {format} 格式")

        buffer.close()

        # 转换为 base64
        base64_str = base64.b64encode(byte_array.data()).decode('ascii')

        if add_header:
            return f"data:image/{format.lower()};base64,{base64_str}"
        return base64_str

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"pixmap 转 base64 失败: {e}", exc_info=True)
        raise ValueError(f"图片转换失败: {e}") from e
