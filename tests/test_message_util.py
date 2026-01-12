"""
测试消息格式转换工具
"""

from src.util.message_util import (
    dict_to_message_base,
    message_base_to_dict,
    convert_message_format,
    is_valid_message,
    extract_text_content
)


def test_dict_to_message_base():
    """测试字典 → MessageBase 转换"""
    print("测试 1: 字典 → MessageBase 转换")
    
    message_dict = {
        'message_info': {
            'platform': 'desktop-pet',
            'message_id': 'test-001',
            'time': 1234567890.0,
            'user_info': {
                'platform': 'desktop-pet',
                'user_id': 'user-001',
                'user_nickname': '测试用户',
                'user_cardname': '测试名片'
            },
            'format_info': {
                'content_format': ['text'],
                'accept_format': ['text']
            }
        },
        'message_segment': {
            'type': 'text',
            'data': '你好，这是一条测试消息'
        },
        'raw_message': '原始消息内容'
    }
    
    try:
        message_base = dict_to_message_base(message_dict)
        print(f"✅ 转换成功")
        print(f"   消息内容: {message_base.message_segment.data}")
        print(f"   用户昵称: {message_base.message_info.user_info.user_nickname}")
        return True
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_base_to_dict():
    """测试 MessageBase → 字典转换"""
    print("\n测试 2: MessageBase → 字典转换")
    
    message_dict = {
        'message_info': {
            'platform': 'desktop-pet',
            'message_id': 'test-002',
            'time': 1234567890.0,
            'user_info': {
                'platform': 'desktop-pet',
                'user_id': 'user-002',
                'user_nickname': '测试用户2',
                'user_cardname': '测试名片2'
            },
            'format_info': {
                'content_format': ['text'],
                'accept_format': ['text']
            }
        },
        'message_segment': {
            'type': 'text',
            'data': '这是另一条测试消息'
        }
    }
    
    try:
        # 先转换为 MessageBase
        message_base = dict_to_message_base(message_dict)
        
        # 再转换回字典
        result_dict = message_base_to_dict(message_base)
        
        print(f"✅ 转换成功")
        print(f"   消息内容: {result_dict['message_segment']['data']}")
        print(f"   用户昵称: {result_dict['message_info']['user_info']['user_nickname']}")
        return True
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convert_message_format():
    """测试 seglist → text 格式转换"""
    print("\n测试 3: seglist → text 格式转换")
    
    # 测试 seglist 格式
    seglist_message = {
        'message_info': {
            'platform': 'desktop-pet',
            'message_id': 'test-003'
        },
        'message_segment': {
            'type': 'seglist',
            'data': [
                {'type': 'text', 'data': '你好，'},
                {'type': 'emoji', 'data': '😊'},
                {'type': 'text', 'data': '这是一条包含多个片段的消息'}
            ]
        }
    }
    
    try:
        converted = convert_message_format(seglist_message)
        print(f"✅ 转换成功")
        print(f"   原始类型: seglist")
        print(f"   转换后类型: {converted['message_segment']['type']}")
        print(f"   转换后内容: {converted['message_segment']['data']}")
        return True
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_is_valid_message():
    """测试消息验证"""
    print("\n测试 4: 消息验证")
    
    # 有效消息
    valid_message = {
        'message_info': {'platform': 'desktop-pet'},
        'message_segment': {'type': 'text', 'data': 'test'}
    }
    
    # 无效消息（缺少 message_info）
    invalid_message1 = {
        'message_segment': {'type': 'text', 'data': 'test'}
    }
    
    # 无效消息（缺少 message_segment）
    invalid_message2 = {
        'message_info': {'platform': 'desktop-pet'}
    }
    
    result1 = is_valid_message(valid_message)
    result2 = is_valid_message(invalid_message1)
    result3 = is_valid_message(invalid_message2)
    
    print(f"✅ 有效消息验证: {result1}")
    print(f"   无效消息1（缺少 message_info）: {not result2}")
    print(f"   无效消息2（缺少 message_segment）: {not result3}")
    
    return result1 and not result2 and not result3


def test_extract_text_content():
    """测试文本内容提取"""
    print("\n测试 5: 文本内容提取")
    
    # 测试纯文本消息
    text_message = {
        'message_segment': {
            'type': 'text',
            'data': '这是一条纯文本消息'
        }
    }
    
    # 测试 seglist 消息
    seglist_message = {
        'message_segment': {
            'type': 'seglist',
            'data': [
                {'type': 'text', 'data': '片段1'},
                {'type': 'emoji', 'data': '😊'},
                {'type': 'text', 'data': '片段2'}
            ]
        }
    }
    
    text1 = extract_text_content(text_message)
    text2 = extract_text_content(seglist_message)
    
    print(f"✅ 纯文本提取: {text1}")
    print(f"   seglist 提取: {text2}")
    
    expected1 = '这是一条纯文本消息'
    expected2 = '片段1片段2'
    
    result1 = (text1 == expected1)
    result2 = (text2 == expected2)
    
    print(f"   纯文本验证: {result1}")
    print(f"   seglist 验证: {result2}")
    
    return result1 and result2


def test_round_trip():
    """测试双向转换（字典 → MessageBase → 字典）"""
    print("\n测试 6: 双向转换")
    
    original_message = {
        'message_info': {
            'platform': 'desktop-pet',
            'message_id': 'test-roundtrip',
            'time': 1234567890.0,
            'user_info': {
                'platform': 'desktop-pet',
                'user_id': 'user-rt',
                'user_nickname': '往返测试',
                'user_cardname': '测试用户'
            },
            'format_info': {
                'content_format': ['text'],
                'accept_format': ['text']
            }
        },
        'message_segment': {
            'type': 'text',
            'data': '这是往返转换测试消息'
        },
        'raw_message': '原始消息'
    }
    
    try:
        # 字典 → MessageBase
        message_base = dict_to_message_base(original_message)
        
        # MessageBase → 字典
        converted_message = message_base_to_dict(message_base)
        
        # 验证关键信息
        success = True
        
        # 检查消息内容
        if converted_message['message_segment']['data'] != original_message['message_segment']['data']:
            print(f"❌ 消息内容不匹配")
            success = False
        
        # 检查用户信息
        if converted_message['message_info']['user_info']['user_nickname'] != original_message['message_info']['user_info']['user_nickname']:
            print(f"❌ 用户信息不匹配")
            success = False
        
        # 检查平台
        if converted_message['message_info']['platform'] != original_message['message_info']['platform']:
            print(f"❌ 平台信息不匹配")
            success = False
        
        if success:
            print(f"✅ 双向转换成功")
            print(f"   消息内容一致")
            print(f"   用户信息一致")
            print(f"   平台信息一致")
        
        return success
    except Exception as e:
        print(f"❌ 双向转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("消息格式转换工具测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("字典 → MessageBase", test_dict_to_message_base()))
    results.append(("MessageBase → 字典", test_message_base_to_dict()))
    results.append(("seglist → text 转换", test_convert_message_format()))
    results.append(("消息验证", test_is_valid_message()))
    results.append(("文本内容提取", test_extract_text_content()))
    results.append(("双向转换", test_round_trip()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    # 统计
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  {total - passed} 个测试失败")
