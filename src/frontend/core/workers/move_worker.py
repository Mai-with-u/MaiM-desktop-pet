"""
移动工作线程
负责处理窗口拖动移动
"""

import logging
from typing import Optional

from PyQt5.QtCore import QThread, QPoint
from PyQt5.QtGui import QCursor
from src.frontend.signals import signals_bus

logger = logging.getLogger(__name__)


class MoveWorker(QThread):
    """
    移动工作线程
    
    职责：
    - 在独立线程中处理窗口移动
    - 控制移动频率
    - 响应停止信号
    """
    
    def __init__(self, start_pos: QPoint, pet_widget):
        """
        初始化移动工作线程
        
        Args:
            start_pos: 拖动起始偏移量
            pet_widget: 桌宠控件
        """
        super().__init__()
        self.start_pos = start_pos
        self.pet_widget = pet_widget
        self._active = True  # 线程运行状态标志
    
    def run(self):
        """线程主循环"""
        logger.debug("移动线程启动")
        
        while self._active:
            # 检查桌宠是否是焦点目标
            if not self.pet_widget.isActiveWindow():
                logger.debug("桌宠失去焦点，停止移动")
                self.stop()
                break
            
            # 获取当前光标位置
            current_pos = QCursor.pos()
            
            # 计算新窗口位置
            new_pos = current_pos - self.start_pos
            
            # 发送位置更新信号
            signals_bus.position_changed.emit(new_pos)
            
            # 控制更新频率（约 120 FPS）
            self.msleep(8)
        
        logger.debug("移动线程结束")
    
    def stop(self):
        """安全停止线程"""
        logger.debug("停止移动线程")
        self._active = False
