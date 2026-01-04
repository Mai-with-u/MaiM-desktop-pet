# views/bubble_input.py
from PyQt5.QtWidgets import (QWidget, QLineEdit, QPushButton, 
                            QHBoxLayout, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QCursor

class BubbleInput(QWidget):
    def __init__(self, parent=None, on_send=None):
        super().__init__(parent)
        self.on_send_callback = on_send
        self.init_ui()
        self.init_style()
        self.init_animation()

    def init_ui(self):
        # 主容器
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("对我说点什么吧...")
        self.input_field.setMinimumWidth(250)
        
        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # 布局
        layout = QHBoxLayout(self)
        layout.addWidget(self.input_field)
        layout.addWidget(self.send_btn)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 信号连接
        self.send_btn.clicked.connect(self._on_send)
        self.input_field.returnPressed.connect(self._on_send)

    def init_style(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f0f8ff, stop:1 #e6f3ff);
                border-radius: 15px;
                border: 2px solid #a0d1eb;
            }
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #c0ddec;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
                color: #333;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5cb860, stop:1 #4CAF50);
            }
        """)

    def init_animation(self):
        # 透明度动画
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def showEvent(self, event):
        self._animate_show()
        super().showEvent(event)

    def _animate_show(self):
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def _on_send(self):
        text = self.input_field.text().strip()
        if text and self.on_send_callback:
            self.on_send_callback(text)
        self.close()

    def close(self):
        self.input_field.clear()
        super().close()
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()

    def update_position(self):
        if not self.parent():
            return
        
        parent_rect = self.parent().geometry()
        screen = self.parent().screen().availableGeometry()
        
        # 计算位置（显示在宠物下方）
        x = parent_rect.center().x() - self.width() // 2
        y = parent_rect.bottom() + 10  # 在宠物底部下方10像素处
        
        # 边界检查
        x = max(screen.left() + 10, min(x, screen.right() - self.width() - 10))
        
        # 如果下方空间不足，自动调整到上方
        if y + self.height() > screen.bottom():
            y = parent_rect.top() - self.height() - 10  # 改为显示在上方
        
        y = max(screen.top() + 10, y)  # 确保不会超出屏幕上边界
        
        self.move(x, y)