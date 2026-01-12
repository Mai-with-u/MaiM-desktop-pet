import asyncio
from src.frontend.signals import signals_bus
from config import load_config
from src.util.logger import logger
from src.core.protocol_manager import protocol_manager

# 加载配置
config = load_config()
from src.database import db_manager

# 兼容性：保留旧的 router 接口
# RouterAdapter 提供与旧 Router 兼容的接口
class RouterAdapter:
    """路由器适配器 - 将协议管理器适配为旧 Router 接口"""
    
    def __init__(self):
        self._message_handlers = []
        self._initialized = False
    
    def register_class_handler(self, handler):
        """注册消息处理器（兼容旧接口）"""
        self._message_handlers.append(handler)
        logger.debug(f"注册消息处理器: {handler.__name__}")
    
    async def send_message(self, message):
        """发送消息（兼容旧接口）"""
        return await protocol_manager.send_message(message)
    
    async def run(self):
        """运行路由器（兼容旧接口）"""
        logger.info("RouterAdapter 运行中...")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("RouterAdapter 被取消")
    
    async def stop(self):
        """停止路由器（兼容旧接口）"""
        logger.info("RouterAdapter 停止中...")
        await protocol_manager.cleanup()

# 创建路由器适配器实例
router = RouterAdapter()

def register_router():
    """向线程管理器注册协议管理器（延迟启动）"""
    from src.core.thread_manager import thread_manager
    from src.util.logger import logger
    
    logger.info("向线程管理器注册 ProtocolManager...")
    
    # 注册延迟启动的线程
    thread_manager.register_thread_deferred(
        target=lambda: asyncio.run(run_protocol_manager_async()),
        name="ProtocolManager",
        daemon=True
    )

async def cleanup_router():
    """清理协议管理器"""
    from src.util.logger import logger
    
    logger.info("正在关闭协议管理器...")
    try:
        await protocol_manager.cleanup()
        logger.info("已关闭所有协议连接")
    except Exception as e:
        logger.error(f"关闭协议管理器时出错: {e}", exc_info=True)

async def run_protocol_manager_async():
    """异步运行协议管理器"""
    from src.core.thread_manager import thread_manager
    
    # 注册清理函数
    thread_manager.register_cleanup(cleanup_router)
    
    # 注册消息处理器到协议管理器
    protocol_manager.register_message_handler(message_handler)
    
    try:
        # 检查配置中是否有协议
        if not config.protocols or len(config.protocols) == 0:
            # 如果没有配置协议，使用旧的 url 和 platform 创建默认配置
            logger.warning("配置文件中未找到协议配置，使用旧配置创建默认 Maim 协议")
            protocol_configs = [{
                'type': 'maim',
                'url': config.url,
                'platform': config.platform
            }]
        else:
            # 转换为字典格式
            protocol_configs = [p.dict() if hasattr(p, 'dict') else p for p in config.protocols]
        
        # 初始化协议管理器
        await protocol_manager.initialize(protocol_configs)
        
        # 打印协议状态
        protocol_manager.print_status()
        
        # 等待连接建立
        await asyncio.sleep(2)

        # 保持运行直到被中断
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"协议管理器运行出错: {e}", exc_info=True)
    finally:
        logger.info("协议管理器正在关闭...")
        await protocol_manager.cleanup()

async def main():
    """
    主函数（保留用于直接运行 router 的场景）
    注意：正常情况下应该使用 register_router() 注册到线程管理器
    """
    await run_protocol_manager_async()


async def message_handler(message):
    """
    消息处理函数
    从协议层收到的消息将会进入此函数
    注意：消息格式转换（如 seglist → text）已在各协议内部完成
    """
    # 提取消息内容
    logger.info(f"收到消息: {message}")
    
    # 将接收到的消息保存到数据库
    try:
        if db_manager.is_initialized():
            save_success = await db_manager.save_message(message)
            if save_success:
                logger.debug(f"接收消息已保存到数据库")
            else:
                logger.warning(f"接收消息保存到数据库失败")
        else:
            logger.debug(f"数据库未初始化，跳过消息存储")
    except Exception as e:
        logger.error(f"保存接收消息到数据库时出错: {e}", exc_info=True)
    
    # 解析消息并发送到信号总线
    # 注意：此时消息应该已经是统一的 text 格式
    message_segment = message.get('message_segment', {})
    
    if not message_segment:
        logger.warning(f"消息格式错误，缺少 message_segment: {message}")
        return
    
    message_type = message_segment.get('type', '')
    message_data = message_segment.get('data', '')
    
    if message_type == "text":
        message_content = str(message_data)
        signals_bus.message_received.emit(message_content)  # 跨线程安全
    else:
        logger.warning(f"不支持的消息格式: {message_type}")
