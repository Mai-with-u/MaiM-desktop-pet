# views/bubble_input.py
from PyQt5.QtWidgets import (QWidget, QLineEdit, QPushButton, 
                            QHBoxLayout, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QCursor, QFont
from config import load_config, get_scale_factor

class BubbleInput(QWidget):
    def __init__(self, parent=None, on_send=None):
        super().__init__(parent)
        self.on_send_callback = on_send
        
        # 加载配置
        config = load_config()
        self.scale_factor = get_scale_factor(config)
        
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
        self.input_field.setMinimumWidth(int(250 * self.scale_factor))
        self.input_field.setFont(QFont("Microsoft YaHei", int(12 * self.scale_factor)))
        
        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_btn.setFont(QFont("Microsoft YaHei", int(12 * self.scale_factor)))
        
        # 布局（应用缩放倍率）
        layout = QHBoxLayout(self)
        layout.addWidget(self.input_field)
        layout.addWidget(self.send_btn)
        layout.setContentsMargins(
            int(15 * self.scale_factor), 
            int(10 * self.scale_factor), 
            int(15 * self.scale_factor), 
            int(10 * self.scale_factor)
        )
        layout.setSpacing(int(10 * self.scale_factor))
        
        # 信号连接
        self.send_btn.clicked.connect(self._on_send)
        self.input_field.returnPressed.connect(self._on_send)

    def init_style(self):
        try:
            with open('src/frontend/style_sheets/bubble_input.css', 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("样式表文件未找到: src/frontend/style_sheets/bubble_input.css")
            # 如果文件不存在，保持原始内联样式作为后备（应用缩放倍率）
            self.setStyleSheet(f"""
                QWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f0f8ff, stop:1 #e6f3ff);
                    border-radius: {int(15 * self.scale_factor)}px;
                    border: {int(2 * self.scale_factor)}px solid #a0d1eb;
                }}
                QLineEdit {{
                    background: rgba(255, 255, 255, 0.9);
                    border: {int(1 * self.scale_factor)}px solid #c0ddec;
                    border-radius: {int(10 * self.scale_factor)}px;
                    padding: {int(8 * self.scale_factor)}px;
                    font-size: {int(14 * self.scale_factor)}px;
                    color: #333;
                }}
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #45a049);
                    color: white;
                    border: none;
                    border-radius: {int(8 * self.scale_factor)}px;
                    padding: {int(8 * self.scale_factor)}px {int(20 * self.scale_factor)}px;
                    font-weight: bold;
                    min-width: {int(60 * self.scale_factor)}px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5cb860, stop:1 #4CAF50);
                }}
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
        
        # 计算位置（显示在宠物下方，应用缩放倍率）
        x = parent_rect.center().x() - self.width() // 2
        y = parent_rect.bottom() + int(10 * self.scale_factor)  # 在宠物底部下方
        
        # 边界检查（应用缩放倍率）
        x = max(screen.left() + int(10 * self.scale_factor), 
                min(x, screen.right() - self.width() - int(10 * self.scale_factor)))
        
        # 如果下方空间不足，自动调整到上方
        if y + self.height() > screen.bottom():
            y = parent_rect.top() - self.height() - int(10 * self.scale_factor)  # 改为显示在上方
        
        y = max(screen.top() + int(10 * self.scale_factor), y)  # 确保不会超出屏幕上边界
        
        self.move(x, y)
