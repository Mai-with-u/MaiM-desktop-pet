"""
重构后的桌面宠物主窗口
展示如何使用新的架构
"""

import asyncio
import atexit
import random
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QShortcut, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon, QKeySequence, QCursor

from src.core.chat import chat_manager
from src.core.thread_manager import thread_manager
from src.frontend.signals import signals_bus
from src.frontend.bubble_speech import SpeechBubbleList
from src.frontend.bubble_input import BubbleInput
from src.frontend.ScreenshotSelector import ScreenshotSelector

from src.util.logger import logger
from src.util.image_util import get_scale_factor as util_get_scale_factor, pixmap_to_base64

import sys
from typing import Literal, Optional

# 默认缩放倍率（用于配置加载失败时的降级）
_DEFAULT_SCALE_FACTOR = 1.0

# 延迟加载配置，避免模块导入时崩溃
_config = None
_scale_factor = _DEFAULT_SCALE_FACTOR


def _get_config():
    """延迟加载配置"""
    global _config, _scale_factor
    if _config is None:
        try:
            from config import load_config, get_scale_factor
            _config = load_config()
            _scale_factor = get_scale_factor(_config) if _config else _DEFAULT_SCALE_FACTOR
        except Exception as e:
            logger.warning(f"配置加载失败，使用默认值: {e}")
            _scale_factor = _DEFAULT_SCALE_FACTOR
    return _config


def _get_scale_factor() -> float:
    """获取缩放倍率"""
    _get_config()  # 确保配置已加载
    return _scale_factor


# 为了兼容现有代码，导出 config 和 scale_factor
config = None  # 延迟初始化
scale_factor = _DEFAULT_SCALE_FACTOR


def get_qapp():
    """获取 QApplication 实例"""
    from PyQt5.QtWidgets import QApplication
    return QApplication.instance()


app = get_qapp()

# 全局桌面宠物实例引用（延迟初始化）
_desktop_pet_instance: Optional['DesktopPet'] = None


def safe_quit_global():
    """全局安全退出函数 - 确保无论如何退出都能清理所有资源"""
    global _desktop_pet_instance
    logger.info("全局清理资源...")
    if _desktop_pet_instance:
        try:
            logger.info("全局清理：守护线程将自动退出")
        except Exception as e:
            logger.error(f"全局清理时出错: {e}", exc_info=True)


atexit.register(safe_quit_global)


def _safe_get_primary_screen():
    """安全获取主屏幕，返回 None 如果失败"""
    try:
        screen = QApplication.primaryScreen()
        if screen is None:
            logger.warning("无法获取主屏幕")
        return screen
    except Exception as e:
        logger.error(f"获取主屏幕失败: {e}")
        return None


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

        # 加载配置（使用延迟加载的配置）
        global config, scale_factor
        config = _get_config()
        scale_factor = _get_scale_factor()
        self._last_live2d_canvas_size = None

        # 初始化窗口
        self.init_window()

        # 初始化管理器
        self.init_managers()

        # 注册清理函数到线程管理器
        self._register_cleanup_functions()

        # 初始化子系统
        self.init_subsystems()
        self.chat_window_active = False

        # 初始化 UI
        self.init_ui()

        # 初始化托盘图标
        self.init_tray_icon()

        # 初始化快捷键
        self.init_shortcuts()

        # 连接信号（保存连接以便后续断开）
        self._signal_connections = []
        self._connect_signal(signals_bus.message_received, self.show_message)

        # 窥屏功能
        self.is_peeking = False
        self.peek_timer = QTimer(self)
        self.peek_timer.timeout.connect(self._on_peek_timer)

        # 保存全局引用以便在强制退出时也能清理
        global _desktop_pet_instance
        _desktop_pet_instance = self

        logger.info("重构后的桌面宠物初始化完成")

    def _connect_signal(self, signal, slot):
        """安全连接信号，并记录连接以便后续断开"""
        try:
            signal.connect(slot)
            self._signal_connections.append((signal, slot))
        except Exception as e:
            logger.error(f"连接信号失败: {e}")

    def _disconnect_signals(self):
        """断开所有已连接的信号"""
        for signal, slot in self._signal_connections:
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                # 信号可能已经断开或对象已销毁
                pass
        self._signal_connections.clear()

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

        # 设置初始位置（安全获取屏幕）
        screen = _safe_get_primary_screen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = screen_geo.width() - self.width() - int(20 * scale_factor)
            y = screen_geo.height() - self.height() - int(80 * scale_factor)
            self.move(x, y)
        else:
            # 无法获取屏幕时使用默认位置
            self.move(100, 100)
    
    def init_managers(self):
        """初始化核心管理器"""
        from src.frontend.core.managers import (
            RenderManager,
            EventManager,
            StateManager,
            HotkeyManager
        )
        
        # 渲染管理器
        self.render_manager = RenderManager(self)
        
        # 状态管理器
        self.state_manager = StateManager(self)
        
        # 事件管理器
        self.event_manager = EventManager(self)
        
        # 热键管理器
        self.hotkey_manager = HotkeyManager()
        
        # 气泡管理器
        self.bubble_manager = BubbleManager(self)
        
        # 截图管理器
        self.screenshot_manager = ScreenshotManager(self)
        
        # 设置管理器之间的引用
        self.event_manager.set_managers(
            render_manager=self.render_manager,
            state_manager=self.state_manager,
            bubble_manager=self.bubble_manager,
            screenshot_manager=self.screenshot_manager,
            hotkey_manager=self.hotkey_manager
        )
        
        # 注册热键管理器的清理函数
        from src.core.thread_manager import thread_manager
        thread_manager.register_cleanup(self.hotkey_manager.cleanup)
        
        logger.info("核心管理器初始化完成")
    
    def init_subsystems(self):
        """初始化子系统"""
        # 气泡系统（传入气泡点击回调）
        self.chat_bubbles = SpeechBubbleList(
            parent=self,
            on_bubble_click=self._on_bubble_click
        )
        self.bubble_input = BubbleInput(parent=self, on_send=self.handle_user_input)
        self.bubble_input.hide()

        # 截图选择器
        self.screenshot_selector = None

        # 将气泡组件设置到管理器
        self.bubble_manager.set_widgets(self.chat_bubbles, self.bubble_input)

        logger.info("子系统初始化完成")

    def _on_bubble_click(self, event=None):
        """气泡点击回调，打开聊天窗口"""
        from src.frontend.chat_window import ChatWindow
        ChatWindow.show_chat_window(parent=None, pet_window=self)
    
    def init_ui(self):
        """初始化 UI"""
        # 渲染容器
        self.render_container = QWidget(self)
        self.render_container.setGeometry(0, 0, self.width(), self.height())
        
        # 将渲染管理器的控件添加到容器
        self.render_manager.attach_to(self.render_container)
        
        logger.info("UI 初始化完成")

    def adjust_to_live2d_canvas_size(self, canvas_width: float, canvas_height: float):
        """根据 Live2D 模型画布比例调整桌宠窗口大小。"""
        try:
            canvas_width = float(canvas_width)
            canvas_height = float(canvas_height)
        except (TypeError, ValueError):
            return

        if canvas_width <= 0 or canvas_height <= 0:
            return

        canvas_size = (round(canvas_width, 2), round(canvas_height, 2))
        if self._last_live2d_canvas_size == canvas_size:
            return
        self._last_live2d_canvas_size = canvas_size

        max_width = int(400 * scale_factor)
        max_height = int(600 * scale_factor)
        min_width = int(180 * scale_factor)
        min_height = int(180 * scale_factor)

        fit_scale = min(max_width / canvas_width, max_height / canvas_height)
        target_width = max(min_width, int(round(canvas_width * fit_scale)))
        target_height = max(min_height, int(round(canvas_height * fit_scale)))

        if abs(target_width - self.width()) <= 2 and abs(target_height - self.height()) <= 2:
            return

        old_bottom_right = self.geometry().bottomRight()
        self.setFixedSize(target_width, target_height)

        if hasattr(self, "render_container") and self.render_container:
            self.render_container.setGeometry(0, 0, target_width, target_height)

        self.move(
            old_bottom_right.x() - target_width + 1,
            old_bottom_right.y() - target_height + 1
        )

        if hasattr(self, "chat_bubbles") and self.chat_bubbles:
            self.chat_bubbles.update_position()

        logger.info(
            f"根据 Live2D 画布调整桌宠窗口: "
            f"canvas={canvas_width}x{canvas_height}, window={target_width}x{target_height}"
        )
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)

        # 使用绝对路径加载图标
        try:
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent.resolve()
            icon_path = project_root / "img" / "maim.png"
            if icon_path.exists():
                self.tray_icon.setIcon(QIcon(str(icon_path)))
            else:
                # 降级使用相对路径
                self.tray_icon.setIcon(QIcon("./img/maim.png"))
        except Exception as e:
            logger.warning(f"加载托盘图标失败: {e}")
            self.tray_icon.setIcon(QIcon("./img/maim.png"))

        self.tray_icon.setToolTip("桌面宠物")

        # 创建菜单
        tray_menu = self.create_tray_menu()
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 如果配置中要求隐藏终端
        if config and config.hide_console:
            self.state_manager.hide_console()
            self.show_notice("终端藏在托盘栏咯，进入托盘栏打开叭")

        logger.info("托盘图标初始化完成")
    
    def init_shortcuts(self):
        """初始化全局快捷键"""
        logger.info("开始初始化全局快捷键...")

        # 注册截图热键
        screenshot_shortcuts = getattr(config, 'Screenshot_shortcuts', None) if config else None
        if screenshot_shortcuts is not None:
            success = self.hotkey_manager.register_hotkey(
                name="screenshot",
                shortcut_str=screenshot_shortcuts,
                callback=self._on_screenshot_hotkey
            )

            if success:
                logger.info(f"✓ 已注册全局截图快捷键: {screenshot_shortcuts}")
            else:
                # 降级使用 QShortcut
                logger.warning("全局热键注册失败，降级使用 QShortcut")
                self._init_fallback_shortcut()
        else:
            logger.info("截图快捷键未配置（值为 None）")

        # 启动热键监听器
        self.hotkey_manager.start()

    def _init_fallback_shortcut(self):
        """降级使用 QShortcut（仅窗口有焦点时有效）"""
        screenshot_shortcuts = getattr(config, 'Screenshot_shortcuts', None) if config else None
        if screenshot_shortcuts is not None:
            logger.info(f"使用 QShortcut 注册截图快捷键: {screenshot_shortcuts}")
            shortcut = QShortcut(QKeySequence(screenshot_shortcuts), self)
            shortcut.activated.connect(self.screenshot_manager.start_screenshot)
            logger.info("✓ 截图快捷键注册成功（仅窗口有焦点时有效）")
    
    def _on_screenshot_hotkey(self):
        """全局截图快捷键触发"""
        logger.info("全局截图快捷键被触发")
        
        # 使用 QTimer.singleShot 确保在主线程中执行 UI 操作
        # pynput 的热键回调在单独的线程中，必须在主线程中执行 Qt UI 操作
        QTimer.singleShot(0, self._do_start_screenshot)
    
    def _do_start_screenshot(self):
        """实际执行截图的方法（确保在主线程中）"""
        # 检查截图状态，避免重复触发
        if self.screenshot_manager.is_screenshotting:
            logger.warning("截图正在进行中，忽略新的截图请求")
            return
        
        # 激活窗口并置于前台（必须在主线程中）
        self.activateWindow()
        self.raise_()
        self.showNormal()
        
        # 确保窗口获得焦点
        self.setFocus()
        
        # 执行截图
        self.screenshot_manager.start_screenshot()
    
    def _register_cleanup_functions(self):
        """将各管理器的清理函数注册到线程管理器"""
        # 注册前端管理器的清理函数
        thread_manager.register_cleanup(self.render_manager.cleanup)
        thread_manager.register_cleanup(self.event_manager.cleanup)
        thread_manager.register_cleanup(self.state_manager.cleanup)
        
        # 注册桌面宠物自己的清理函数
        thread_manager.register_cleanup(self._cleanup_pet_resources)
        
        logger.info("清理函数已注册到线程管理器")
    
    def _cleanup_pet_resources(self):
        """清理桌面宠物特有的资源"""
        # 注意：热键管理器的清理已经通过线程管理器注册
        # 不需要在这里手动清理
        
        # 恢复终端显示
        if not self.state_manager.is_console_visible():
            self.state_manager.show_console()
        
        # 隐藏托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        
        # 隐藏所有窗口
        self.hide()
        if hasattr(self, 'chat_bubbles') and self.chat_bubbles:
            for bubble in self.chat_bubbles._active_bubbles:
                if bubble:
                    bubble.hide()
        if hasattr(self, 'bubble_input') and self.bubble_input:
            self.bubble_input.hide()

        # 隐藏聊天窗口（不关闭，保持单例）
        from src.frontend.chat_window import ChatWindow
        if ChatWindow._instance and ChatWindow._instance.isVisible():
            ChatWindow._instance.hide()

        logger.info("桌面宠物资源已清理")
    
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
        if self.is_chat_window_active():
            logger.debug("聊天窗口已打开，跳过桌宠气泡显示")
            return
        self.bubble_manager.show_message(text, msg_type, pixmap)

    def show_notice(self, text: str, on_click=None):
        """显示非聊天系统提示。"""
        if not text:
            return
        if self.is_chat_window_active():
            try:
                from src.frontend.chat_window import ChatWindow
                chat_window = ChatWindow.get_instance(parent=None, pet_window=self)
                chat_window.add_notice(str(text), on_click=on_click)
                return
            except Exception as e:
                logger.error(f"将系统提示同步到聊天窗口失败: {e}", exc_info=True)

        self.bubble_manager.show_notice(str(text), on_click=on_click)

    def show_click_feedback(self, text: str, event=None):
        """在点击位置附近显示一个短暂的轻提示。"""
        if not text:
            return
        try:
            global_pos = event.globalPos() if event is not None and hasattr(event, "globalPos") else QCursor.pos()
            popup = QLabel(text)
            popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            popup.setAttribute(Qt.WA_TranslucentBackground, True)
            popup.setStyleSheet(f"""
                QLabel {{
                    color: #666666;
                    background-color: rgba(245, 245, 245, 235);
                    border: 1px solid #dddddd;
                    border-radius: {int(8 * scale_factor)}px;
                    padding: {int(5 * scale_factor)}px {int(10 * scale_factor)}px;
                }}
            """)
            popup.adjustSize()
            popup.move(global_pos + QPoint(int(10 * scale_factor), -popup.height() - int(10 * scale_factor)))

            popups = getattr(self, "_click_feedback_popups", None)
            if popups is None:
                self._click_feedback_popups = []
                popups = self._click_feedback_popups
            popups.append(popup)

            def cleanup():
                try:
                    popup.hide()
                    popup.deleteLater()
                finally:
                    if popup in popups:
                        popups.remove(popup)

            popup.show()
            QTimer.singleShot(1200, cleanup)
        except Exception as e:
            logger.error(f"显示点击反馈失败: {e}", exc_info=True)
    
    def safe_quit(self):
        """安全退出 - 使用 Qt 的方式退出"""
        
        # 使用 QTimer.singleShot 延迟执行退出，确保在 Qt 事件循环中正确处理
        # 这样可以避免在事件处理函数中直接调用 exit 导致的问题
        QTimer.singleShot(100, self._do_safe_quit)
    
    def _do_safe_quit(self):
        """实际执行退出的方法"""
        # 清理所有资源（包括前端和协议管理器的清理）
        self.cleanup_resources()
        
        # 退出应用程序
        logger.info("退出应用程序")
        # 使用 os._exit 强制终止进程，避免等待非守护线程
        import os
        os._exit(0)
    
    def handle_user_input(self, text):
        """处理用户输入（同步接口）"""
        logger.info(f"收到用户输入: {text}")
        if self.is_chat_window_active():
            try:
                from src.frontend.chat_window import ChatWindow
                chat_window = ChatWindow.get_instance(parent=None, pet_window=self)
                chat_window.add_message(text=str(text), msg_type="sent")
                chat_window.activateWindow()
            except Exception as e:
                logger.error(f"将桌宠输入同步到聊天窗口失败: {e}", exc_info=True)
        else:
            self.show_message(text=text, msg_type="sent")

        # 使用 qasync 事件循环，创建异步任务而不阻塞主线程
        asyncio.create_task(chat_manager.send_message(str(text)))

    def set_chat_window_active(self, active: bool):
        """切换聊天窗口独占对话展示模式。"""
        if getattr(self, "chat_window_active", False) == active:
            return

        self.chat_window_active = active
        if active:
            if hasattr(self, 'bubble_input') and self.bubble_input:
                self.bubble_input.hide()
            if hasattr(self, 'chat_bubbles') and self.chat_bubbles:
                self.chat_bubbles.clear_all()
            logger.info("已切换到聊天窗口交互模式，桌宠气泡暂停显示")
        else:
            logger.info("已退出聊天窗口交互模式，桌宠气泡恢复显示")

    def is_chat_window_active(self) -> bool:
        """聊天窗口是否正在接管聊天展示。"""
        return bool(getattr(self, "chat_window_active", False))
    
    def cleanup_resources(self):
        """清理所有资源（不包含退出逻辑）"""
        # 防止重复清理
        if hasattr(self, '_is_cleaning_up') and self._is_cleaning_up:
            logger.info("已经在清理中，跳过重复调用")
            return

        self._is_cleaning_up = True
        logger.info("开始清理资源...")

        try:
            # 先断开信号连接
            self._disconnect_signals()

            # 停止定时器
            if hasattr(self, 'peek_timer') and self.peek_timer:
                self.peek_timer.stop()

            # 执行线程管理器中注册的所有清理函数
            from src.core.thread_manager import thread_manager

            # 使用公共接口访问清理函数列表，而不是直接访问私有属性
            cleanup_functions = getattr(thread_manager, '_cleanup_functions', [])
            logger.info(f"共有 {len(cleanup_functions)} 个清理函数")

            # 分离同步和异步清理函数
            sync_cleanup_funcs = [
                f for f in cleanup_functions
                if not asyncio.iscoroutinefunction(f)
            ]
            async_cleanup_funcs = [
                f for f in cleanup_functions
                if asyncio.iscoroutinefunction(f)
            ]

            # 执行同步清理函数
            for cleanup_func in sync_cleanup_funcs:
                try:
                    func_name = getattr(cleanup_func, '__name__', 'unknown')
                    logger.info(f"[同步] 执行清理函数: {func_name}")
                    cleanup_func()
                    logger.info(f"[同步] {func_name} 执行完成")
                except Exception as e:
                    func_name = getattr(cleanup_func, '__name__', 'unknown')
                    logger.error(f"执行同步清理函数时出错: {func_name}, 错误: {e}", exc_info=True)

            # 执行异步清理函数（创建新的事件循环）
            if async_cleanup_funcs:
                try:
                    logger.info(f"开始执行 {len(async_cleanup_funcs)} 个异步清理函数...")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        for cleanup_func in async_cleanup_funcs:
                            try:
                                func_name = getattr(cleanup_func, '__name__', 'unknown')
                                logger.info(f"[异步] 执行清理函数: {func_name}")
                                loop.run_until_complete(cleanup_func())
                                logger.info(f"[异步] {func_name} 执行完成")
                            except Exception as e:
                                func_name = getattr(cleanup_func, '__name__', 'unknown')
                                logger.error(f"执行异步清理函数时出错: {func_name}, 错误: {e}", exc_info=True)
                    finally:
                        # 取消所有未完成的任务
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            logger.info(f"取消 {len(pending)} 个未完成的异步任务...")
                            for task in pending:
                                task.cancel()
                            loop.run_until_complete(
                                asyncio.gather(*pending, return_exceptions=True)
                            )
                        loop.close()
                        logger.info("事件循环已关闭")
                except Exception as e:
                    logger.error(f"执行异步清理函数时出错: {e}", exc_info=True)
            
            logger.info("所有资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源过程中出错: {e}", exc_info=True)
    
    # 窥屏功能
    def start_peeking(self):
        """开始窥屏"""
        if not self.is_peeking:
            self.is_peeking = True
            random_time = random.randint(10, 30)
            self.peek_timer.start(random_time * 1000)
            self.show_notice("开始窥屏")
        else:
            self.stop_peeking()
    
    def stop_peeking(self):
        """停止窥屏"""
        if self.is_peeking:
            self.is_peeking = False
            self.peek_timer.stop()
            self.show_notice("停止窥屏")
    
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

    def show_notice(self, text: str, on_click=None):
        """显示非聊天系统提示。"""
        if self.chat_bubbles:
            self.chat_bubbles.add_notice(text, on_click=on_click)
            QTimer.singleShot(8000, self.del_first_msg)
    
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
        self.is_screenshotting = False  # 防止重复启动截图
    
    def start_screenshot(self):
        """启动截图"""
        # 如果已经在截图中，忽略新的截图请求
        if self.is_screenshotting:
            logger.warning("截图正在进行中，忽略新的截图请求")
            return
        
        self.is_screenshotting = True
        logger.info("启动截图...")
        
        self.parent.hide()
        for chat_bubble in self.parent.chat_bubbles._active_bubbles:
            chat_bubble.hide()
        
        self.screenshot_selector = PetScreenshotSelector(self.parent)
        self.screenshot_selector.show()
    
    def handle_screenshot(self, pixmap, text=""):
        """处理截图结果
        
        参数:
            pixmap: 截图 QPixmap
            text: 用户输入的文本说明（可选）
        """
        # 重置截图状态
        self.is_screenshotting = False
        logger.info("截图处理完成")
        
        self.parent.show()
        for chat_bubble in self.parent.chat_bubbles._active_bubbles:
            chat_bubble.show()
        
        # 显示截图气泡
        self.parent.show_message(pixmap=pixmap, msg_type="sent")
        
        # 发送消息
        if text:
            # 有文本，发送文本+图片的 seglist
            logger.info(f"发送文本+图片复合消息，文本: {text}")
            asyncio.create_task(chat_manager.send_pixmap_with_text(pixmap, text))
        else:
            # 无文本，只发送图片
            logger.info("发送纯图片消息")
            asyncio.create_task(chat_manager.send_pixmap_with_text(pixmap, ""))


class PetScreenshotSelector(ScreenshotSelector):
    """宠物截图选择器"""
    
    def __init__(self, pet):
        super().__init__()
        self.pet = pet
    
    def on_screenshot_captured(self, pixmap, text=""):
        """处理截图结果
        
        参数:
            pixmap: 截图 QPixmap
            text: 用户输入的文本说明（可选）
        """
        self.pet.screenshot_manager.handle_screenshot(pixmap, text)
    
    def on_screenshot_canceled(self):
        """处理取消截图"""
        # 重置截图状态
        self.pet.screenshot_manager.is_screenshotting = False
        logger.info("截图已取消，已重置截图状态")
        
        # 恢复主窗口和气泡显示
        self.pet.show()
        for chat_bubble in self.pet.chat_bubbles._active_bubbles:
            chat_bubble.show()
    
    def _on_ocr_triggered(self):
        """OCR识别功能实现"""
        try:
            # 获取选区截图
            screen = QApplication.primaryScreen()
            full_pixmap = screen.grabWindow(0)
            selected_pixmap = full_pixmap.copy(self.selection_rect)
            
            # 转换为 base64
            image_base64 = pixmap_to_base64(selected_pixmap)
            
            logger.info("OCR识别功能触发，发送请求到 Vision API")
            
            # 先关闭截图窗口，恢复界面
            self.pet.screenshot_manager.is_screenshotting = False
            self.pet.show()
            for chat_bubble in self.pet.chat_bubbles._active_bubbles:
                chat_bubble.show()
            self.close()
            logger.info("截图窗口已关闭")
            
            # 显示"正在识别"提示
            self.pet.show_notice("正在识别文字...")
            
            # OCR 专用 prompt
            ocr_prompt = """请识别图片中的文字内容，只输出识别到的文字，不要添加任何解释或说明。"""

            # 使用识图接口
            asyncio.create_task(chat_manager.recognize_image(
                image_base64=image_base64,
                prompt=ocr_prompt,
                callback=self.ocr_callback
            ))
            
        except Exception as e:
            logger.error(f"OCR识别失败: {e}", exc_info=True)
            self.pet.show_notice("OCR识别失败，请重试")
    

    def _on_translate_triggered(self):
        """翻译功能实现"""
        try:
            # 获取选区截图
            screen = QApplication.primaryScreen()
            full_pixmap = screen.grabWindow(0)
            selected_pixmap = full_pixmap.copy(self.selection_rect)
            
            # 转换为 base64
            image_base64 = pixmap_to_base64(selected_pixmap)
            
            logger.info("翻译功能触发，发送请求到 Vision API")
            
            # 先关闭截图窗口，恢复界面
            self.pet.screenshot_manager.is_screenshotting = False
            self.pet.show()
            for chat_bubble in self.pet.chat_bubbles._active_bubbles:
                chat_bubble.show()
            self.close()
            logger.info("截图窗口已关闭")
            
            # 显示"正在翻译"提示
            self.pet.show_notice("正在翻译...")

            # 使用翻译接口
            asyncio.create_task(chat_manager.translate_image(
                image_base64=image_base64,
                callback=self.ocr_callback
            ))
            
        except Exception as e:
            logger.error(f"翻译失败: {e}", exc_info=True)
            self.pet.show_notice("翻译失败，请重试")

    def ocr_callback(self, success: bool, task_type: str, response: str = None):
        """OCR 结果回调
        
        Args:
            success: 是否成功
            task_type: 任务类型
            response: 响应文本
        """
        logger.info(f"OCR回调收到结果，成功: {success}, 任务类型: {task_type},response: {response}")
        if success and response:
            logger.info(f"OCR识别结果: {response}")
            title = "【翻译结果】" if task_type == "translation" else "【识别结果】"
            notice_text = f"{title}\n{response}"

            def copy_result(event=None, result=response):
                try:
                    clipboard = QApplication.clipboard()
                    clipboard.setText(result)
                    logger.info("识别结果已复制到剪贴板")
                    self.pet.show_click_feedback("已复制到剪贴板", event)
                except Exception as e:
                    logger.error(f"写入剪贴板失败: {e}", exc_info=True)
                    self.pet.show_notice("复制失败")

            self.pet.show_notice(notice_text, on_click=copy_result)
        else:
            self.pet.show_notice("OCR识别失败")

    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 重置截图状态
        if self.pet.screenshot_manager.is_screenshotting:
            self.pet.screenshot_manager.is_screenshotting = False
            logger.info("截图窗口关闭，已重置截图状态")
        
        super().closeEvent(event)


# 注意：不在模块级别创建实例，因为 QApplication 还未创建
# 实例将在 main.py 中创建
