#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt5 Live2D Demo
在 PyQt5 界面中显示 Live2D 模型
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QLabel, QPushButton, QHBoxLayout, QOpenGLWidget)
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QSurfaceFormat
from live2d.v3 import Model, glInit, glRelease, clearBuffer, init as live2d_init


class Live2DWidget(QOpenGLWidget):
    """Live2D OpenGL Widget"""
    
    def __init__(self, model_path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.model = None
        self.initialized = False
        self.mouse_x = 400
        self.mouse_y = 300
        
        # 设置 OpenGL 格式
        fmt = QSurfaceFormat()
        fmt.setSamples(4)  # 抗锯齿
        QSurfaceFormat.setDefaultFormat(fmt)
    
    def initializeGL(self):
        """初始化 OpenGL 上下文"""
        if self.initialized:
            return
        
        # 初始化 Live2D
        live2d_init()
        glInit()
        
        # 加载模型
        self.model = Model()
        self.model.LoadModelJson(self.model_path)
        self.model.CreateRenderer()
        
        # 设置模型显示位置和大小
        self.model.SetScale(1.5)
        self.model.SetOffset(0, -0.2)
        
        # 启用自动眨眼
        self.model.SetAutoBlink(True)
        
        self.initialized = True
        print("Live2D 模型初始化成功")
    
    def paintGL(self):
        """绘制场景"""
        if not self.model:
            return
        
        # 清除缓冲区
        clearBuffer()
        
        # 绘制模型
        self.model.Draw()
    
    def resizeGL(self, width, height):
        """调整窗口大小"""
        if self.model:
            self.model.Resize(width, height)
    
    def update_model(self):
        """更新模型状态"""
        if not self.model:
            return
        
        # 计算鼠标相对于中心的偏移
        center_x = self.width() / 2
        center_y = self.height() / 2
        dx = (self.mouse_x - center_x) / center_x
        dy = (self.mouse_y - center_y) / center_y
        
        # 设置眼睛跟随
        try:
            self.model.SetParameterValue('ParamEyeBallX', dx * 30)
        except:
            pass
        try:
            self.model.SetParameterValue('ParamEyeBallY', dy * 30)
        except:
            pass
        
        # 更新模型
        delta_time = 0.016  # 约 60 FPS
        self.model.Update(delta_time)
        self.model.UpdateBlink(delta_time)
        
        # 重绘
        self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, model_path):
        super().__init__()
        self.model_path = model_path
        
        self.setWindowTitle("PyQt5 Live2D Demo")
        self.resize(1000, 700)
        
        # 创建中央 widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QHBoxLayout(central_widget)
        
        # 创建 Live2D widget
        self.live2d_widget = Live2DWidget(model_path)
        layout.addWidget(self.live2d_widget, stretch=3)
        
        # 创建控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel, stretch=1)
        
        # 创建定时器用于更新模型
        self.timer = QTimer()
        self.timer.timeout.connect(self.live2d_widget.update_model)
        self.timer.start(16)  # 约 60 FPS
    
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel("Live2D 控制面板")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # 说明
        info = QLabel(
            "操作说明:\n\n"
            "• 移动鼠标：角色眼睛跟随\n"
            "• 自动眨眼：已启用\n"
            "• 帧率：约 60 FPS\n\n"
            f"模型:\n{os.path.basename(self.model_path)}"
        )
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        # 重置按钮
        reset_btn = QPushButton("重置位置")
        reset_btn.clicked.connect(self.reset_position)
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(reset_btn)
        
        # 退出按钮
        exit_btn = QPushButton("退出")
        exit_btn.clicked.connect(self.close)
        exit_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 14px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        layout.addWidget(exit_btn)
        
        return panel
    
    def reset_position(self):
        """重置位置"""
        self.live2d_widget.mouse_x = self.live2d_widget.width() / 2
        self.live2d_widget.mouse_y = self.live2d_widget.height() / 2


def main():
    """主函数"""
    # 模型文件路径
    model_path = "data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json"
    
    # 检查模型是否存在
    if not os.path.exists(model_path):
        print(f"错误: 找不到模型文件 {model_path}")
        print("请确保模型文件存在于正确位置")
        return
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow(model_path)
    window.show()
    
    print("PyQt5 Live2D Demo 启动成功")
    print("移动鼠标查看效果，关闭窗口退出")
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
