from PyQt5.QtCore import QObject, pyqtSignal , QPoint

class GlobalSignals(QObject):
    # 定义全局信号
    message_received = pyqtSignal(str)  # 参数类型: str
    position_changed = pyqtSignal(QPoint)  # 定义信号，用于传递新位置

# 创建全局信号总线实例
signals_bus = GlobalSignals()