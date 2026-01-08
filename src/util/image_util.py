from PyQt5.QtCore import QBuffer, QIODevice, QByteArray
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import base64

def get_scale_factor() -> float:
    """获取界面缩放倍率"""
    from config import load_config, get_scale_factor as _get_scale_factor
    config = load_config()
    return _get_scale_factor(config)

def pixmap_to_base64(
    pixmap: QPixmap, 
    format: str = "PNG", 
    add_header: bool = False,
    scale_size: tuple = None
) -> str:
    """
    将QPixmap转换为base64字符串
    
    :param pixmap: 要转换的QPixmap
    :param format: 图片格式(PNG/JPG/BMP等)
    :param add_header: 是否添加data:image前缀
    :param scale_size: 可选，缩放尺寸(width, height)
    :return: base64编码字符串
    """
    if scale_size:
        pixmap = pixmap.scaled(
            scale_size[0], scale_size[1],
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
    
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, format)
    base64_str = base64.b64encode(byte_array.data()).decode('ascii')
    
    if add_header:
        return f"data:image/{format.lower()};base64,{base64_str}"
    return base64_str
