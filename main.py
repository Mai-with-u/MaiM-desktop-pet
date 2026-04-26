import sys
import asyncio
import src.util.except_hook
from PyQt5.QtWidgets import QApplication
import qasync


async def initialize_database():
    """初始化数据库"""
    from src.database import db_manager
    from config import load_config
    from src.util.logger import logger

    config = load_config()

    try:
        if config and config.database:
            db_type = getattr(config.database, 'type', 'sqlite')
            db_path = getattr(config.database, 'path', 'data/chat.db')

            success = await db_manager.initialize(
                db_type=db_type,
                path=db_path
            )

            if success:
                logger.info(f"数据库初始化成功: {db_type} ({db_path})")
            else:
                logger.warning("数据库初始化失败")
        else:
            logger.warning("未配置数据库")
    except Exception as e:
        logger.error(f"数据库初始化出错: {e}")


async def setup_backend_services():
    """设置所有后台服务"""
    from src.util.logger import logger
    from src.core.chat import chat_manager

    # 初始化数据库
    await initialize_database()

    # 初始化聊天管理器
    try:
        success = await chat_manager.initialize('chat')
        if success:
            logger.info("聊天管理器初始化成功")
        else:
            logger.warning("聊天管理器初始化失败")
    except Exception as e:
        logger.error(f"聊天管理器初始化出错: {e}", exc_info=True)


async def main():
    """初始化后台服务并创建桌面宠物"""
    from src.util.logger import logger
    from src.frontend.presentation.pet import DesktopPet

    # 初始化后台服务
    await setup_backend_services()

    # 创建并显示桌面宠物
    chat_pet = DesktopPet()
    logger.info("✓ 桌面宠物启动")
    chat_pet.show()

    return chat_pet


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    chat_pet = None

    try:
        with loop:
            chat_pet = loop.run_until_complete(main())
            loop.run_forever()
    except KeyboardInterrupt:
        print("\n程序正在退出...")
    finally:
        if chat_pet is not None:
            try:
                chat_pet.cleanup_resources()
            except Exception:
                pass
        loop.close()
        sys.exit(0)
