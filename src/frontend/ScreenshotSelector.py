from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect,QRectF
from PyQt5.QtGui import QPainter, QColor, QPen,QPainterPath 

class ScreenshotSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)  # 全屏覆盖
        
        # 框选变量
        self.start_pos = None
        self.end_pos = None
        self.selection_rect = QRect()
        
        # 界面样式
        self.mask_color = QColor(0, 0, 0, 100)  # 半透明黑色遮罩
        self.border_color = QColor(255, 255, 255)  # 白色边框
        self.border_width = 2
        
    def paintEvent(self, event):
        """绘制半透明遮罩和选择框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制全屏半透明遮罩
        painter.fillRect(self.rect(), self.mask_color)
        
        # 如果有选择区域，绘制透明区域和边框
        if not self.selection_rect.isNull():
            # 创建一个全屏路径，并减去选区
            full_path = QPainterPath()
            full_path.addRect(QRectF(self.rect()))
            
            selection_path = QPainterPath()
            selection_path.addRect(QRectF(self.selection_rect))
            
            # 使用 subtracted() 方法得到遮罩路径（全屏 - 选区）
            mask_path = full_path.subtracted(selection_path)
            
            # 绘制遮罩（只保留选区外的部分）
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.mask_color)
            painter.drawPath(mask_path)
            
            # 绘制边框
            painter.setPen(QPen(self.border_color, self.border_width))
            painter.setBrush(Qt.NoBrush)  # 确保边框内不填充
            painter.drawRect(self.selection_rect)

    def mousePressEvent(self, event):
        """鼠标按下开始选择"""
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动更新选择框"""
        if self.start_pos:
            self.end_pos = event.pos()
            self.selection_rect = QRect(
                min(self.start_pos.x(), self.end_pos.x()),
                min(self.start_pos.y(), self.end_pos.y()),
                abs(self.start_pos.x() - self.end_pos.x()),
                abs(self.start_pos.y() - self.end_pos.y())
            )
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放完成截图"""
        if event.button() == Qt.LeftButton and self.start_pos:
            # 先隐藏窗口确保截图无遮罩
            self.hide()  # 关键修改：先隐藏界面
            QApplication.processEvents()  # 确保界面立即隐藏
            
            # 获取屏幕截图（此时窗口已隐藏）
            screen = QApplication.primaryScreen()
            full_pixmap = screen.grabWindow(0)
            
            # 截取选定区域（使用窗口隐藏前记录的坐标）
            selected_pixmap = full_pixmap.copy(self.selection_rect)
            
            # 关闭选择器
            self.close()
            
            # 返回截图（通过信号或直接处理）
            self.on_screenshot_captured(selected_pixmap)

    def on_screenshot_captured(self, pixmap):
        """子类需重写此方法处理截图"""
        raise NotImplementedError