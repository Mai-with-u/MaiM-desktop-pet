from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath

class BubbleMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._load_style()
        # 添加阴影效果（需重写 paintEvent）
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def _load_style(self):
        """加载样式表"""
        try:
            with open('src/frontend/style_sheets/bubble_menu.css', 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("样式表文件未找到: src/frontend/style_sheets/bubble_menu.css")
            # 如果文件不存在，保持原始内联样式作为后备
            self.setStyleSheet("""
                QMenu {
                    background-color: #ffffff;
                    border-radius: 10px;
                    padding: 5px;
                    border: 1px solid #e0e0e0;
                }
                QMenu::item {
                    padding: 8px 20px;
                    color: #333;
                    border-radius: 5px;
                }
                QMenu::item:selected {
                    background-color: #4CAF50;
                    color: white;
                }
            """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        # 获取窗口尺寸并转为浮点数
        w, h = float(self.width()), float(self.height())
        path.addRoundedRect(0, 0, w, h, 10, 10)  # ✅ 使用 (x, y, w, h, rx, ry)
        
        painter.fillPath(path, QColor(255, 255, 255))
        super().paintEvent(event)
