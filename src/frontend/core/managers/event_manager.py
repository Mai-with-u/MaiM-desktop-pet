"""
事件管理器
负责统一处理所有窗口事件
"""

import logging
from typing import Optional

from PyQt5.QtCore import QObject, QPoint
from PyQt5.QtWidgets import QMenu

from ..workers.move_worker import MoveWorker
from src.frontend.signals import signals_bus

logger = logging.getLogger(__name__)


class EventManager(QObject):
    """
    事件管理器 - 负责所有事件处理
    
    职责：
    - 处理鼠标按下事件
    - 处理鼠标释放事件
    - 处理鼠标移动事件
    - 处理鼠标双击事件
    - 处理右键菜单
    - 管理窗口移动
    """
    
    def __init__(self, parent):
        """
        初始化事件管理器
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.parent = parent
        
        # 引用其他管理器
        self.render_manager = None
        self.state_manager = None
        self.bubble_manager = None
        self.screenshot_manager = None
        
        # 移动相关
        self.move_worker: Optional[MoveWorker] = None
        self.drag_start_position: Optional[QPoint] = None
    
    def set_managers(self, render_manager, state_manager, bubble_manager, screenshot_manager):
        """
        设置其他管理器的引用
        
        Args:
            render_manager: 渲染管理器
            state_manager: 状态管理器
            bubble_manager: 气泡管理器
            screenshot_manager: 截图管理器
        """
        self.render_manager = render_manager
        self.state_manager = state_manager
        self.bubble_manager = bubble_manager
        self.screenshot_manager = screenshot_manager
    
    def handle_mouse_press(self, event):
        """
        处理鼠标按下事件
        
        Args:
            event: 鼠标事件
        """
        if event.button() == 1:  # 左键
            self.drag_start_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            
            # 如果窗口未被锁定，创建移动线程
            if self.state_manager and not self.state_manager.is_locked():
                self.start_move_worker()
        
        event.accept()
    
    def handle_mouse_release(self, event):
        """
        处理鼠标释放事件
        
        Args:
            event: 鼠标事件
        """
        if event.button() == 1 and self.move_worker:  # 左键
            self.stop_move_worker()
            self.drag_start_position = None
        
        event.accept()
    
    def handle_mouse_move(self, event):
        """
        处理鼠标移动事件
        
        Args:
            event: 鼠标事件
        """
        if self.drag_start_position:
            # 委托给渲染器处理（用于 Live2D 注视效果）
            rel_x = event.x() / self.parent.width()
            rel_y = event.y() / self.parent.height()
            
            if self.render_manager:
                self.render_manager.handle_mouse_move(rel_x, rel_y)
    
    def handle_mouse_double_click(self, event):
        """
        处理鼠标双击事件
        
        Args:
            event: 鼠标事件
        """
        if event.button() == 1:  # 左键
            # 触发交互事件（摸摸头）
            logger.info("检测到双击事件，触发摸摸头动作")
            
            # 设置动画状态（如果支持）
            if self.render_manager:
                self.render_manager.set_animation_state("happy")
            
            # 发送消息
            import asyncio
            from src.core.chat import chat_util
            asyncio.run(chat_util.easy_to_send("(这是一个类似于摸摸头的友善动作)", "text"))
        
        event.accept()
    
    def show_context_menu(self, event):
        """
        显示右键菜单
        
        Args:
            event: 鼠标事件
        """
        # 暂停移动线程
        if self.move_worker:
            self.stop_move_worker()
        
        # 创建并显示菜单
        menu = self.create_context_menu(event.globalPos())
        menu.exec_(event.globalPos())
        menu.deleteLater()
    
    def create_context_menu(self, pos) -> QMenu:
        """
        创建右键菜单
        
        Args:
            pos: 菜单显示位置
            
        Returns:
            QMenu: 创建的菜单
        """
        from src.frontend.bubble_menu import BubbleMenu
        
        menu = BubbleMenu(self.parent)
        
        # 主菜单项
        actions = [
            ("🐾 隐藏", self.parent.hide),
            ("✏️ 聊聊天", self.show_chat_input),
            ("📸 截图", self.start_screenshot),
        ]
        
        # 添加窥屏选项（如果有）
        if hasattr(self.parent, 'is_peeking'):
            if not self.parent.is_peeking:
                actions.append(("👀 麦麦窥屏", self.start_peeking))
            else:
                actions.append(("⏹️ 停止窥屏", self.stop_peeking))
        
        for text, callback in actions:
            action = menu.addAction(text)
            action.triggered.connect(callback)
        
        # 添加缩放子菜单
        scale_menu = menu.addMenu("🔍 缩放")
        
        from src.util.image_util import get_scale_factor
        scale_actions = [
            ("0.5x (50%)", 0.5),
            ("0.75x (75%)", 0.75),
            ("1.0x (100%)", 1.0),
            ("1.25x (125%)", 1.25),
            ("1.5x (150%)", 1.5),
            ("2.0x (200%)", 2.0),
        ]
        
        for text, scale in scale_actions:
            action = scale_menu.addAction(text)
            # 标记当前缩放
            if abs(scale - get_scale_factor()) < 0.01:
                action.setText(f"✓ {text}")
            action.triggered.connect(lambda checked, s=scale: self.change_scale(s))
        
        menu.addSeparator()
        
        # 添加渲染模式切换选项（如果支持）
        if self.render_manager and self.render_manager.allow_switch:
            mode_menu = menu.addMenu("🎨 渲染模式")
            
            static_action = mode_menu.addAction("静态图片")
            if self.render_manager.current_mode == "static":
                static_action.setText("✓ 静态图片")
            static_action.triggered.connect(lambda: self.switch_render_mode("static"))
            
            live2d_action = mode_menu.addAction("Live2D")
            if self.render_manager.current_mode == "live2d":
                live2d_action.setText("✓ Live2D")
            live2d_action.triggered.connect(lambda: self.switch_render_mode("live2d"))
        
        # 退出选项
        exit_action = menu.addAction("❌ 退出")
        exit_action.triggered.connect(self.parent.safe_quit)
        
        return menu
    
    def show_chat_input(self):
        """显示聊天输入框"""
        if self.bubble_manager:
            self.bubble_manager.show_input()
    
    def start_screenshot(self):
        """启动截图"""
        if self.screenshot_manager:
            self.screenshot_manager.start_screenshot()
    
    def start_peeking(self):
        """开始窥屏"""
        if hasattr(self.parent, 'start_peeking'):
            self.parent.start_peeking()
    
    def stop_peeking(self):
        """停止窥屏"""
        if hasattr(self.parent, 'stop_peeking'):
            self.parent.stop_peeking()
    
    def change_scale(self, new_scale: float):
        """改变界面缩放倍率"""
        try:
            import tomli
            import tomli_w
            
            # 更新配置文件
            with open("config.toml", "rb") as f:
                config_data = tomli.load(f)
            
            # 更新缩放倍率
            if 'interface' not in config_data:
                config_data['interface'] = {}
            config_data['interface']['scale_factor'] = new_scale
            
            # 写回配置文件
            with open("config.toml", "w", encoding='utf-8') as f:
                f.write(tomli_w.dumps(config_data))
            
            # 显示提示
            if self.bubble_manager:
                self.bubble_manager.show_message(
                    f"缩放已调整为 {new_scale}x，重启程序后生效",
                    msg_type="received"
                )
            
        except Exception as e:
            logger.error(f"修改缩放倍率失败: {e}")
            if self.bubble_manager:
                self.bubble_manager.show_message(
                    f"修改缩放失败: {e}",
                    msg_type="received"
                )
    
    def switch_render_mode(self, mode: str):
        """切换渲染模式"""
        if self.render_manager:
            try:
                self.render_manager.switch_mode(mode)
                mode_name = "静态图片" if mode == "static" else "Live2D"
                if self.bubble_manager:
                    self.bubble_manager.show_message(
                        f"已切换到 {mode_name} 模式",
                        msg_type="received"
                    )
            except Exception as e:
                logger.error(f"切换渲染模式失败: {e}")
                if self.bubble_manager:
                    self.bubble_manager.show_message(
                        f"切换模式失败: {e}",
                        msg_type="received"
                    )
    
    def start_move_worker(self):
        """启动移动工作线程"""
        self.move_worker = MoveWorker(self.drag_start_position, self.parent)
        signals_bus.position_changed.connect(self._on_position_changed)
        self.move_worker.start()
        logger.debug("移动线程已启动")
    
    def stop_move_worker(self):
        """停止移动工作线程"""
        if self.move_worker:
            self.move_worker.stop()
            self.move_worker.wait()
            self.move_worker = None
            logger.debug("移动线程已停止")
    
    def _on_position_changed(self, pos):
        """
        窗口移动时更新位置
        
        Args:
            pos: 新位置
        """
        self.parent.move(pos)
        
        # 更新气泡位置
        if self.bubble_manager:
            self.bubble_manager.on_position_changed()
    
    def cleanup(self):
        """清理资源"""
        self.stop_move_worker()
        self.drag_start_position = None
        logger.info("事件管理器已清理")
