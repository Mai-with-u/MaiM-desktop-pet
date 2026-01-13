"""
测试热键管理器功能
"""

import time
from src.frontend.core.managers import HotkeyManager
from src.util.logger import logger


def test_hotkey_registration():
    """测试热键注册"""
    print("\n" + "=" * 60)
    print("测试 1: 热键注册")
    print("=" * 60)
    
    manager = HotkeyManager()
    
    # 测试回调函数
    callback_called = {"count": 0}
    
    def test_callback():
        callback_called["count"] += 1
        print(f"✓ 回调函数被触发（第 {callback_called['count']} 次）")
        logger.info(f"测试回调被触发：{callback_called['count']}")
    
    # 注册热键
    success = manager.register_hotkey(
        name="test_hotkey",
        shortcut_str="Ctrl+Shift+T",
        callback=test_callback
    )
    
    print(f"注册热键 Ctrl+Shift+T: {'成功' if success else '失败'}")
    print(f"已注册的热键: {manager.get_registered_hotkeys()}")
    
    # 启动监听
    manager.start()
    print(f"监听器状态: {'运行中' if manager.is_listening() else '未运行'}")
    
    print("\n请按 Ctrl+Shift+T 测试热键（按 Ctrl+C 退出测试）...")
    print("注意：无论焦点在哪里都应该能触发！")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断，停止测试...")
    
    # 清理
    manager.cleanup()
    print("热键管理器已清理")


def test_multiple_hotkeys():
    """测试多个热键"""
    print("\n" + "=" * 60)
    print("测试 2: 多个热键注册")
    print("=" * 60)
    
    manager = HotkeyManager()
    
    def callback1():
        print("✓ 热键 1 被触发 (Ctrl+Shift+1)")
    
    def callback2():
        print("✓ 热键 2 被触发 (Ctrl+Shift+2)")
    
    # 注册多个热键
    manager.register_hotkey("hotkey1", "Ctrl+Shift+1", callback1)
    manager.register_hotkey("hotkey2", "Ctrl+Shift+2", callback2)
    
    manager.start()
    
    print(f"已注册 {len(manager.get_registered_hotkeys())} 个热键")
    print("请按 Ctrl+Shift+1 或 Ctrl+Shift+2 测试（按 Ctrl+C 退出）...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断，停止测试...")
    
    manager.cleanup()


def test_hotkey_unregister():
    """测试热键注销"""
    print("\n" + "=" * 60)
    print("测试 3: 热键注销")
    print("=" * 60)
    
    manager = HotkeyManager()
    
    def test_callback():
        print("✓ 热键被触发")
    
    # 注册热键
    manager.register_hotkey("test", "Ctrl+Shift+U", test_callback)
    print(f"注册前: {manager.get_registered_hotkeys()}")
    
    # 注销热键
    manager.unregister_hotkey("test")
    print(f"注销后: {manager.get_registered_hotkeys()}")
    
    print("测试完成！")


if __name__ == "__main__":
    print("=" * 60)
    print("热键管理器测试套件")
    print("=" * 60)
    
    # 运行测试
    test_hotkey_registration()
    
    # 如果想测试多个热键，取消下面的注释
    # test_multiple_hotkeys()
    
    # 测试注销功能
    test_hotkey_unregister()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
