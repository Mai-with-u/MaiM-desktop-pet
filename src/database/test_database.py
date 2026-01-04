"""
数据库功能测试脚本
用于测试数据库的基本功能
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import db_manager
from src.util.logger import logger
import time
import uuid


async def test_database():
    """测试数据库功能"""
    
    logger.info("开始测试数据库功能...")
    
    # 1. 初始化数据库
    logger.info("步骤 1: 初始化数据库")
    success = await db_manager.initialize(
        db_type='sqlite',
        db_path='data/test_chat.db'
    )
    
    if not success:
        logger.error("数据库初始化失败")
        return False
    
    logger.info("✓ 数据库初始化成功")
    
    # 2. 清空旧数据
    logger.info("\n步骤 2: 清空旧数据")
    await db_manager.clear_all_messages()
    logger.info("✓ 旧数据已清空")
    
    # 3. 保存测试消息
    logger.info("\n步骤 3: 保存测试消息")
    test_messages = [
        {
            'message_info': {
                'message_id': str(uuid.uuid4()),
                'platform': 'desktop-pet',
                'time': time.time(),
            },
            'message_segment': {
                'type': 'text',
                'data': '你好，这是一条测试消息',
            },
            'raw_message': '你好，这是一条测试消息',
        },
        {
            'message_info': {
                'message_id': str(uuid.uuid4()),
                'platform': 'desktop-pet',
                'time': time.time(),
            },
            'message_segment': {
                'type': 'text',
                'data': '这是第二条测试消息',
            },
            'raw_message': '这是第二条测试消息',
        },
        {
            'message_info': {
                'message_id': str(uuid.uuid4()),
                'platform': 'desktop-pet',
                'time': time.time(),
            },
            'message_segment': {
                'type': 'image',
                'data': 'https://example.com/image.png',
            },
            'raw_message': '[图片]',
        },
    ]
    
    for i, msg in enumerate(test_messages, 1):
        success = await db_manager.save_message(msg)
        if success:
            logger.info(f"✓ 消息 {i} 保存成功: {msg['message_info']['message_id'][:8]}...")
        else:
            logger.error(f"✗ 消息 {i} 保存失败")
            return False
    
    # 4. 获取消息总数
    logger.info("\n步骤 4: 获取消息总数")
    count = await db_manager.get_message_count()
    logger.info(f"✓ 当前数据库中共有 {count} 条消息")
    
    # 5. 获取消息列表
    logger.info("\n步骤 5: 获取消息列表")
    messages = await db_manager.get_messages(limit=10)
    logger.info(f"✓ 获取到 {len(messages)} 条消息:")
    for msg in messages:
        logger.info(f"  - [{msg['message_type']}] {msg['message_content']} (ID: {msg['id'][:8]}...)")
    
    # 6. 根据ID获取单条消息
    logger.info("\n步骤 6: 根据ID获取单条消息")
    if messages:
        first_msg_id = messages[0]['id']
        message = await db_manager.get_message_by_id(first_msg_id)
        if message:
            logger.info(f"✓ 成功获取消息: {message['message_content']}")
        else:
            logger.error("✗ 获取消息失败")
            return False
    
    # 7. 搜索消息
    logger.info("\n步骤 7: 搜索消息")
    search_results = await db_manager.search_messages('测试', limit=10)
    logger.info(f"✓ 搜索到 {len(search_results)} 条包含'测试'的消息:")
    for msg in search_results:
        logger.info(f"  - {msg['message_content']}")
    
    # 8. 删除消息
    logger.info("\n步骤 8: 删除消息")
    if messages:
        last_msg_id = messages[-1]['id']
        success = await db_manager.delete_message(last_msg_id)
        if success:
            logger.info(f"✓ 成功删除消息: {last_msg_id[:8]}...")
        else:
            logger.error("✗ 删除消息失败")
            return False
    
    # 9. 再次获取消息总数
    logger.info("\n步骤 9: 再次获取消息总数")
    count = await db_manager.get_message_count()
    logger.info(f"✓ 删除后数据库中共有 {count} 条消息")
    
    # 10. 关闭数据库连接
    logger.info("\n步骤 10: 关闭数据库连接")
    success = await db_manager.close()
    if success:
        logger.info("✓ 数据库连接已关闭")
    else:
        logger.error("✗ 关闭数据库连接失败")
        return False
    
    logger.info("\n" + "="*50)
    logger.info("所有测试完成！✓")
    logger.info("="*50)
    
    return True


async def main():
    """主函数"""
    try:
        success = await test_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
