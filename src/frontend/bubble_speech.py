from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QSize, QRect, QSequentialAnimationGroup
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QPixmap, QImage

from typing import Literal, Optional, TYPE_CHECKING
import uuid
import time
import asyncio
from src.database import db_manager
from src.util.logger import logger
from src.shared.models.message import MessageBase
from config import scale_factor

if TYPE_CHECKING:
    pass
        

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
        
            # 添加边距和间距的初始化（应用缩放倍率）
        self._content_margin = int(10 * scale_factor)  # 内容与气泡边缘的边距
        self._image_text_spacing = int(5 * scale_factor)  # 图片和文字之间的间距

        # 如果有图片，创建缩略图
        if self.original_pixmap and not self.original_pixmap.isNull():
            self.create_scaled_pixmap()
        
        # 根据气泡类型设置不同样式
        if bubble_type == "received":
            self.bg_color = QColor(240, 248, 255)  # 爱丽丝蓝(接收气泡)
            self.follow_offset = QPoint(int(-100 * scale_factor), int(-30 * scale_factor))   # 向左偏移
        else:
            self.bg_color = QColor(200, 255, 200)  # 浅绿色(发送气泡)
            self.follow_offset = QPoint(int(100 * scale_factor), int(-30 * scale_factor))    # 向右偏移
            
        self.text_color = QColor(70, 70, 70)   # 深灰色
        self.setFont(QFont("Arial", int(12 * scale_factor), QFont.Bold))
        self.corner_radius = int(10 * scale_factor)
        self.arrow_height = int(10 * scale_factor)
        
        # 字体设置
        self.setFont(QFont("Microsoft YaHei", int(12 * scale_factor)))
        
        # 动画组
        self.animation_group = QSequentialAnimationGroup(self)
    
    def create_scaled_pixmap(self):
        """创建缩放后的图片缩略图"""
        try:
            # 计算缩略图尺寸（最大250x250，保持宽高比，应用全局缩放倍率）
            max_size = int(250 * scale_factor)
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
        
        # 绘制箭头(根据气泡类型决定方向，应用缩放倍率)
        path = QPainterPath()
        arrow_width = int(20 * scale_factor)
        if self.bubble_type == "received":
            # 接收气泡箭头在左侧
            center_x = int(30 * scale_factor)
        else:
            # 发送气泡箭头在右侧
            center_x = self.width() - int(30 * scale_factor)
            
        path.moveTo(center_x - arrow_width//2, body_rect.height())
        path.lineTo(center_x, self.height())
        path.lineTo(center_x + arrow_width//2, body_rect.height())
        painter.drawPath(path)
        
        # 绘制内容（图片和/或文字，应用缩放倍率）
        content_top = int(5 * scale_factor)  # 顶部边距
        left_margin = int(10 * scale_factor)  # 左边距
        right_margin = int(10 * scale_factor)  # 右边距
        
        # 如果有图片，绘制图片
        if self.scaled_pixmap and not self.scaled_pixmap.isNull():
            # 图片居中显示
            img_x = (self.width() - self.scaled_pixmap.width()) // 2
            painter.drawPixmap(img_x, content_top, self.scaled_pixmap)
            content_top += self.scaled_pixmap.height() + int(5 * scale_factor)  # 图片下方留间距
        
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
        """计算包含图片和文字的气泡大小（应用缩放倍率）"""
        # 计算文字所需大小（应用缩放倍率）
        min_text_width = int(100 * scale_factor)  # 最小文字宽度
        text_width = int(300 * scale_factor)  # 最大文字宽度
        text_height = 0
        
        if self.text_data:
            text_rect = self.fontMetrics().boundingRect(
                QRect(0, 0, text_width - 2*self._content_margin, 0),
                Qt.TextWordWrap,
                self.text_data
            )
            text_height = text_rect.height()
            min_text_width = min(text_rect.width() + 2*self._content_margin, min_text_width)
        
        # 计算图片所需大小（应用缩放倍率）
        img_width = img_height = 0
        if self.scaled_pixmap:
            img_width = min(int(300 * scale_factor), self.scaled_pixmap.width())  # 图片最大宽度
            img_height = int(img_width * (self.scaled_pixmap.height() / self.scaled_pixmap.width()))
            img_height = min(int(200 * scale_factor), img_height)  # 图片最大高度
            
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
    _vertical_spacing = int(5 * scale_factor)
    
    def __init__(self, parent=None, use_database: bool = True) -> None:
        self.parent = parent
        self._active_bubbles = []  # 保存所有活动气泡
        self.use_database = use_database  # 是否使用数据库存储

    def add_message(self, 
                  message: str | MessageBase = "", 
                  msg_type: Literal["received", "sent"] = "received",
                  pixmap: Optional[QPixmap] = None,
                  save_to_db: bool = True):
        """添加新消息（可以是文字、图片、MessageBase对象或两者都有）
        
        参数:
            message: 要显示的文本消息 或 MessageBase 对象
            msg_type: 消息类型，"received"或"sent"
            pixmap: 要显示的图片(QPixmap对象)
            save_to_db: 是否保存到数据库（默认True）
        """
        # 如果是 MessageBase 对象，提取信息
        message_obj = None
        text_content = ""
        
        if isinstance(message, MessageBase):
            message_obj = message
            text_content = message.message_content
            # 从 MessageBase 对象确定消息类型
            if message.user_id == "0":
                msg_type = "sent"
            else:
                msg_type = "received"
            # MessageBase 对象已经保存过，不再保存
            save_to_db = True
        else:
            text_content = message
        
        new_bubble = SpeechBubble(
            parent=self.parent,
            bubble_type=msg_type,
            text=text_content,
            pixmap=pixmap
        )
        self._active_bubbles.append(new_bubble)
        new_bubble.show_message()
        self.update_position()
        
        # 异步保存到数据库（不阻塞UI）
        if self.use_database and save_to_db:
            if message_obj:
                self._async_save(self._save_to_database(message_obj))
            else:
                self._async_save(self._save_message_to_db(text_content, msg_type))
    
    def _async_save(self, coro):
        """在后台线程中执行异步任务"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(coro, loop=loop)
            else:
                # 如果没有运行中的事件循环，创建新的
                asyncio.run(coro)
        except RuntimeError:
            # 如果没有事件循环，创建新的
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(coro)
                new_loop.close()
            except Exception as e:
                logger.error(f"异步保存失败: {e}")
    
    def del_first_msg(self):
        if self._active_bubbles and self._active_bubbles[0]:
            self._active_bubbles[0].fade_out()
            del self._active_bubbles[0]
    
    async def _save_to_database(self, message_obj: MessageBase):
        """将 MessageBase 对象保存到数据库"""
        if not self.use_database or not db_manager.is_initialized():
            return
        
        try:
            # 保存到数据库
            await db_manager.save_message(message_obj)
            logger.debug(f"消息已保存到数据库: {message_obj.message_id[:8]}...")
        except Exception as e:
            logger.error(f"保存消息到数据库失败: {e}")
    
    async def _save_message_to_db(self, text: str, msg_type: Literal["received", "sent"]):
        """将文本消息创建为 MessageBase 并保存到数据库"""
        if not self.use_database or not db_manager.is_initialized():
            return
        
        try:
            # 创建 MessageBase 对象
            if msg_type == "sent":
                message_obj = MessageBase.create_sent_message(text, user_nickname="桌面宠物")
            else:
                message_obj = MessageBase.create_received_message(text, user_nickname="用户")
            
            # 保存到数据库
            await db_manager.save_message(message_obj)
            logger.debug(f"消息已保存到数据库: {message_obj.message_id[:8]}...")
        except Exception as e:
            logger.error(f"保存消息到数据库失败: {e}")
    
    async def load_history(self, limit: int = 20):
        """从数据库加载历史消息
        
        参数:
            limit: 加载的消息数量
        """
        if not self.use_database or not db_manager.is_initialized():
            logger.warning("数据库未初始化，无法加载历史消息")
            return
        
        try:
            # 清空当前显示的消息
            self.clear_all()
            
            # 从数据库获取消息（按时间倒序）
            messages = await db_manager.get_messages(limit=limit)
            
            # 按时间顺序显示（从旧到新），所以需要反转列表
            messages = list(reversed(messages))
            
            for msg_dict in messages:
                # 从字典创建 MessageBase 对象
                message_obj = MessageBase.from_dict(msg_dict)
                
                # 直接使用 MessageBase 对象添加消息
                self.add_message(
                    message=message_obj,
                    save_to_db=False  # 避免重复保存
                )
            
            logger.info(f"已加载 {len(messages)} 条历史消息")
        except Exception as e:
            logger.error(f"加载历史消息失败: {e}")
    
    async def search_messages(self, keyword: str, limit: int = 20):
        """从数据库搜索消息并显示
        
        参数:
            keyword: 搜索关键词
            limit: 返回结果数量限制
        """
        if not self.use_database or not db_manager.is_initialized():
            logger.warning("数据库未初始化，无法搜索消息")
            return []
        
        try:
            # 从数据库搜索消息
            messages = await db_manager.search_messages(keyword, limit=limit)
            
            logger.info(f"搜索到 {len(messages)} 条包含'{keyword}'的消息")
            return messages
        except Exception as e:
            logger.error(f"搜索消息失败: {e}")
            return []
    
    def clear_all(self):
        """清空所有显示的消息气泡"""
        for bubble in self._active_bubbles:
            bubble.deleteLater()
        self._active_bubbles.clear()
        logger.info("已清空所有消息气泡")
    
    async def clear_database(self):
        """清空数据库中的所有消息"""
        if not self.use_database or not db_manager.is_initialized():
            logger.warning("数据库未初始化，无法清空数据库")
            return False
        
        try:
            # 清空数据库
            await db_manager.clear_all_messages()
            logger.info("已清空数据库中的所有消息")
            return True
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            return False
    
    def update_position(self):
        """更新所有活动气泡的位置，自动排列并处理边界情况"""
        if not self.parent or not hasattr(self.parent, 'geometry'):
            return

        # 获取屏幕和父对象几何信息
        screen_geo = QApplication.primaryScreen().availableGeometry()
        parent_rect = self.parent.geometry()
        
        # 计算基准位置（应用缩放倍率）
        center_x = parent_rect.center().x()
        base_y = parent_rect.top() - int(30 * scale_factor)  # 初始Y位置
        
        # 从下往上排列气泡
        total_height = 0
        visible_bubbles = [b for b in self._active_bubbles if b.isVisible()]
        
        for bubble in reversed(visible_bubbles):
            # 计算气泡宽度和高度
            bubble_size = bubble.size()
            bubble_width = bubble_size.width()
            bubble_height = bubble_size.height()
            
            # 根据气泡类型确定水平位置（应用缩放倍率）
            if bubble.bubble_type == "received":
                # 接收气泡：左侧对齐(距中心160px左侧)
                x_pos = max(screen_geo.left() + int(10 * scale_factor), 
                        center_x - int(160 * scale_factor) - bubble_width//2)
            else:
                # 发送气泡：右侧对齐(距中心160px右侧)
                x_pos = min(screen_geo.right() - bubble_width - int(10 * scale_factor),
                        center_x + int(160 * scale_factor) - bubble_width//2)
            
            # 计算垂直位置(从下往上排列)
            y_pos = base_y - total_height - bubble_height
            
            # 检查上方空间是否足够
            if y_pos < screen_geo.top():
                # 如果上方空间不足，改为显示在下方(从父对象底部开始)
                y_pos = parent_rect.bottom() + total_height + int(30 * scale_factor)
                bubble.arrow_height = -abs(bubble.arrow_height)  # 箭头朝下
            else:
                bubble.arrow_height = abs(bubble.arrow_height)  # 箭头朝上
            
            # 最终边界检查（应用缩放倍率）
            x_pos = max(screen_geo.left() + int(5 * scale_factor), 
                    min(x_pos, screen_geo.right() - bubble_width - int(5 * scale_factor)))
            y_pos = max(screen_geo.top() + int(5 * scale_factor),
                    min(y_pos, screen_geo.bottom() - bubble_height - int(5 * scale_factor)))
            
            # 应用新位置
            bubble.move(int(x_pos), int(y_pos))
            
            # 更新累计高度(包括间距)
            total_height += bubble_height + self._vertical_spacing
            
            # 如果累计高度超过屏幕高度的一半，移除最旧的气泡
            if total_height > screen_geo.height() // 3:
                self.del_first_msg()
