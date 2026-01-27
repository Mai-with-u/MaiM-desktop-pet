"""
重构后的桌面宠物主窗口
展示如何使用新的架构
"""

import asyncio
import atexit
import random
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QShortcut
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon, QKeySequence

from src.core.chat_manager import chat_manager
from src.core.thread_manager import thread_manager
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

# 从 main.py 导入 QApplication 实例（避免创建多个实例）
# 注意：这个导入需要在模块级别，所以会导致循环依赖
# 我们通过 sys.modules 来获取已创建的 app 实例
def get_qapp():
    """获取 QApplication 实例"""
    from PyQt5.QtWidgets import QApplication
    return QApplication.instance()

app = get_qapp()

# 全局桌面宠物实例引用（延迟初始化）
_desktop_pet_instance = None

def safe_quit_global():
    """全局安全退出函数 - 确保无论如何退出都能清理所有资源"""
    global _desktop_pet_instance
    logger.info("全局清理资源...")
    if _desktop_pet_instance:
        try:
            # 不再调用 safe_quit（它会创建 event loop）
            # 只执行必要的同步清理
            # 协议管理器的清理已经在自己的线程中处理
            logger.info("全局清理：守护线程将自动退出")
        except Exception as e:
            logger.error(f"全局清理时出错: {e}", exc_info=True)


atexit.register(safe_quit_global)

# 连接应用程序退出信号 - 处理 PyQt 应用的正常退出
# 注意：这可能在 atexit 之前触发，所以需要处理重复调用
# app.aboutToQuit.connect(safe_quit_global)


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
        
        # 注册清理函数到线程管理器
        self._register_cleanup_functions()
        
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
        
        # 保存全局引用以便在强制退出时也能清理
        global _desktop_pet_instance
        _desktop_pet_instance = self
        
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
        """初始化全局快捷键"""
        logger.info(f"开始初始化全局快捷键...")
        
        # 注册截图热键
        if config.Screenshot_shortcuts is not None:
            success = self.hotkey_manager.register_hotkey(
                name="screenshot",
                shortcut_str=config.Screenshot_shortcuts,
                callback=self._on_screenshot_hotkey
            )
            
            if success:
                logger.info(f"✓ 已注册全局截图快捷键: {config.Screenshot_shortcuts}")
            else:
                # 降级使用 QShortcut
                logger.warning("全局热键注册失败，降级使用 QShortcut")
                self._init_fallback_shortcut()
        else:
            logger.info(f"截图快捷键未配置（值为 None）")
        
        # 启动热键监听器
        self.hotkey_manager.start()
    
    def _init_fallback_shortcut(self):
        """降级使用 QShortcut（仅窗口有焦点时有效）"""
        if config.Screenshot_shortcuts is not None:
            logger.info(f"使用 QShortcut 注册截图快捷键: {config.Screenshot_shortcuts}")
            shortcut = QShortcut(QKeySequence(config.Screenshot_shortcuts), self)
            shortcut.activated.connect(self.screenshot_manager.start_screenshot)
            logger.info(f"✓ 截图快捷键注册成功（仅窗口有焦点时有效）")
    
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
        if hasattr(self, 'chat_bubbles'):
            for bubble in self.chat_bubbles._active_bubbles:
                bubble.hide()
        if hasattr(self, 'bubble_input'):
            self.bubble_input.hide()
        
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
        self.bubble_manager.show_message(text, msg_type, pixmap)
    
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
        self.show_message(text=text, msg_type="sent")
        
        # 使用 qasync 事件循环，创建异步任务而不阻塞主线程
        asyncio.create_task(chat_manager.send_text(
            str(text),
            additional_config={
                "maimcore_reply_probability_gain": 1  # 回复概率增益（Maim 协议专用）
            }
        ))
    
    def cleanup_resources(self):
        """清理所有资源（不包含退出逻辑）"""
        # 防止重复清理
        if hasattr(self, '_is_cleaning_up') and self._is_cleaning_up:
            logger.info("已经在清理中，跳过重复调用")
            return
        
        self._is_cleaning_up = True
        logger.info("开始清理资源...")
        
        try:
            # 执行线程管理器中注册的所有清理函数
            # 这包括了前端管理器的清理函数和协议管理器的清理函数
            from src.core.thread_manager import thread_manager
            
            logger.info(f"共有 {len(thread_manager._cleanup_functions)} 个清理函数")
            
            # 分离同步和异步清理函数
            sync_cleanup_funcs = [
                f for f in thread_manager._cleanup_functions 
                if not asyncio.iscoroutinefunction(f)
            ]
            async_cleanup_funcs = [
                f for f in thread_manager._cleanup_functions 
                if asyncio.iscoroutinefunction(f)
            ]
            
            # 执行同步清理函数
            for cleanup_func in sync_cleanup_funcs:
                try:
                    logger.info(f"[同步] 执行清理函数: {cleanup_func.__name__}")
                    cleanup_func()
                    logger.info(f"[同步] {cleanup_func.__name__} 执行完成")
                except Exception as e:
                    logger.error(
                        f"执行同步清理函数时出错: {cleanup_func.__name__}, 错误: {e}",
                        exc_info=True
                    )
            
            # 执行异步清理函数（创建新的事件循环）
            if async_cleanup_funcs:
                try:
                    logger.info(f"开始执行 {len(async_cleanup_funcs)} 个异步清理函数...")
                    # 创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        for cleanup_func in async_cleanup_funcs:
                            try:
                                logger.info(f"[异步] 执行清理函数: {cleanup_func.__name__}")
                                loop.run_until_complete(cleanup_func())
                                logger.info(f"[异步] {cleanup_func.__name__} 执行完成")
                            except Exception as e:
                                logger.error(
                                    f"执行异步清理函数时出错: {cleanup_func.__name__}, 错误: {e}",
                                    exc_info=True
                                )
                    finally:
                        # 取消所有未完成的任务
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            logger.info(f"取消 {len(pending)} 个未完成的异步任务...")
                            for task in pending:
                                task.cancel()
                            # 等待任务被取消
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
            
            logger.info("OCR识别功能触发，发送请求到LLM")
            
            # 先关闭截图窗口，恢复界面
            self.pet.screenshot_manager.is_screenshotting = False
            self.pet.show()
            for chat_bubble in self.pet.chat_bubbles._active_bubbles:
                chat_bubble.show()
            self.close()
            logger.info("截图窗口已关闭")
            
            # 显示"正在识别"提示
            self.pet.show_message("正在识别文字...", msg_type="received")
            
            # 构建 OCR prompt
            ocr_prompt = """请识别图片中的文字内容，只输出识别到的文字，不要添加任何解释或说明。"""
            
            # 使用 image_recognition 任务发送请求（使用 qasync 事件循环）
            asyncio.create_task(chat_manager.send_by_task(
                task_type='image_recognition',
                text=ocr_prompt,
                image_data=image_base64,
                callback=self.ocr_callback
            ))
            
        except Exception as e:
            logger.error(f"OCR识别失败: {e}", exc_info=True)
            self.pet.show_message("OCR识别失败，请重试", msg_type="received")
    

    def _on_translate_triggered(self):
        """翻译功能实现"""
        try:
            # 获取选区截图
            screen = QApplication.primaryScreen()
            full_pixmap = screen.grabWindow(0)
            selected_pixmap = full_pixmap.copy(self.selection_rect)
            
            # 转换为 base64
            image_base64 = pixmap_to_base64(selected_pixmap)
            
            logger.info("翻译功能触发，发送请求到LLM")
            
            # 先关闭截图窗口，恢复界面
            self.pet.screenshot_manager.is_screenshotting = False
            self.pet.show()
            for chat_bubble in self.pet.chat_bubbles._active_bubbles:
                chat_bubble.show()
            self.close()
            logger.info("截图窗口已关闭")
            
            # 显示"正在翻译"提示
            self.pet.show_message("正在翻译...", msg_type="received")
            
            # 构建翻译 prompt
            translate_prompt = """请识别图片中的文字内容，并将其翻译成中文。如果已经是中文，则翻译成英文。只输出翻译结果，不要添加任何解释或说明。"""
            
            # 使用 image_recognition 任务发送请求（使用 qasync 事件循环）
            asyncio.create_task(chat_manager.send_by_task(
                task_type='image_recognition',
                text=translate_prompt,
                image_data=image_base64
            ))
            
        except Exception as e:
            logger.error(f"翻译失败: {e}", exc_info=True)
            self.pet.show_message("翻译失败，请重试", msg_type="received")

    def ocr_callback(self, success: bool, task_type: str, response: str = None):
        """OCR 结果回调
        
        Args:
            success: 是否成功
            task_type: 任务类型
            response: 响应文本
        """
        logger.info(f"OCR回调收到结果，成功: {success}, 任务类型: {task_type},response: {response}")
        if success and response:
            self.pet.show_message(response, msg_type="received")
            logger.info(f"OCR识别结果: {response}")
        else:
            self.pet.show_message("OCR识别失败", msg_type="received")

    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 重置截图状态
        if self.pet.screenshot_manager.is_screenshotting:
            self.pet.screenshot_manager.is_screenshotting = False
            logger.info("截图窗口关闭，已重置截图状态")
        
        super().closeEvent(event)


# 注意：不在模块级别创建实例，因为 QApplication 还未创建
# 实例将在 main.py 中创建
