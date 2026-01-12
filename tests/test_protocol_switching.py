"""
协议切换测试脚本
测试协议管理器的协议切换功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.protocol_manager import protocol_manager
from src.util.logger import logger


class TestMessageHandler:
    """测试消息处理器"""
    
    def __init__(self):
        self.messages = []
    
    async def __call__(self, message):
        """处理接收到的消息"""
        self.messages.append(message)
        
        msg_type = message.get('message_segment', {}).get('type', 'unknown')
        msg_data = message.get('message_segment', {}).get('data', '')
        
        logger.info(f"测试处理器收到消息 - 类型: {msg_type}, 内容: {msg_data[:50]}...")


async def test_basic_functionality():
    """测试基本功能"""
    logger.info("=" * 60)
    logger.info("测试 1: 基本功能测试")
    logger.info("=" * 60)
    
    # 创建消息处理器
    handler = TestMessageHandler()
    
    # 测试 1.1: 注册消息处理器
    protocol_manager.register_message_handler(handler)
    logger.info("✓ 消息处理器已注册")
    
    # 测试 1.2: 获取协议名称
    if hasattr(protocol_manager, '_protocols') and protocol_manager._protocols:
        names = protocol_manager.get_protocol_names()
        logger.info(f"✓ 可用协议: {names}")
    else:
        logger.warning("⚠ 没有可用的协议")
    
    # 测试 1.3: 打印状态
    protocol_manager.print_status()
    
    logger.info("✓ 基本功能测试完成\n")


async def test_protocol_switching():
    """测试协议切换"""
    logger.info("=" * 60)
    logger.info("测试 2: 协议切换测试")
    logger.info("=" * 60)
    
    # 获取所有协议
    protocols = protocol_manager.get_protocol_names()
    
    if len(protocols) < 2:
        logger.warning("⚠ 需要至少配置 2 个协议才能测试切换功能")
        logger.info("✓ 跳过协议切换测试\n")
        return
    
    # 测试切换顺序
    for i in range(len(protocols)):
        current_protocol = protocols[i]
        next_protocol = protocols[(i + 1) % len(protocols)]
        
        logger.info(f"切换协议: {current_protocol} → {next_protocol}")
        
        # 切换协议
        success = await protocol_manager.switch_protocol(next_protocol)
        
        if success:
            active = protocol_manager.get_active_protocol()
            if active and active.get_name() == next_protocol:
                logger.info(f"✓ 协议切换成功: {next_protocol}")
            else:
                logger.error(f"✗ 协议切换失败: 激活的协议不是 {next_protocol}")
        else:
            logger.error(f"✗ 协议切换失败: {next_protocol}")
        
        # 等待连接建立
        await asyncio.sleep(1)
    
    logger.info("✓ 协议切换测试完成\n")


async def test_message_sending():
    """测试消息发送"""
    logger.info("=" * 60)
    logger.info("测试 3: 消息发送测试")
    logger.info("=" * 60)
    
    # 检查是否有激活的协议
    active_protocol = protocol_manager.get_active_protocol()
    
    if not active_protocol:
        logger.warning("⚠ 没有激活的协议，跳过消息发送测试")
        logger.info("✓ 跳过消息发送测试\n")
        return
    
    if not protocol_manager.is_active_protocol_connected():
        logger.warning("⚠ 激活的协议未连接，跳过消息发送测试")
        logger.info("✓ 跳过消息发送测试\n")
        return
    
    # 测试发送文本消息
    test_message = "这是一条测试消息"
    logger.info(f"发送测试消息: {test_message}")
    
    success = await protocol_manager.send_message({
        'message_segment': {
            'type': 'text',
            'data': test_message
        }
    })
    
    if success:
        logger.info("✓ 消息发送成功")
    else:
        logger.error("✗ 消息发送失败")
    
    logger.info("✓ 消息发送测试完成\n")


async def test_error_handling():
    """测试错误处理"""
    logger.info("=" * 60)
    logger.info("测试 4: 错误处理测试")
    logger.info("=" * 60)
    
    # 测试 4.1: 切换到不存在的协议
    logger.info("测试: 切换到不存在的协议")
    success = await protocol_manager.switch_protocol("NonExistentProtocol")
    
    if not success:
        logger.info("✓ 正确拒绝了不存在的协议")
    else:
        logger.error("✗ 错误: 接受了不存在的协议")
    
    # 测试 4.2: 发送无效消息
    logger.info("测试: 发送无效消息格式")
    success = await protocol_manager.send_message({})
    
    if not success:
        logger.info("✓ 正确拒绝了无效消息")
    else:
        logger.error("✗ 错误: 接受了无效消息")
    
    logger.info("✓ 错误处理测试完成\n")


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("协议管理器测试开始")
    logger.info("=" * 60)
    logger.info()
    
    try:
        # 初始化协议管理器
        # 注意：这里使用模拟配置，实际使用时应该从 config.toml 加载
        protocol_configs = [
            {
                'type': 'maim',
                'url': 'ws://127.0.0.1:8000/ws',
                'platform': 'desktop-pet-test'
            },
            {
                'type': 'openai',
                'api_key': 'sk-test-key',
                'model': 'gpt-3.5-turbo'
            }
        ]
        
        await protocol_manager.initialize(protocol_configs)
        
        # 运行测试
        await test_basic_functionality()
        await test_protocol_switching()
        await test_message_sending()
        await test_error_handling()
        
        # 总结
        logger.info("=" * 60)
        logger.info("所有测试完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}", exc_info=True)
    
    finally:
        # 清理
        logger.info("\n清理协议管理器...")
        await protocol_manager.cleanup()
        logger.info("✓ 清理完成")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
