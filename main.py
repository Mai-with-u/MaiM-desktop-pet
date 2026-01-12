import sys
import asyncio
import atexit
import src.util.except_hook
from PyQt5.QtWidgets import QApplication
from src.core.thread_manager import thread_manager

app = QApplication(sys.argv)

# 全局安全退出函数
def safe_quit():
    """安全退出应用 - 统一管理所有清理和退出逻辑"""
    from src.util.logger import logger
    import sys
    
    logger.info("=" * 60)
    logger.info("safe_quit() 被调用 - main.py (atexit 回调)")
    logger.info("=" * 60)
    
    try:
        # 1. 清理桌面宠物资源
        from src.frontend.presentation.pet import desktop_pet
        if desktop_pet:
            logger.info("开始清理桌面宠物资源...")
            desktop_pet.cleanup_resources()
            logger.info("桌面宠物资源清理完成")
        
        # 2. 退出 Qt 事件循环
        logger.info("准备退出 Qt 事件循环...")
        app.quit()
        logger.info("QApplication.quit() 已调用")
        
        # 3. 不需要调用 sys.exit(0)，因为 atexit 回调已经在退出过程中了
        logger.info("atexit 回调完成，进程即将退出...")
        
    except SystemExit as e:
        # SystemExit 是正常的退出，记录日志后重新抛出
        logger.info(f"程序正在退出，退出码: {e.code}")
        raise
    except Exception as e:
        logger.error(f"安全退出过程中出错: {e}", exc_info=True)
        # atexit 回调中的错误不会阻止进程退出，所以不需要 sys.exit(1)

# 注册为 atexit 回调
atexit.register(safe_quit)

async def run_router():
    """运行路由器"""
    from src.core.router import main
    await main()

async def initialize_database():
    """初始化数据库"""
    from src.database import db_manager
    from config import load_config
    from src.util.logger import logger
    
    config = load_config()
    
    try:
        if config.database:
            db_type = getattr(config.database, 'type', 'sqlite')
            db_path = getattr(config.database, 'path', 'data/chat.db')
            
            success = await db_manager.initialize(
                db_type=db_type,
                path=db_path
            )
            
            if success:
                logger.info(f"数据库初始化成功: {db_type} ({db_path})")
            else:
                logger.warning("数据库初始化失败，消息将不会保存到数据库")
        else:
            logger.warning("未配置数据库，消息将不会保存到数据库")
    except Exception as e:
        logger.error(f"数据库初始化出错: {e}")

if __name__ == "__main__":
    try:
        # 初始化数据库（异步）
        asyncio.run(initialize_database())
        
        # 各个模块向线程管理器注册自己的线程
        print("正在注册后台服务...")
        
        # 注册 MaimRouter
        from src.core.router import register_router
        register_router()
        
        # 如果需要，可以在这里注册其他服务
        # from src.core.some_service import register_some_service
        # register_some_service()
        
        print(f"已注册 {len(thread_manager._thread_configs)} 个后台服务")
        
        # 启动所有延迟注册的线程
        thread_manager.start_all()
        
        # 打印线程状态
        thread_manager.print_status()
        
        from src.frontend.presentation.pet import desktop_pet
        chat_pet = desktop_pet
        print("✓ 使用重构后的架构")
        
        chat_pet.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n程序正在退出...")
        sys.exit(0)
