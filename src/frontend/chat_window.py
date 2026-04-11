"""
聊天窗口主组件
独立的聊天界面，支持显示历史消息和实时接收新消息
"""

import asyncio
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                              QPushButton, QScrollArea, QLabel, QApplication)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QIcon, QCursor

from src.frontend.chat_bubble import ChatBubbleList
from src.frontend.signals import signals_bus
from src.core.chat import chat_manager
from src.database import db_manager
from src.shared.models.message import MessageBase
from src.util.logger import logger
from config import load_config, get_scale_factor

config = load_config()
scale_factor = get_scale_factor(config)


class ChatWindow(QWidget):
    """独立聊天窗口"""

    _instance = None  # 单例实例

    def __init__(self, parent=None, pet_window=None):
        super().__init__(parent)
        self.pet_window = pet_window  # 桌宠主窗口引用
        self._history_loaded = False  # 历史消息加载标记

        # 窗口设置
        self.init_window()
        self.init_ui()
        self.init_signals()

        logger.info("聊天窗口已创建")

    def init_window(self):
        """初始化窗口属性"""
        self.setWindowTitle("聊天窗口")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_StyledBackground, True)

        # 窗口大小
        self.setMinimumSize(int(400 * scale_factor), int(500 * scale_factor))
        self.resize(int(450 * scale_factor), int(600 * scale_factor))

        # 加载样式表
        self._load_style()

    def init_ui(self):
        """初始化 UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏（可拖拽）
        self.header = self._create_header()
        main_layout.addWidget(self.header)

        # 消息显示区域
        self.message_area = self._create_message_area()
        main_layout.addWidget(self.message_area, 1)

        # 输入区域
        self.input_area = self._create_input_area()
        main_layout.addWidget(self.input_area)

    def _create_header(self) -> QWidget:
        """创建标题栏"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(int(40 * scale_factor))
        header.setCursor(QCursor(Qt.SizeAllCursor))  # 拖拽光标

        layout = QHBoxLayout(header)
        layout.setContentsMargins(int(15 * scale_factor), 0, int(10 * scale_factor), 0)

        # 标题
        title_label = QLabel("💬 聊天")
        title_label.setFont(QFont("Microsoft YaHei", int(14 * scale_factor), QFont.Bold))
        layout.addWidget(title_label)

        layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(int(30 * scale_factor), int(30 * scale_factor))
        close_btn.setFont(QFont("Arial", int(12 * scale_factor)))
        close_btn.clicked.connect(self._on_close_clicked)  # 点击隐藏而非关闭
        layout.addWidget(close_btn)

        # 拖拽相关
        header._drag_pos = None
        header.mousePressEvent = self._header_mouse_press
        header.mouseMoveEvent = self._header_mouse_move

        return header

    def _header_mouse_press(self, event):
        """标题栏鼠标按下"""
        if event.button() == Qt.LeftButton:
            self.header._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _header_mouse_move(self, event):
        """标题栏鼠标移动（拖拽窗口）"""
        if self.header._drag_pos:
            self.move(event.globalPos() - self.header._drag_pos)

    def _create_message_area(self) -> QScrollArea:
        """创建消息显示区域"""
        scroll_area = QScrollArea()
        scroll_area.setObjectName("message_area")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 消息列表容器
        self.bubble_list = ChatBubbleList()
        scroll_area.setWidget(self.bubble_list)

        return scroll_area

    def _create_input_area(self) -> QWidget:
        """创建输入区域"""
        input_widget = QWidget()
        input_widget.setObjectName("input_area")
        input_widget.setFixedHeight(int(50 * scale_factor))

        layout = QHBoxLayout(input_widget)
        layout.setContentsMargins(int(10 * scale_factor), int(8 * scale_factor),
                                   int(10 * scale_factor), int(8 * scale_factor))
        layout.setSpacing(int(10 * scale_factor))

        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setObjectName("input_field")
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setFont(QFont("Microsoft YaHei", int(12 * scale_factor)))
        self.input_field.returnPressed.connect(self._send_message)
        layout.addWidget(self.input_field, 1)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("send_btn")
        self.send_btn.setFont(QFont("Microsoft YaHei", int(12 * scale_factor)))
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_btn.clicked.connect(self._send_message)
        layout.addWidget(self.send_btn)

        return input_widget

    def _load_style(self):
        """加载样式表"""
        try:
            with open('src/frontend/style_sheets/chat_window.css', 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger.warning("样式表文件未找到，使用默认样式")
            self.setStyleSheet(self._get_default_style())

    def _get_default_style(self) -> str:
        """获取默认样式"""
        return f"""
            QWidget {{
                background-color: #f5f5f5;
            }}
            #header {{
                background-color: #4CAF50;
                border: none;
            }}
            #header QLabel {{
                color: white;
            }}
            #close_btn {{
                background-color: transparent;
                color: white;
                border: none;
                border-radius: {int(15 * scale_factor)}px;
            }}
            #close_btn:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            #message_area {{
                background-color: #ffffff;
                border: none;
            }}
            #input_area {{
                background-color: #f0f0f0;
                border-top: 1px solid #ddd;
            }}
            #input_field {{
                background-color: white;
                border: 1px solid #ccc;
                border-radius: {int(5 * scale_factor)}px;
                padding: {int(5 * scale_factor)}px;
            }}
            #send_btn {{
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: {int(5 * scale_factor)}px;
                padding: {int(8 * scale_factor)}px {int(15 * scale_factor)}px;
                min-width: {int(60 * scale_factor)}px;
            }}
            #send_btn:hover {{
                background-color: #45a049;
            }}
        """

    def init_signals(self):
        """初始化信号连接"""
        signals_bus.message_received.connect(self._on_message_received)

    def _on_message_received(self, text: str):
        """接收到新消息"""
        self.bubble_list.add_message(text=text, msg_type="received")
        self._scroll_to_bottom()

    def _send_message(self):
        """发送消息"""
        text = self.input_field.text().strip()
        if not text:
            return

        # 显示发送的消息
        self.bubble_list.add_message(text=text, msg_type="sent")
        self.input_field.clear()
        self._scroll_to_bottom()

        # 发送消息到聊天管理器
        asyncio.create_task(chat_manager.send_message(text))

    def _scroll_to_bottom(self):
        """滚动到底部"""
        QTimer.singleShot(50, lambda: self.message_area.verticalScrollBar().setValue(
            self.message_area.verticalScrollBar().maximum()
        ))

    async def _load_history(self):
        """加载历史消息"""
        if not db_manager.is_initialized():
            logger.warning("数据库未初始化，无法加载历史消息")
            return

        try:
            messages = await db_manager.get_messages(limit=50)
            messages = list(reversed(messages))  # 从旧到新

            for msg_dict in messages:
                message_obj = MessageBase.from_dict(msg_dict)

                # 判断消息类型：user_id 为 "0" 表示发送
                if message_obj.user_id == "0":
                    msg_type = "sent"
                else:
                    msg_type = "received"

                self.bubble_list.add_message(
                    text=message_obj.message_content,
                    msg_type=msg_type
                )

            self._scroll_to_bottom()
            logger.info(f"已加载 {len(messages)} 条历史消息")

        except Exception as e:
            logger.error(f"加载历史消息失败: {e}")

    def show_window(self):
        """显示窗口"""
        # 如果窗口已显示，激活它
        if self.isVisible():
            self.activateWindow()
            self.raise_()
        else:
            # 计算位置（在桌宠附近）
            if self.pet_window:
                pet_geo = self.pet_window.geometry()
                x = pet_geo.left() - self.width() - int(20 * scale_factor)
                y = pet_geo.top()

                # 边界检查（安全获取屏幕）
                screen = QApplication.primaryScreen()
                if screen:
                    screen_geo = screen.availableGeometry()
                    if x < screen_geo.left():
                        x = pet_geo.right() + int(20 * scale_factor)
                    if y + self.height() > screen_geo.bottom():
                        y = screen_geo.bottom() - self.height()
                else:
                    # 无法获取屏幕时使用默认偏移
                    x = pet_geo.right() + int(20 * scale_factor)

                self.move(x, y)

            self.show()
            self.activateWindow()
            self.input_field.setFocus()

            # 首次显示时加载历史消息
            if not self._history_loaded:
                self._start_load_history()

    def _start_load_history(self):
        """启动历史消息加载（同步包装器）"""
        self._history_loaded = True
        asyncio.create_task(self._load_history())

    def _on_close_clicked(self):
        """点击关闭按钮时隐藏窗口"""
        self.hide()
        logger.info("聊天窗口已隐藏")

    def closeEvent(self, event):
        """窗口关闭事件 - 只隐藏，不真正关闭"""
        event.ignore()  # 拒绝关闭事件
        self.hide()
        logger.info("聊天窗口已隐藏")

    @classmethod
    def get_instance(cls, parent=None, pet_window=None) -> 'ChatWindow':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(parent, pet_window)
        return cls._instance

    @classmethod
    def show_chat_window(cls, parent=None, pet_window=None):
        """显示聊天窗口（便捷方法）"""
        instance = cls.get_instance(parent, pet_window)
        instance.show_window()