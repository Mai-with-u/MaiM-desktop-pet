import sys
import threading
import asyncio
import src.util.except_hook
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

def run():
    from src.core.router import main
    asyncio.run(main())

async def initialize_database():
    """初始化数据库"""
    from src.database import db_manager
    from config import config
    from src.util.logger import logger
    
    try:
        if config.database:
            db_type = config.database.get('type', 'sqlite')
            db_path = config.database.get('path', 'data/chat.db')
            
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
        
        # 配置：是否使用重构后的架构
        USE_REFACTORED_ARCHITECTURE = True
        
        if USE_REFACTORED_ARCHITECTURE:
            # 使用重构后的架构
            from src.frontend.presentation.refactored_pet import refactored_pet
            chat_pet = refactored_pet
            print("✓ 使用重构后的架构")
        else:
            # 使用旧架构（向后兼容）
            from src.frontend.pet import chat_pet
            print("✓ 使用旧架构")
        
        chat_pet.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n程序正在退出...")
        sys.exit(0)
