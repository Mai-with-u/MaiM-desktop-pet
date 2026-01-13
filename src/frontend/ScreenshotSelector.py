from PyQt5.QtWidgets import (QWidget, QApplication, QPushButton, QHBoxLayout, 
                            QVBoxLayout, QLabel, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, QRect, QRectF, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QCursor, QMouseEvent
from src.util.logger import logger


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
        
        # 调整选区的变量
        self.is_dragging = False
        self.is_resizing = False
        self.resize_handle_size = 10  # 调整手柄大小
        self.drag_start_pos = None
        self.original_rect = None
        self.resize_handle = None  # 当前正在调整的边或角
        
        # 界面样式
        self.mask_color = QColor(0, 0, 0, 100)  # 半透明黑色遮罩
        self.border_color = QColor(0, 174, 255)  # 蓝色边框
        self.border_width = 2
        
        # 确认面板
        self.confirm_panel = None
        self.show_confirm_panel = False
        
        # 创建选项栏面板
        self.option_panel = OptionPanel(self)
        self.option_panel.hide()
        self.option_panel.confirm.clicked.connect(self._confirm_screenshot)
        self.option_panel.cancel.clicked.connect(self._cancel_screenshot)
        self.option_panel.resel.clicked.connect(self._resel_selection)
        
        logger.info("截图选择器初始化完成")
        
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
            
            # 绘制蓝色边框
            painter.setPen(QPen(self.border_color, self.border_width))
            painter.setBrush(Qt.NoBrush)  # 确保边框内不填充
            painter.drawRect(self.selection_rect)
            
            # 绘制调整手柄（8个点：4个角 + 4个边）
            self._draw_resize_handles(painter)
    
    def _draw_resize_handles(self, painter):
        """绘制调整手柄"""
        handle_size = 8
        handle_color = QColor(255, 255, 255, 200)
        
        # 8个手柄位置
        handles = self._get_resize_handles()
        
        for handle_pos in handles:
            # 绘制白色手柄
            painter.setPen(QPen(self.border_color, 2))
            painter.setBrush(handle_color)
            painter.drawRect(
                handle_pos.x() - handle_size // 2,
                handle_pos.y() - handle_size // 2,
                handle_size,
                handle_size
            )
    
    def _update_option_panel_position(self):
        """更新选项栏位置"""
        if self.selection_rect.isNull():
            self.option_panel.hide()
            return
            
        # 选项栏面板位置：选区右下角下方
        panel_width = 350
        panel_height = 90
        margin = 10
        
        x = self.selection_rect.right() - panel_width
        y = self.selection_rect.bottom() + margin
        
        # 确保面板在屏幕内
        if x < 0:
            x = 0
        if y + panel_height > self.height():
            y = self.selection_rect.top() - panel_height - margin
        
        # 设置选项栏位置
        self.option_panel.setGeometry(x, y, panel_width, panel_height)
        self.option_panel.show()
    
    def _get_resize_handles(self):
        """获取8个调整手柄的位置"""
        if self.selection_rect.isNull():
            return []
            
        x, y, w, h = self.selection_rect.x(), self.selection_rect.y(), \
                       self.selection_rect.width(), self.selection_rect.height()
        
        # 8个点：左上、上中、右上、右中、右下、下中、左下、左中
        handles = [
            QPoint(x, y),          # 左上
            QPoint(x + w // 2, y), # 上中
            QPoint(x + w, y),      # 右上
            QPoint(x + w, y + h // 2), # 右中
            QPoint(x + w, y + h), # 右下
            QPoint(x + w // 2, y + h), # 下中
            QPoint(x, y + h),      # 左下
            QPoint(x, y + h // 2)  # 左中
        ]
        
        return handles
    
    def _get_resize_handle_at(self, pos):
        """判断鼠标位置是否在某个调整手柄上"""
        handles = self._get_resize_handles()
        handle_names = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w']
        
        for i, handle_pos in enumerate(handles):
            handle_rect = QRect(
                handle_pos.x() - self.resize_handle_size // 2,
                handle_pos.y() - self.resize_handle_size // 2,
                self.resize_handle_size,
                self.resize_handle_size
            )
            if handle_rect.contains(pos):
                return handle_names[i]
        
        return None
    
    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.LeftButton:
            if not self.selection_rect.isNull() and self.show_confirm_panel:
                # 已经在调整模式下，检查是否在调整手柄上
                handle = self._get_resize_handle_at(event.pos())
                if handle:
                    self.is_resizing = True
                    self.resize_handle = handle
                    self.drag_start_pos = event.pos()
                    self.original_rect = QRect(self.selection_rect)
                elif self.selection_rect.contains(event.pos()):
                    # 点击在选区内，准备移动
                    self.is_dragging = True
                    self.drag_start_pos = event.pos()
                    self.original_rect = QRect(self.selection_rect)
                else:
                    # 点击在选区外，重新选择
                    self.start_pos = event.pos()
                    self.end_pos = event.pos()
                    self.selection_rect = QRect()
                    self.show_confirm_panel = False
                    self.update()
            else:
                # 初始选择模式
                self.start_pos = event.pos()
                self.end_pos = event.pos()
                self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        # 更新鼠标光标样式
        if not self.selection_rect.isNull() and self.show_confirm_panel:
            handle = self._get_resize_handle_at(event.pos())
            if handle:
                self._set_cursor_for_handle(handle)
            elif self.selection_rect.contains(event.pos()):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.CrossCursor)
        
        # 处理选区调整
        if self.is_resizing:
            self._handle_resize(event)
        elif self.is_dragging:
            self._handle_drag(event)
        elif self.start_pos:
            # 正在创建选区
            self.end_pos = event.pos()
            self.selection_rect = QRect(
                min(self.start_pos.x(), self.end_pos.x()),
                min(self.start_pos.y(), self.end_pos.y()),
                abs(self.start_pos.x() - self.end_pos.x()),
                abs(self.start_pos.y() - self.end_pos.y())
            )
            self.update()
    
    def _set_cursor_for_handle(self, handle):
        """根据调整手柄设置光标样式"""
        cursor_map = {
            'nw': Qt.SizeFDiagCursor,
            'n': Qt.SizeVerCursor,
            'ne': Qt.SizeBDiagCursor,
            'e': Qt.SizeHorCursor,
            'se': Qt.SizeFDiagCursor,
            's': Qt.SizeVerCursor,
            'sw': Qt.SizeBDiagCursor,
            'w': Qt.SizeHorCursor
        }
        self.setCursor(cursor_map.get(handle, Qt.ArrowCursor))
    
    def _handle_resize(self, event):
        """处理选区大小调整"""
        dx = event.pos().x() - self.drag_start_pos.x()
        dy = event.pos().y() - self.drag_start_pos.y()
        
        rect = QRect(self.original_rect)
        
        # 根据不同的手柄调整矩形
        if 'w' in self.resize_handle:
            rect.setLeft(rect.left() + dx)
        if 'e' in self.resize_handle:
            rect.setRight(rect.right() + dx)
        if 'n' in self.resize_handle:
            rect.setTop(rect.top() + dy)
        if 's' in self.resize_handle:
            rect.setBottom(rect.bottom() + dy)
        
        # 确保矩形不颠倒
        rect = rect.normalized()
        
        # 确保最小尺寸
        if rect.width() < 10:
            if 'w' in self.resize_handle:
                rect.setLeft(rect.right() - 10)
            else:
                rect.setRight(rect.left() + 10)
        if rect.height() < 10:
            if 'n' in self.resize_handle:
                rect.setTop(rect.bottom() - 10)
            else:
                rect.setBottom(rect.top() + 10)
        
        self.selection_rect = rect
        self.update()
    
    def _handle_drag(self, event):
        """处理选区拖动"""
        dx = event.pos().x() - self.drag_start_pos.x()
        dy = event.pos().y() - self.drag_start_pos.y()
        
        self.selection_rect = QRect(
            self.original_rect.x() + dx,
            self.original_rect.y() + dy,
            self.original_rect.width(),
            self.original_rect.height()
        )
        self.update()
    
    def _resel_selection(self):
        """重新选择"""
        self.selection_rect = QRect()
        self.show_confirm_panel = False
        self.option_panel.hide()
        self.option_panel.clear_text()  # 清空文本输入框
        self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.LeftButton:
            if self.is_resizing:
                self.is_resizing = False
                self.resize_handle = None
                # 更新选项栏位置
                self._update_option_panel_position()
            elif self.is_dragging:
                self.is_dragging = False
                # 更新选项栏位置
                self._update_option_panel_position()
            elif self.start_pos:
                # 完成初始选择
                self.start_pos = None
                
                # 如果选区太小，取消选择
                if self.selection_rect.width() < 10 or self.selection_rect.height() < 10:
                    self.selection_rect = QRect()
                    self.show_confirm_panel = False
                    self.option_panel.hide()
                else:
                    # 显示选项面板
                    self.show_confirm_panel = True
                    self._update_option_panel_position()
                    logger.info(f"选区创建完成: {self.selection_rect}")
                
                self.update()
    
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter 键：确认截图
            self._confirm_screenshot()
        elif event.key() == Qt.Key_Escape:
            # Esc 键：取消
            self._cancel_screenshot()
        elif event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Delete/Backspace 键：重新选择
            self.selection_rect = QRect()
            self.show_confirm_panel = False
            self.update()
    
    def _cancel_screenshot(self):
        """取消截图"""
        logger.info("用户取消截图")
        # 隐藏窗口而不是关闭
        self.hide()
        # 隐藏选项面板
        self.option_panel.hide()
        # 调用取消回调
        self.on_screenshot_canceled()
    
    def _confirm_screenshot(self):
        """确认截图"""
        if self.selection_rect.isNull() or self.selection_rect.width() < 10 or self.selection_rect.height() < 10:
            logger.warning("选区无效，取消截图")
            self.close()
            return
        
        logger.info(f"确认截图，选区: {self.selection_rect}")
        
        # 获取输入的文本
        text = self.option_panel.get_text()
        
        # 隐藏窗口和选项面板
        self.option_panel.hide()
        self.hide()
        QApplication.processEvents()  # 确保界面立即隐藏
        
        # 获取屏幕截图（此时窗口已隐藏）
        screen = QApplication.primaryScreen()
        full_pixmap = screen.grabWindow(0)
        
        # 截取选定区域（使用窗口隐藏前记录的坐标）
        selected_pixmap = full_pixmap.copy(self.selection_rect)
        
        # 关闭选择器
        self.close()
        
        # 返回截图和文本（通过信号或直接处理）
        self.on_screenshot_captured(selected_pixmap, text)
    
    def closeEvent(self, event):
        """关闭事件"""
        # 隐藏选项面板
        if hasattr(self, 'option_panel'):
            self.option_panel.hide()
        super().closeEvent(event)
    
    def on_screenshot_captured(self, pixmap, text=""):
        """子类需重写此方法处理截图
        
        参数:
            pixmap: 截图 QPixmap
            text: 用户输入的文本（可选）
        """
        raise NotImplementedError
    
    def on_screenshot_canceled(self):
        """子类需重写此方法处理取消截图"""
        pass


class OptionPanel(QWidget):
    """截图选项面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(350, 90)
        
        # 创建界面
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 文本输入框容器
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 8, 10, 0)
        input_layout.setSpacing(8)
        
        # 文本输入框
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入文字说明（可选）...")
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.95);
                color: #333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
                background-color: rgba(255, 255, 255, 1);
            }
        """)
        
        input_layout.addWidget(self.text_input)
        main_layout.addLayout(input_layout)
        
        # 按钮容器
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 0, 10, 8)
        button_layout.setSpacing(8)
        
        # 确认按钮
        self.confirm = QPushButton("✓")
        self.confirm.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.confirm.setCursor(Qt.PointingHandCursor)
        self.confirm.setToolTip("确认截图 (Enter)")
        
        # 取消按钮
        self.cancel = QPushButton("✕")
        self.cancel.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.cancel.setCursor(Qt.PointingHandCursor)
        self.cancel.setToolTip("取消截图 (Esc)")
        
        # 重新选择按钮
        self.resel = QPushButton("↺")
        self.resel.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:pressed {
                background-color: #0062cc;
            }
        """)
        self.resel.setCursor(Qt.PointingHandCursor)
        self.resel.setToolTip("重新选择 (Delete)")
        
        # 添加到按钮布局
        button_layout.addWidget(self.confirm)
        button_layout.addWidget(self.cancel)
        button_layout.addWidget(self.resel)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def get_text(self) -> str:
        """获取输入的文本"""
        return self.text_input.text().strip()
    
    def clear_text(self):
        """清空文本输入框"""
        self.text_input.clear()
    
    def paintEvent(self, event):
        """绘制面板背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制深色半透明背景
        bg_color = QColor(30, 30, 30, 230)
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(bg_color)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)
