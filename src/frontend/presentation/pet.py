"""
重构后的桌面宠物主窗口
展示如何使用新的架构
"""

import asyncio
import random
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QShortcut
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon, QKeySequence

from src.core.chat import chat_util
from src.frontend.signals import signals_bus
from src.frontend.bubble_speech import SpeechBubbleList
from src.frontend.bubble_input import BubbleInput
from src.frontend.ScreenshotSelector import ScreenshotSelector

from src.util.logger import logger
from src.util.image_util import get_scale_factor, pixmap_to_base64

from config import load_config, get_scale_factor

config = load_config()
scale_factor = get_scale_factor(config)

import sys
from typing import Literal

app = QApplication(sys.argv)


class DesktopPet(QWidget):
    """
    重构后的桌面宠物主窗口
    
    职责：
    - 窗口生命周期管理
    - 子窗口容器管理
    - 布局管理
    - 事件委托
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化窗口
        self.init_window()
        
        # 初始化管理器
        self.init_managers()
        
        # 初始化子系统
        self.init_subsystems()
        
        # 初始化 UI
        self.init_ui()
        
        # 初始化托盘图标
        self.init_tray_icon()
        
        # 初始化快捷键
        self.init_shortcuts()
        
        # 连接信号
        signals_bus.message_received.connect(self.show_message)
        
        # 窥屏功能
        self.is_peeking = False
        self.peek_timer = QTimer(self)
        self.peek_timer.timeout.connect(self._on_peek_timer)
        
        logger.info("重构后的桌面宠物初始化完成")
    
    def init_window(self):
        """初始化窗口属性"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 应用缩放倍率
        base_width = 400
        base_height = 600
        scaled_width = int(base_width * scale_factor)
        scaled_height = int(base_height * scale_factor)
        self.setFixedSize(scaled_width, scaled_height)
        
        # 设置初始位置
        screen_geo = QApplication.primaryScreen().availableGeometry()
        x = screen_geo.width() - self.width() - int(20 * scale_factor)
        y = screen_geo.height() - self.height() - int(80 * scale_factor)
        self.move(x, y)
    
    def init_managers(self):
        """初始化核心管理器"""
        from src.frontend.core.managers import RenderManager, EventManager, StateManager
        
        # 渲染管理器
        self.render_manager = RenderManager(self)
        
        # 状态管理器
        self.state_manager = StateManager(self)
        
        # 事件管理器
        self.event_manager = EventManager(self)
        
        # 气泡管理器
        self.bubble_manager = BubbleManager(self)
        
        # 截图管理器
        self.screenshot_manager = ScreenshotManager(self)
        
        # 设置管理器之间的引用
        self.event_manager.set_managers(
            render_manager=self.render_manager,
            state_manager=self.state_manager,
            bubble_manager=self.bubble_manager,
            screenshot_manager=self.screenshot_manager
        )
        
        logger.info("核心管理器初始化完成")
    
    def init_subsystems(self):
        """初始化子系统"""
        # 气泡系统
        self.chat_bubbles = SpeechBubbleList(parent=self)
        self.bubble_input = BubbleInput(parent=self, on_send=self.handle_user_input)
        self.bubble_input.hide()
        
        # 截图选择器
        self.screenshot_selector = None
        
        # 将气泡组件设置到管理器
        self.bubble_manager.set_widgets(self.chat_bubbles, self.bubble_input)
        
        logger.info("子系统初始化完成")
    
    def init_ui(self):
        """初始化 UI"""
        # 渲染容器
        self.render_container = QWidget(self)
        self.render_container.setGeometry(0, 0, self.width(), self.height())
        
        # 将渲染管理器的控件添加到容器
        self.render_manager.attach_to(self.render_container)
        
        logger.info("UI 初始化完成")
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("./img/maim.png"))
        self.tray_icon.setToolTip("桌面宠物")
        
        # 创建菜单
        tray_menu = self.create_tray_menu()
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # 如果配置中要求隐藏终端
        if config.hide_console:
            self.state_manager.hide_console()
            self.show_message("终端藏在托盘栏咯，进入托盘栏打开叭")
        
        logger.info("托盘图标初始化完成")
    
    def init_shortcuts(self):
        """初始化快捷键"""
        if config.Screenshot_shortcuts is not None:
            shortcut = QShortcut(QKeySequence(config.Screenshot_shortcuts), self)
            shortcut.activated.connect(self.screenshot_manager.start_screenshot)
    
    def create_tray_menu(self) -> QMenu:
        """创建托盘菜单"""
        menu = QMenu()
        
        # 宠物控制
        show_action = menu.addAction("显示宠物")
        show_action.triggered.connect(self.state_manager.show_window)
        
        # 终端控制
        self.toggle_term_action = menu.addAction("隐藏终端")
        self.toggle_term_action.triggered.connect(self.state_manager.toggle_console)
        
        # 锁定控制
        self.lock_action = menu.addAction("锁定桌宠")
        self.lock_action.triggered.connect(self.state_manager.toggle_lock)
        
        menu.addSeparator()
        
        # 退出
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.safe_quit)
        
        return menu
    
    # 事件委托
    def mousePressEvent(self, event):
        """鼠标按下 - 委托给事件管理器"""
        self.event_manager.handle_mouse_press(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放 - 委托给事件管理器"""
        self.event_manager.handle_mouse_release(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动 - 委托给事件管理器"""
        self.event_manager.handle_mouse_move(event)
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击 - 委托给事件管理器"""
        self.event_manager.handle_mouse_double_click(event)
    
    def contextMenuEvent(self, event):
        """右键菜单 - 委托给事件管理器"""
        self.event_manager.show_context_menu(event)
    
    # 公开方法
    def show_message(self, text=None, msg_type: Literal["received", "sent"] = "received", pixmap=None):
        """显示消息"""
        self.bubble_manager.show_message(text, msg_type, pixmap)
    
    def handle_user_input(self, text):
        """处理用户输入"""
        logger.info(f"收到用户输入: {text}")
        self.show_message(text=text, msg_type="sent")
        asyncio.run(chat_util.easy_to_send(str(text), "text"))
    
    def safe_quit(self):
        """安全退出"""
        import asyncio
        
        # 恢复终端显示
        if not self.state_manager.is_console_visible():
            self.state_manager.show_console()
        
        # 清理前端资源
        logger.info("清理前端资源...")
        self.event_manager.cleanup()
        self.render_manager.cleanup()
        self.state_manager.cleanup()
        
        # 清理所有资源（包括 router、数据库等）
        try:
            # 在新的事件循环中执行异步清理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._cleanup_all_resources())
            loop.close()
        except Exception as e:
            logger.error(f"清理资源时出错: {e}", exc_info=True)
        
        # 退出应用
        logger.info("应用程序退出")
        QApplication.quit()
    
    async def _cleanup_all_resources(self):
        """清理所有异步资源"""
        try:
            # 导入并执行清理函数
            from main import cleanup_all
            await cleanup_all()
            
            # 清理数据库
            from src.database import db_manager
            if db_manager.is_initialized():
                await db_manager.close()
                logger.info("数据库连接已关闭")
                
        except Exception as e:
            logger.error(f"清理异步资源失败: {e}", exc_info=True)
    
    # 窥屏功能
    def start_peeking(self):
        """开始窥屏"""
        if not self.is_peeking:
            self.is_peeking = True
            random_time = random.randint(10, 30)
            self.peek_timer.start(random_time * 1000)
            self.show_message("开始窥屏啦~", msg_type="received")
        else:
            self.stop_peeking()
    
    def stop_peeking(self):
        """停止窥屏"""
        if self.is_peeking:
            self.is_peeking = False
            self.peek_timer.stop()
            self.show_message("停止窥屏啦~", msg_type="received")
    
    def _on_peek_timer(self):
        """窥屏定时器触发"""
        if self.is_peeking:
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0)
            self.screenshot_manager.handle_screenshot(pixmap)


class BubbleManager:
    """气泡管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.chat_bubbles = None
        self.bubble_input = None
    
    def set_widgets(self, chat_bubbles, bubble_input):
        """设置气泡组件"""
        self.chat_bubbles = chat_bubbles
        self.bubble_input = bubble_input
    
    def show_message(self, text=None, msg_type: Literal["received", "sent"] = "received", pixmap=None):
        """显示消息"""
        if self.chat_bubbles:
            self.chat_bubbles.add_message(text, msg_type, pixmap)
            QTimer.singleShot(25000, self.del_first_msg)
    
    def del_first_msg(self):
        """删除第一条消息"""
        if self.chat_bubbles:
            self.chat_bubbles.del_first_msg()
    
    def show_input(self):
        """显示输入框"""
        if self.bubble_input:
            self.bubble_input.show()
            self.bubble_input.update_position()
            self.bubble_input.input_field.setFocus()
    
    def hide_all(self):
        """隐藏所有气泡"""
        if self.bubble_input:
            self.bubble_input.hide()
        if self.chat_bubbles:
            self.chat_bubbles.hide()
    
    def on_position_changed(self):
        """窗口移动时更新气泡位置"""
        if self.bubble_input and self.bubble_input.isVisible():
            self.bubble_input.update_position()
        if self.chat_bubbles:
            for bubble in self.chat_bubbles._active_bubbles:
                if bubble.isVisible():
                    self.chat_bubbles.update_position()


class ScreenshotManager:
    """截图管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.screenshot_selector = None
    
    def start_screenshot(self):
        """启动截图"""
        self.parent.hide()
        for chat_bubble in self.parent.chat_bubbles._active_bubbles:
            chat_bubble.hide()
        
        self.screenshot_selector = PetScreenshotSelector(self.parent)
        self.screenshot_selector.show()
    
    def handle_screenshot(self, pixmap):
        """处理截图结果"""
        self.parent.show()
        for chat_bubble in self.parent.chat_bubbles._active_bubbles:
            chat_bubble.show()
        
        self.parent.show_message(pixmap=pixmap, msg_type="sent")
        base64_str = pixmap_to_base64(pixmap)
        asyncio.run(chat_util.easy_to_send(base64_str, "image"))


class PetScreenshotSelector(ScreenshotSelector):
    """宠物截图选择器"""
    
    def __init__(self, pet):
        super().__init__()
        self.pet = pet
    
    def on_screenshot_captured(self, pixmap):
        self.pet.screenshot_manager.handle_screenshot(pixmap)


# 创建实例
desktop_pet = DesktopPet()
