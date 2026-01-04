import sys
import threading
import src.util.except_hook
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

def run():
    import asyncio
    from src.core.router import main
    asyncio.run(main())

if __name__ == "__main__":
    try:
        # 在单独线程中运行 FastAPI
        api_thread = threading.Thread(target=run, daemon=True)
        api_thread.start()
        
        from src.frontend.pet import chat_pet
        chat_pet.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n程序正在退出...")
        sys.exit(0)
