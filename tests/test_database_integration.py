"""
数据库集成测试 - 测试消息存储功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db_manager


async def test_database_integration():
    """测试数据库集成功能"""
    print("\n" + "="*60)
    print("数据库集成测试")
    print("="*60)
    
    # 使用测试数据库路径
    test_db_path = "data/test_integration.db"
    
    try:
        # 测试 1: 数据库初始化
        print("\n[测试 1] 数据库初始化")
        print("-" * 60)
        
        success = await db_manager.initialize(
            db_type='sqlite',
            path=test_db_path
        )
        
        if success:
            print("✓ 数据库初始化成功")
        else:
            print("✗ 数据库初始化失败")
            return False
        
        # 检查数据库是否已初始化
        if db_manager.is_initialized():
            print("✓ 数据库状态检查通过")
        else:
            print("✗ 数据库状态检查失败")
            return False
        
        # 测试 2: 保存接收消息
        print("\n[测试 2] 保存接收消息")
        print("-" * 60)
        
        received_message = {
            'message_info': {
                'platform': 'test-platform',
                'message_id': 'test-received-msg-001',
                'time': 1704661200.0,
                'group_info': None,
                'user_info': {
                    'platform': 'test-platform',
                    'user_id': 'test-user-001',
                    'user_nickname': '测试用户',
                    'user_cardname': '测试名片'
                },
                'format_info': {
                    'content_format': ['text'],
                    'accept_format': ['text']
                },
                'additional_config': {}
            },
            'message_segment': {
                'type': 'text',
                'data': '这是一条测试接收消息'
            },
            'raw_message': '这是一条测试接收消息'
        }
        
        save_success = await db_manager.save_message(received_message)
        
        if save_success:
            print("✓ 接收消息保存成功")
        else:
            print("✗ 接收消息保存失败")
            return False
        
        # 测试 3: 保存发送消息
        print("\n[测试 3] 保存发送消息")
        print("-" * 60)
        
        sent_message = {
            'message_info': {
                'platform': 'desktop-pet',
                'message_id': 'test-sent-msg-001',
                'time': 1704661201.0,
                'group_info': None,
                'user_info': {
                    'platform': 'desktop-pet',
                    'user_id': '0',
                    'user_nickname': '桌面宠物',
                    'user_cardname': '桌面宠物'
                },
                'format_info': {
                    'content_format': ['text'],
                    'accept_format': ['text']
                },
                'additional_config': {}
            },
            'message_segment': {
                'type': 'text',
                'data': '这是一条测试发送消息'
            },
            'raw_message': '这是一条测试发送消息'
        }
        
        save_success = await db_manager.save_message(sent_message)
        
        if save_success:
            print("✓ 发送消息保存成功")
        else:
            print("✗ 发送消息保存失败")
            return False
        
        # 测试 4: 查询消息
        print("\n[测试 4] 查询消息")
        print("-" * 60)
        
        messages = await db_manager.get_messages(limit=10)
        
        if len(messages) >= 2:
            print(f"✓ 成功查询到 {len(messages)} 条消息")
            for msg in messages:
                print(f"  - ID: {msg['id']}, 用户: {msg['user_nickname']}, 内容: {msg['raw_message'][:30]}...")
        else:
            print(f"✗ 查询到的消息数量不足: {len(messages)}")
            return False
        
        # 测试 5: 获取消息总数
        print("\n[测试 5] 获取消息总数")
        print("-" * 60)
        
        count = await db_manager.get_message_count()
        
        if count >= 2:
            print(f"✓ 消息总数: {count}")
        else:
            print(f"✗ 消息总数不正确: {count}")
            return False
        
        # 测试 6: 根据ID获取单条消息
        print("\n[测试 6] 根据ID获取单条消息")
        print("-" * 60)
        
        message = await db_manager.get_message_by_id('test-received-msg-001')
        
        if message:
            print(f"✓ 成功获取消息: {message['raw_message']}")
        else:
            print("✗ 未找到指定消息")
            return False
        
        # 测试 7: 搜索消息
        print("\n[测试 7] 搜索消息")
        print("-" * 60)
        
        search_results = await db_manager.search_messages('测试', limit=10)
        
        if len(search_results) >= 2:
            print(f"✓ 搜索到 {len(search_results)} 条包含'测试'的消息")
        else:
            print(f"✗ 搜索结果不足: {len(search_results)}")
            return False
        
        # 测试 8: 删除消息
        print("\n[测试 8] 删除消息")
        print("-" * 60)
        
        delete_success = await db_manager.delete_message('test-received-msg-001')
        
        if delete_success:
            print("✓ 消息删除成功")
            
            # 验证删除
            deleted_message = await db_manager.get_message_by_id('test-received-msg-001')
            if deleted_message is None:
                print("✓ 删除验证通过")
            else:
                print("✗ 删除验证失败：消息仍然存在")
                return False
        else:
            print("✗ 消息删除失败")
            return False
        
        # 测试 9: 清空所有消息
        print("\n[测试 9] 清空所有消息")
        print("-" * 60)
        
        clear_success = await db_manager.clear_all_messages()
        
        if clear_success:
            print("✓ 消息清空成功")
            
            # 验证清空
            count_after_clear = await db_manager.get_message_count()
            if count_after_clear == 0:
                print("✓ 清空验证通过")
            else:
                print(f"✗ 清空验证失败：仍有 {count_after_clear} 条消息")
                return False
        else:
            print("✗ 消息清空失败")
            return False
        
        # 测试 10: 关闭数据库
        print("\n[测试 10] 关闭数据库")
        print("-" * 60)
        
        close_success = await db_manager.close()
        
        if close_success:
            print("✓ 数据库关闭成功")
            
            if not db_manager.is_initialized():
                print("✓ 数据库状态验证通过")
            else:
                print("✗ 数据库状态验证失败")
                return False
        else:
            print("✗ 数据库关闭失败")
            return False
        
        # 所有测试通过
        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(test_database_integration())
    
    # 根据测试结果退出
    sys.exit(0 if result else 1)
