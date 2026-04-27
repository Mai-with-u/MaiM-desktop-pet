"""
聊天窗口内的气泡组件
用于显示聊天消息，支持接收和发送两种样式
"""

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QPen, QFontMetrics, QPixmap, QCursor
from typing import Literal, Optional
from config import load_config, get_scale_factor

config = load_config()
scale_factor = get_scale_factor(config)


class ChatBubble(QWidget):
    """聊天窗口内的单个消息气泡"""

    def __init__(self, parent=None, bubble_type: Literal["received", "sent"] = "received",
                 text: str = "", pixmap: Optional[QPixmap] = None):
        super().__init__(parent)

        self.bubble_type = bubble_type
        self.text_content = text
        self.original_pixmap = pixmap
        self.scaled_pixmap = None

        # 边距设置
        self._padding = int(12 * scale_factor)
        self._margin = int(10 * scale_factor)
        self._max_width = int(350 * scale_factor)

        # 颜色设置
        if bubble_type == "received":
            self.bg_color = QColor(240, 248, 255)  # 爱丽丝蓝
            self.text_color = QColor(50, 50, 50)
            self._alignment = Qt.AlignLeft
        else:
            self.bg_color = QColor(200, 255, 200)  # 浅绿色
            self.text_color = QColor(50, 50, 50)
            self._alignment = Qt.AlignRight

        # 圆角半径
        self._corner_radius = int(12 * scale_factor)

        # 字体
        self._font = QFont("Microsoft YaHei", int(12 * scale_factor))
        self.setFont(self._font)

        # 处理图片
        if self.original_pixmap and not self.original_pixmap.isNull():
            self._create_scaled_pixmap()

        # 计算并设置大小
        self._calculate_size()

    def _create_scaled_pixmap(self):
        """创建缩放后的图片"""
        max_img_width = int(200 * scale_factor)
        max_img_height = int(150 * scale_factor)

        width = self.original_pixmap.width()
        height = self.original_pixmap.height()

        # 计算缩放比例
        if width > max_img_width or height > max_img_height:
            ratio = min(max_img_width / width, max_img_height / height)
            scaled_width = int(width * ratio)
            scaled_height = int(height * ratio)
            self.scaled_pixmap = self.original_pixmap.scaled(
                scaled_width, scaled_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            self.scaled_pixmap = self.original_pixmap

    def _calculate_size(self):
        """计算气泡大小"""
        # 计算文字区域大小
        fm = QFontMetrics(self._font)

        if self.text_content:
            # 计算文字所需的宽度和高度
            text_rect = fm.boundingRect(
                0, 0, self._max_width - 2 * self._padding, 0,
                Qt.TextWordWrap,
                self.text_content
            )
            text_width = text_rect.width() + 2 * self._padding
            text_height = text_rect.height() + 2 * self._padding
        else:
            text_width = 0
            text_height = 0

        # 计算图片大小
        img_width = 0
        img_height = 0
        if self.scaled_pixmap:
            img_width = self.scaled_pixmap.width() + 2 * self._padding
            img_height = self.scaled_pixmap.height() + 2 * self._padding

        # 总大小
        total_width = max(text_width, img_width, int(80 * scale_factor))
        total_height = text_height + img_height

        self.setMinimumWidth(total_width)
        self.setMinimumHeight(total_height)
        self.setMaximumWidth(self._max_width + 2 * self._margin)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        """绘制气泡"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆角矩形背景
        rect = self.rect().adjusted(
            self._margin, 0,
            -self._margin, 0
        )

        painter.setBrush(self.bg_color)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(rect, self._corner_radius, self._corner_radius)

        # 绘制内容
        content_rect = rect.adjusted(self._padding, self._padding, -self._padding, -self._padding)

        # 如果有图片，绘制图片
        if self.scaled_pixmap:
            img_x = content_rect.x() + (content_rect.width() - self.scaled_pixmap.width()) // 2
            img_y = content_rect.y()
            painter.drawPixmap(img_x, img_y, self.scaled_pixmap)
            content_rect.adjust(0, self.scaled_pixmap.height() + int(5 * scale_factor), 0, 0)

        # 如果有文字，绘制文字
        if self.text_content:
            painter.setPen(self.text_color)
            painter.setFont(self._font)
            painter.drawText(content_rect, Qt.TextWordWrap, self.text_content)


class ChatNotice(QWidget):
    """聊天窗口中的低调系统提示。"""

    def __init__(self, parent=None, text: str = "", on_click=None):
        super().__init__(parent)
        self.on_click = on_click

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, int(6 * scale_factor), 0, int(6 * scale_factor))
        layout.setSpacing(0)

        self.label = QLabel(text, self)
        self.label.setObjectName("chat_notice_label")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(int(280 * scale_factor))
        self.label.setFont(QFont("Microsoft YaHei", int(9 * scale_factor)))
        self.label.setStyleSheet(f"""
            QLabel#chat_notice_label {{
                color: #8a8a8a;
                background-color: #f1f1f1;
                border: 1px solid #e5e5e5;
                border-radius: {int(9 * scale_factor)}px;
                padding: {int(3 * scale_factor)}px {int(9 * scale_factor)}px;
            }}
        """)

        layout.addStretch()
        layout.addWidget(self.label)
        layout.addStretch()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if self.on_click:
            self.setCursor(QCursor(Qt.PointingHandCursor))
            self.label.setCursor(QCursor(Qt.PointingHandCursor))
            self.label.mousePressEvent = self._handle_mouse_press

    def _handle_mouse_press(self, event):
        if event.button() == Qt.LeftButton and self.on_click:
            try:
                self.on_click(event)
            except TypeError as event_error:
                try:
                    self.on_click()
                except TypeError:
                    raise event_error
            event.accept()
            return
        super().mousePressEvent(event)

    def mousePressEvent(self, event):
        self._handle_mouse_press(event)


class ChatBubbleContainer(QWidget):
    """气泡容器，用于对齐气泡（左或右）"""

    def __init__(self, parent=None, bubble_type: Literal["received", "sent"] = "received"):
        super().__init__(parent)
        self.bubble_type = bubble_type

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, int(5 * scale_factor), 0, int(5 * scale_factor))

        # 根据类型设置对齐
        # received: 对方的消息 -> 左边
        # sent: 自己的消息 -> 右边
        if bubble_type == "received":
            self.bubble = ChatBubble(self, bubble_type="received")
            layout.addWidget(self.bubble)
            layout.addStretch()
        else:
            layout.addStretch()
            self.bubble = ChatBubble(self, bubble_type="sent")
            layout.addWidget(self.bubble)

    def set_content(self, text: str = "", pixmap: Optional[QPixmap] = None):
        """设置气泡内容"""
        self.bubble.text_content = text
        self.bubble.original_pixmap = pixmap
        if pixmap and not pixmap.isNull():
            self.bubble._create_scaled_pixmap()
        self.bubble._calculate_size()
        self.bubble.update()


class ChatBubbleList(QWidget):
    """聊天气泡列表，管理所有消息气泡"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._bubbles: list[QWidget] = []

        # 主布局（垂直排列）
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(int(10 * scale_factor), int(10 * scale_factor),
                                         int(10 * scale_factor), int(10 * scale_factor))
        self._layout.setSpacing(int(5 * scale_factor))
        self._layout.addStretch()  # 底部弹性空间，让消息从上往下排列

    def add_message(self, text: str = "", msg_type: Literal["received", "sent"] = "received",
                    pixmap: Optional[QPixmap] = None):
        """添加新消息"""
        container = ChatBubbleContainer(self, bubble_type=msg_type)
        container.set_content(text, pixmap)

        self._bubbles.append(container)
        self._layout.insertWidget(self._layout.count() - 1, container)  # 在 stretch 之前插入

    def add_notice(self, text: str, on_click=None):
        """添加低调系统提示，不作为聊天消息显示。"""
        if not text:
            return
        notice = ChatNotice(self, text=text, on_click=on_click)
        self._bubbles.append(notice)
        self._layout.insertWidget(self._layout.count() - 1, notice)

    def clear_all(self):
        """清空所有消息"""
        for container in self._bubbles:
            container.deleteLater()
        self._bubbles.clear()

    def get_bubble_count(self) -> int:
        """获取气泡数量"""
        return len(self._bubbles)
