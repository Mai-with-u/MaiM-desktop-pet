import sys
import asyncio
import src.util.except_hook
from PyQt5.QtWidgets import QApplication
from src.core.thread_manager import thread_manager
import qasync

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

async def setup_backend_services():
    """设置所有后台服务"""
    from src.util.logger import logger
    
    # 初始化数据库
    await initialize_database()
    
    logger.info("后台服务初始化完成")

async def main():
    """主函数 - 使用 qasync 事件循环"""
    from src.util.logger import logger
    from src.frontend.presentation.pet import DesktopPet
    
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    
    # 设置 qasync 事件循环
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 初始化后台服务
    await setup_backend_services()
    
    # 创建并显示桌面宠物
    chat_pet = DesktopPet()
    logger.info("✓ 桌面宠物启动")
    chat_pet.show()
    
    # 启动事件循环
    with loop:
        await loop.run_forever()

if __name__ == "__main__":
    try:
        # 使用 asyncio.run 启动主函数
        # qasync 会在内部集成 Qt 事件循环
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序正在退出...")
        sys.exit(0)