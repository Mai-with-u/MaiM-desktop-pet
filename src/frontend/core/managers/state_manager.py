"""
状态管理器
负责窗口状态管理
"""

import logging
import platform
from typing import Optional

from PyQt5.QtCore import QObject

logger = logging.getLogger(__name__)


class StateManager(QObject):
    """
    状态管理器 - 负责窗口状态管理
    
    职责：
    - 窗口锁定/解锁
    - 窗口显示/隐藏
    - 终端显示/隐藏
    - 状态持久化
    - 状态通知
    """
    
    def __init__(self, parent):
        """
        初始化状态管理器
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.parent = parent
        
        # 状态标志
        self._is_locked = False
        self._is_visible = True
        self._console_visible = True
        
        # 终端窗口句柄（Windows 专用）
        self.console_window = None
        self._init_console_window()
    
    def _init_console_window(self):
        """初始化终端窗口句柄"""
        if platform.system() == "Windows":
            try:
                import win32gui
                self.console_window = win32gui.GetForegroundWindow()
                logger.debug("终端窗口句柄已获取")
            except Exception as e:
                logger.error(f"获取终端窗口句柄失败: {e}")
                self.console_window = None
        else:
            self.console_window = None
    
    def is_locked(self) -> bool:
        """
        检查窗口是否锁定
        
        Returns:
            bool: 是否锁定
        """
        return self._is_locked
    
    def is_visible(self) -> bool:
        """
        检查窗口是否可见
        
        Returns:
            bool: 是否可见
        """
        return self._is_visible
    
    def is_console_visible(self) -> bool:
        """
        检查终端是否可见
        
        Returns:
            bool: 终端是否可见
        """
        return self._console_visible
    
    def lock_window(self):
        """锁定窗口，使其不可选中"""
        from PyQt5.QtCore import Qt
        
        logger.info("锁定窗口")
        
        # 设置窗口标志
        self.parent.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 始终在最前
            Qt.SubWindow |            # 子窗口
            Qt.WindowTransparentForInput  # 关键标志：使窗口不接收输入事件
        )
        
        self._is_locked = True
        self.parent.show()  # 必须调用show()才能使窗口标志更改生效
        
        # 隐藏所有气泡
        if hasattr(self.parent, 'bubble_manager'):
            self.parent.bubble_manager.hide_all()
        
        logger.debug("窗口已锁定")
    
    def unlock_window(self):
        """解锁窗口，恢复原始可选中状态"""
        from PyQt5.QtCore import Qt
        
        logger.info("解锁窗口")
        
        # 设置窗口标志
        self.parent.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 始终在最前
            Qt.SubWindow              # 子窗口
        )
        
        self._is_locked = False
        self.parent.show()  # 必须调用show()才能使窗口标志更改生效
        
        logger.debug("窗口已解锁")
    
    def toggle_lock(self):
        """切换锁定状态"""
        if self._is_locked:
            self.unlock_window()
        else:
            self.lock_window()
    
    def hide_window(self):
        """隐藏窗口"""
        logger.debug("隐藏窗口")
        self._is_visible = False
        self.parent.hide()
    
    def show_window(self):
        """显示窗口"""
        logger.debug("显示窗口")
        self._is_visible = True
        self.parent.show()
    
    def toggle_window(self):
        """切换窗口显示/隐藏"""
        if self._is_visible:
            self.hide_window()
        else:
            self.show_window()
    
    def show_console(self):
        """显示终端窗口"""
        logger.debug("显示终端")
        
        if platform.system() == "Windows":
            if self.console_window:
                try:
                    import win32con
                    import win32gui
                    win32gui.ShowWindow(self.console_window, win32con.SW_SHOW)
                except Exception as e:
                    logger.error(f"显示终端失败: {e}")
        else:
            print("\n[终端已显示 - 输入Ctrl+C退出]\n")
        
        self._console_visible = True
    
    def hide_console(self):
        """隐藏终端窗口"""
        logger.debug("隐藏终端")
        
        if platform.system() == "Windows":
            if self.console_window:
                try:
                    import win32con
                    import win32gui
                    win32gui.ShowWindow(self.console_window, win32con.SW_HIDE)
                except Exception as e:
                    logger.error(f"隐藏终端失败: {e}")
        
        self._console_visible = False
    
    def toggle_console(self):
        """切换终端显示/隐藏"""
        if self._console_visible:
            self.hide_console()
        else:
            self.show_console()
    
    def save_state(self):
        """保存当前状态"""
        try:
            import tomli  # 用于读取 TOML
            import tomli_w  # 用于写入 TOML
            
            # 读取现有配置
            try:
                with open("config.toml", "rb") as f:
                    config_data = tomli.load(f)
            except FileNotFoundError:
                config_data = {}
            
            # 保存状态
            if 'state' not in config_data:
                config_data['state'] = {}
            
            config_data['state']['window_locked'] = self._is_locked
            config_data['state']['window_visible'] = self._is_visible
            config_data['state']['console_visible'] = self._console_visible
            
            # 写回文件
            with open("config.toml", "w", encoding='utf-8') as f:
                f.write(tomli_w.dumps(config_data))
            
            logger.debug("状态已保存")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def load_state(self):
        """加载保存的状态"""
        try:
            try:
                import tomli
            except ImportError:
                logger.warning("tomli 库未安装，无法加载状态")
                return
            
            # 读取配置
            with open("config.toml", "rb") as f:
                config_data = tomli.load(f)
            
            # 恢复状态
            if 'state' in config_data:
                state = config_data['state']
                
                # 恢复锁定状态
                if 'window_locked' in state and state['window_locked']:
                    self.lock_window()
                
                # 恢复可见状态
                if 'window_visible' in state:
                    if state['window_visible']:
                        self.show_window()
                    else:
                        self.hide_window()
                
                # 恢复终端状态
                if 'console_visible' in state:
                    if state['console_visible']:
                        self.show_console()
                    else:
                        self.hide_console()
                
                logger.debug("状态已加载")
        except FileNotFoundError:
            logger.debug("状态配置文件不存在，使用默认状态")
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        # 保存当前状态
        self.save_state()
        logger.info("状态管理器已清理")
