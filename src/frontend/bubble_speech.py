from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QSize, QRect, QSequentialAnimationGroup
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QPixmap, QImage

from typing import Literal, Optional
        

class SpeechBubble(QLabel):
    _vertical_spacing = 5  # 气泡之间的垂直间距
    
    def __init__(self, parent=None, bubble_type="received", text: str = "", pixmap: Optional[QPixmap] = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 改为左对齐

        self.text_data = text
        self.original_pixmap = pixmap
        self.scaled_pixmap = None
        self.bubble_type = bubble_type  # "received" 或 "sent"
        
            # 添加边距和间距的初始化
        self._content_margin = 10  # 内容与气泡边缘的边距
        self._image_text_spacing = 5  # 图片和文字之间的间距

        # 如果有图片，创建缩略图
        if self.original_pixmap and not self.original_pixmap.isNull():
            self.create_scaled_pixmap()
        
        # 根据气泡类型设置不同样式
        if bubble_type == "received":
            self.bg_color = QColor(240, 248, 255)  # 爱丽丝蓝(接收气泡)
            self.follow_offset = QPoint(-100, -30)   # 向左偏移10px
        else:
            self.bg_color = QColor(200, 255, 200)  # 浅绿色(发送气泡)
            self.follow_offset = QPoint(100, -30)    # 向右偏移10px
            
        self.text_color = QColor(70, 70, 70)   # 深灰色
        self.setFont(QFont("Arial", 12, QFont.Bold))
        self.corner_radius = 10
        self.arrow_height = 10
        
        # 字体设置
        self.setFont(QFont("Microsoft YaHei", 12))
        
        # 动画组
        self.animation_group = QSequentialAnimationGroup(self)
    
    def create_scaled_pixmap(self):
        """创建缩放后的图片缩略图"""
        try:
            # 计算缩略图尺寸（最大250x250，保持宽高比）
            max_size = 250
            width = self.original_pixmap.width()
            height = self.original_pixmap.height()
            
            if width > height:
                scaled_width = min(width, max_size)
                scaled_height = int(height * (scaled_width / width))
            else:
                scaled_height = min(height, max_size)
                scaled_width = int(width * (scaled_height / height))
            
            # 创建缩略图
            self.scaled_pixmap = self.original_pixmap.scaled(
                scaled_width, scaled_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
        except Exception as e:
            print(f"Failed to scale pixmap: {e}")
            self.scaled_pixmap = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆角矩形主体
        body_rect = self.rect().adjusted(0, 0, 0, -self.arrow_height)
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(body_rect, self.corner_radius, self.corner_radius)
        
        # 绘制箭头(根据气泡类型决定方向)
        path = QPainterPath()
        arrow_width = 20
        if self.bubble_type == "received":
            # 接收气泡箭头在左侧
            center_x = 30
        else:
            # 发送气泡箭头在右侧
            center_x = self.width() - 30
            
        path.moveTo(center_x - arrow_width//2, body_rect.height())
        path.lineTo(center_x, self.height())
        path.lineTo(center_x + arrow_width//2, body_rect.height())
        painter.drawPath(path)
        
        # 绘制内容（图片和/或文字）
        content_top = 5  # 顶部边距
        left_margin = 10  # 左边距
        right_margin = 10  # 右边距
        
        # 如果有图片，绘制图片
        if self.scaled_pixmap and not self.scaled_pixmap.isNull():
            # 图片居中显示
            img_x = (self.width() - self.scaled_pixmap.width()) // 2
            painter.drawPixmap(img_x, content_top, self.scaled_pixmap)
            content_top += self.scaled_pixmap.height() + 5  # 图片下方留5px间距
        
        # 如果有文字，绘制文字
        if self.text_data:
            text_rect = QRect(
                left_margin, content_top,
                self.width() - left_margin - right_margin,
                body_rect.height() - content_top
            )
            painter.setPen(self.text_color)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.TextWordWrap, self.text_data)

    def calculate_bubble_size(self):
        """计算包含图片和文字的气泡大小"""
        # 计算文字所需大小
        min_text_width = 100  # 最小文字宽度
        text_width = 300  # 最大文字宽度
        text_height = 0
        
        if self.text_data:
            text_rect = self.fontMetrics().boundingRect(
                QRect(0, 0, text_width - 2*self._content_margin, 0),
                Qt.TextWordWrap,
                self.text_data
            )
            text_height = text_rect.height()
            min_text_width = min(text_rect.width() + 2*self._content_margin, min_text_width)
        
        # 计算图片所需大小
        img_width = img_height = 0
        if self.scaled_pixmap:
            img_width = min(300, self.scaled_pixmap.width())  # 图片最大宽度
            img_height = int(img_width * (self.scaled_pixmap.height() / self.scaled_pixmap.width()))
            img_height = min(200, img_height)  # 图片最大高度
            
        # 计算总大小
        content_width = max(
            min_text_width,  # 确保至少是最小宽度
            img_width if self.scaled_pixmap else 0,
            text_width if self.text_data else 0
        ) + 2 * self._content_margin
        
        height = (img_height if self.scaled_pixmap else 0) + \
                (self._image_text_spacing if self.scaled_pixmap and self.text_data else 0) + \
                text_height + \
                2 * self._content_margin + \
                self.arrow_height
        
        return QSize(content_width, height)

    def show_message(self):
        """显示气泡消息"""
        size = self.calculate_bubble_size()
        self.resize(size)
        self.show()
        
    def fade_out(self):
        """淡出并移除气泡"""
        if self.animation_group.state() == QPropertyAnimation.Running:
            self.animation_group.stop()
        
        self.animation_group.clear()
        fade_anim = QPropertyAnimation(self, b"windowOpacity")
        fade_anim.setDuration(500)
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.0)
        fade_anim.finished.connect(self.deleteLater)  # 直接删除对象
        
        self.animation_group.addAnimation(fade_anim)
        self.animation_group.start()


class SpeechBubbleList():
    _active_bubbles : list[SpeechBubble]
    _vertical_spacing = 5
    
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self._active_bubbles = []  # 保存所有活动气泡

    def add_message(self, 
                  message: str = "", 
                  msg_type: Literal["received", "sent"] = "received",
                  pixmap: Optional[QPixmap] = None):
        """添加新消息（可以是文字、图片或两者都有）
        
        参数:
            message: 要显示的文本消息
            msg_type: 消息类型，"received"或"sent"
            pixmap: 要显示的图片(QPixmap对象)
        """
        print(1)
        new_bubble = SpeechBubble(
            parent=self.parent,
            bubble_type=msg_type,
            text=message,
            pixmap=pixmap
        )
        self._active_bubbles.append(new_bubble)
        new_bubble.show_message()
        self.update_position()
    
    def del_first_msg(self):
        if self._active_bubbles and self._active_bubbles[0]:
            self._active_bubbles[0].fade_out()
            del self._active_bubbles[0]
    
    def update_position(self):
        """更新所有活动气泡的位置，自动排列并处理边界情况"""
        if not self.parent or not hasattr(self.parent, 'geometry'):
            return

        # 获取屏幕和父对象几何信息
        screen_geo = QApplication.primaryScreen().availableGeometry()
        parent_rect = self.parent.geometry()
        
        # 计算基准位置
        center_x = parent_rect.center().x()
        base_y = parent_rect.top() - 30  # 初始Y位置(父对象上方30px)
        
        # 从下往上排列气泡
        total_height = 0
        visible_bubbles = [b for b in self._active_bubbles if b.isVisible()]
        
        for bubble in reversed(visible_bubbles):
            # 计算气泡宽度和高度
            bubble_size = bubble.size()
            bubble_width = bubble_size.width()
            bubble_height = bubble_size.height()
            
            # 根据气泡类型确定水平位置
            if bubble.bubble_type == "received":
                # 接收气泡：左侧对齐(距中心200px左侧)
                x_pos = max(screen_geo.left() + 10, 
                        center_x - 160 - bubble_width//2)
            else:
                # 发送气泡：右侧对齐(距中心200px右侧)
                x_pos = min(screen_geo.right() - bubble_width - 10,
                        center_x + 160 - bubble_width//2)
            
            # 计算垂直位置(从下往上排列)
            y_pos = base_y - total_height - bubble_height
            
            # 检查上方空间是否足够
            if y_pos < screen_geo.top():
                # 如果上方空间不足，改为显示在下方(从父对象底部开始)
                y_pos = parent_rect.bottom() + total_height + 30
                bubble.arrow_height = -abs(bubble.arrow_height)  # 箭头朝下
            else:
                bubble.arrow_height = abs(bubble.arrow_height)  # 箭头朝上
            
            # 最终边界检查
            x_pos = max(screen_geo.left() + 5, 
                    min(x_pos, screen_geo.right() - bubble_width - 5))
            y_pos = max(screen_geo.top() + 5,
                    min(y_pos, screen_geo.bottom() - bubble_height - 5))
            
            # 应用新位置
            bubble.move(int(x_pos), int(y_pos))
            
            # 更新累计高度(包括间距)
            total_height += bubble_height + self._vertical_spacing
            
            # 如果累计高度超过屏幕高度的一半，移除最旧的气泡
            if total_height > screen_geo.height() // 3:
                self.del_first_msg()