import sys
import threading
import asyncio
import atexit
import src.util.except_hook
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

# 全局变量，用于存储清理函数
cleanup_functions = []

def register_cleanup(func):
    """注册清理函数"""
    cleanup_functions.append(func)

async def cleanup_all():
    """执行所有清理操作"""
    from src.util.logger import logger
    
    logger.info("开始清理资源...")
    
    # 执行所有注册的清理函数
    for cleanup_func in cleanup_functions:
        try:
            if asyncio.iscoroutinefunction(cleanup_func):
                await cleanup_func()
            else:
                cleanup_func()
        except Exception as e:
            logger.error(f"清理函数执行失败: {e}", exc_info=True)
    
    logger.info("资源清理完成")

def run():
    from src.core.router import main
    asyncio.run(main())

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
        
        # 在单独线程中运行 FastAPI
        api_thread = threading.Thread(target=run, daemon=True)
        api_thread.start()
        
        from src.frontend.presentation.pet import desktop_pet
        chat_pet = desktop_pet
        print("✓ 使用重构后的架构")
        
        chat_pet.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n程序正在退出...")
        sys.exit(0)
