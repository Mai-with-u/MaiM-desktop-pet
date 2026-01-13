"""
全局热键管理器
负责注册和管理全局热键
"""

from typing import Callable, Optional, Dict
from pynput import keyboard
from src.util.logger import logger


class HotkeyManager:
    """
    全局热键管理器
    
    职责：
    - 全局热键的注册和管理
    - 支持多个热键
    - 自动清理资源
    """
    
    def __init__(self):
        self.hotkeys = {}  # {快捷键名称: (快捷键字符串, 回调函数)}
        self.listener: Optional[keyboard.Listener] = None
        self._is_listening = False
        
        logger.info("热键管理器初始化完成")
    
    def register_hotkey(
        self,
        name: str,
        shortcut_str: str,
        callback: Callable[[], None]
    ) -> bool:
        """
        注册一个全局热键
        
        Args:
            name: 热键名称（用于识别）
            shortcut_str: 快捷键字符串，如 "Ctrl+Shift+A"
            callback: 热键触发时的回调函数
            
        Returns:
            bool: 是否注册成功
        """
        if not shortcut_str:
            logger.warning(f"快捷键字符串为空，跳过注册: {name}")
            return False
        
        # 转换为 pynput 格式
        pynput_hotkey = self._convert_to_pynput_format(shortcut_str)
        if not pynput_hotkey:
            logger.error(f"无法转换快捷键: {shortcut_str}")
            return False
        
        # 保存热键信息
        self.hotkeys[name] = (shortcut_str, callback)
        logger.info(f"已注册全局热键 [{name}]: {shortcut_str}")
        return True
    
    def unregister_hotkey(self, name: str):
        """
        注销一个全局热键
        
        Args:
            name: 热键名称
        """
        if name in self.hotkeys:
            shortcut_str, _ = self.hotkeys[name]
            del self.hotkeys[name]
            logger.info(f"已注销全局热键 [{name}]: {shortcut_str}")
        else:
            logger.warning(f"尝试注销不存在的热键: {name}")
    
    def start(self):
        """启动全局热键监听"""
        if self._is_listening:
            logger.warning("热键监听器已经在运行")
            return
        
        if not self.hotkeys:
            logger.warning("没有注册任何热键，跳过启动监听器")
            return
        
        try:
            # 构建 GlobalHotKeys 需要的映射
            hotkey_map = {}
            for name, (shortcut_str, callback) in self.hotkeys.items():
                pynput_hotkey = self._convert_to_pynput_format(shortcut_str)
                if pynput_hotkey:
                    hotkey_map[pynput_hotkey] = lambda name=name: self._trigger_hotkey(name)
            
            if not hotkey_map:
                logger.error("没有有效的热键可以注册")
                return False
            
            # 创建全局热键监听器
            self.listener = keyboard.GlobalHotKeys(hotkey_map)
            self.listener.start()
            self._is_listening = True
            logger.info(f"全局热键监听器已启动（共 {len(self.hotkeys)} 个热键）")
            return True
            
        except Exception as e:
            logger.error(f"启动热键监听器失败: {e}", exc_info=True)
            return False
    
    def stop(self):
        """停止全局热键监听"""
        if not self._is_listening:
            return
        
        try:
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            self._is_listening = False
            logger.info("全局热键监听器已停止")
            
        except Exception as e:
            logger.error(f"停止热键监听器失败: {e}", exc_info=True)
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("清理热键管理器资源...")
        
        # 停止监听
        self.stop()
        
        # 清空热键
        self.hotkeys.clear()
        
        logger.info("热键管理器资源已清理")
    
    def _convert_to_pynput_format(self, shortcut_str: str) -> Optional[str]:
        """
        将快捷键字符串转换为 pynput 格式
        
        Args:
            shortcut_str: 如 "Ctrl+Shift+A"
            
        Returns:
            pynput 格式的字符串，如 "<ctrl>+<shift>+a"
        """
        parts = [part.strip().lower() for part in shortcut_str.split('+')]
        pynput_parts = []
        
        for part in parts:
            if part == 'ctrl':
                pynput_parts.append('<ctrl>')
            elif part == 'alt':
                pynput_parts.append('<alt>')
            elif part == 'shift':
                pynput_parts.append('<shift>')
            elif part in ['cmd', 'win', 'meta']:
                pynput_parts.append('<cmd>')
            elif len(part) == 1:
                # 普通字符键
                pynput_parts.append(part)
            else:
                logger.warning(f"无法识别的快捷键部分: {part}")
                return None
        
        return '+'.join(pynput_parts)
    
    def _trigger_hotkey(self, name: str):
        """
        触发热键回调
        
        Args:
            name: 热键名称
        """
        if name in self.hotkeys:
            _, callback = self.hotkeys[name]
            try:
                logger.info(f"全局热键被触发: {name}")
                callback()
            except Exception as e:
                logger.error(f"执行热键回调 [{name}] 时出错: {e}", exc_info=True)
        else:
            logger.warning(f"触发了未注册的热键: {name}")
    
    def is_listening(self) -> bool:
        """是否正在监听"""
        return self._is_listening
    
    def get_registered_hotkeys(self) -> list:
        """获取已注册的热键列表"""
        return list(self.hotkeys.keys())
