"""
测试标准消息类更新 (v2.0.0 - maim_message v0.6.1+)
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.models.message import (
    MessageBase, UserInfo, Seg, BaseMessageInfo, FormatInfo,
    GroupInfo, TemplateInfo, SenderInfo, ReceiverInfo
)


def test_basic_message_creation():
    """测试基本消息创建"""
    print("测试 1: 基本消息创建...")
    
    # 创建发送消息
    message = MessageBase.create_sent_message("你好，世界！")
    assert message.message_content == "你好，世界！"
    assert message.user_id == "0"
    assert message.platform == "desktop-pet"
    print("✅ 发送消息创建成功")
    
    # 创建接收消息
    message2 = MessageBase.create_received_message("收到消息", user_nickname="用户")
    assert message2.message_content == "收到消息"
    assert message2.user_id == "1"
    assert message2.user_nickname == "用户"
    print("✅ 接收消息创建成功")


def test_serialization():
    """测试序列化和反序列化"""
    print("\n测试 2: 序列化和反序列化...")
    
    message = MessageBase.create_text_message(
        text="测试消息",
        platform="test-platform",
        user_id="12345",
        user_nickname="测试用户",
        msg_type="text"
    )
    
    # 序列化
    message_dict = message.to_dict()
    assert 'message_info' in message_dict
    assert 'message_segment' in message_dict
    assert message_dict['message_segment']['data'] == "测试消息"
    print("✅ 序列化成功")
    
    # 反序列化
    message2 = MessageBase.from_dict(message_dict)
    assert message2.message_content == message.message_content
    assert message2.message_id == message.message_id
    assert message2.user_nickname == message.user_nickname
    print("✅ 反序列化成功")


def test_new_classes():
    """测试新增的类"""
    print("\n测试 3: 新增类...")
    
    # GroupInfo
    group_info = GroupInfo(
        group_id="group_123",
        group_name="测试群组"
    )
    assert group_info.group_id == "group_123"
    assert group_info.group_name == "测试群组"
    print("✅ GroupInfo 创建成功")
    
    # TemplateInfo
    template_info = TemplateInfo(
        template_id="template_456",
        template_name="测试模板",
        template_data={"key": "value"}
    )
    assert template_info.template_id == "template_456"
    assert template_info.template_name == "测试模板"
    print("✅ TemplateInfo 创建成功")
    
    # SenderInfo
    sender_info = SenderInfo(
        platform="qq",
        user_id="sender_789",
        user_nickname="发送者",
        user_cardname="发送者名片"
    )
    assert sender_info.platform == "qq"
    assert sender_info.user_id == "sender_789"
    print("✅ SenderInfo 创建成功")
    
    # ReceiverInfo
    receiver_info = ReceiverInfo(
        platform="wechat",
        user_id="receiver_101",
        user_nickname="接收者",
        user_cardname="接收者名片"
    )
    assert receiver_info.platform == "wechat"
    assert receiver_info.user_id == "receiver_101"
    print("✅ ReceiverInfo 创建成功")


def test_message_with_new_fields():
    """测试包含新增字段的消息"""
    print("\n测试 4: 包含新增字段的消息...")
    
    user_info = UserInfo(
        platform="test",
        user_id="123",
        user_nickname="测试用户"
    )
    
    format_info = FormatInfo()
    
    group_info = GroupInfo(
        group_id="group_001",
        group_name="测试群"
    )
    
    template_info = TemplateInfo(
        template_id="tpl_001",
        template_name="问候模板"
    )
    
    sender_info = SenderInfo(
        platform="qq",
        user_id="sender_001",
        user_nickname="发送者"
    )
    
    receiver_info = ReceiverInfo(
        platform="wechat",
        user_id="receiver_001",
        user_nickname="接收者"
    )
    
    message_info = BaseMessageInfo(
        platform="test",
        message_id="msg_001",
        time=1000000.0,
        user_info=user_info,
        format_info=format_info,
        group_info=group_info,
        template_info=template_info,
        sender_info=sender_info,
        receiver_info=receiver_info,
        additional_config={}
    )
    
    message_segment = Seg(type="text", data="完整测试消息")
    
    message = MessageBase(
        message_info=message_info,
        message_segment=message_segment,
        raw_message="完整测试消息"
    )
    
    # 验证新字段
    assert message.message_info.group_info.group_id == "group_001"
    assert message.message_info.template_info.template_id == "tpl_001"
    assert message.message_info.sender_info.user_id == "sender_001"
    assert message.message_info.receiver_info.user_id == "receiver_001"
    print("✅ 包含新增字段的消息创建成功")
    
    # 测试序列化
    message_dict = message.to_dict()
    assert 'group_info' in message_dict['message_info']
    assert 'template_info' in message_dict['message_info']
    assert 'sender_info' in message_dict['message_info']
    assert 'receiver_info' in message_dict['message_info']
    print("✅ 新增字段序列化成功")
    
    # 测试反序列化
    message2 = MessageBase.from_dict(message_dict)
    assert message2.message_info.group_info.group_id == "group_001"
    assert message2.message_info.template_info.template_id == "tpl_001"
    print("✅ 新增字段反序列化成功")


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n测试 5: 向后兼容性...")
    
    # 创建旧版本格式的消息（不含新字段）
    old_message_dict = {
        'message_info': {
            'platform': 'desktop-pet',
            'message_id': 'old_msg_001',
            'time': 1000000.0,
            'user_info': {
                'platform': 'desktop-pet',
                'user_id': '0',
                'user_nickname': '旧版本用户',
                'user_cardname': '旧版本用户'
            },
            'format_info': {
                'content_format': ['text', 'image', 'emoji'],
                'accept_format': ['text', 'image', 'emoji']
            },
            'group_info': None,
            'additional_config': {}
        },
        'message_segment': {
            'type': 'text',
            'data': '旧版本消息'
        },
        'raw_message': '旧版本消息'
    }
    
    # 反序列化
    message = MessageBase.from_dict(old_message_dict)
    assert message.message_content == "旧版本消息"
    assert message.message_info.group_info is None
    assert message.message_info.template_info is None
    assert message.message_info.sender_info is None
    assert message.message_info.receiver_info is None
    print("✅ 旧版本消息兼容性测试通过")


def test_maim_message_compatibility():
    """测试与 maim_message 库的兼容性"""
    print("\n测试 6: maim_message 库兼容性...")
    
    try:
        from maim_message import (
            MessageBase as MaimMessageBase,
            UserInfo as MaimUserInfo,
            Seg as MaimSeg,
            BaseMessageInfo as MaimBaseMessageInfo,
            FormatInfo as MaimFormatInfo
        )
        
        # 使用 maim_message 创建消息
        maim_user_info = MaimUserInfo(
            platform="test",
            user_id="test_001",
            user_nickname="Maim用户"
        )
        
        maim_format_info = MaimFormatInfo()
        
        maim_message_info = MaimBaseMessageInfo(
            platform="test",
            message_id="maim_001",
            time=1000000.0,
            user_info=maim_user_info,
            format_info=maim_format_info
        )
        
        maim_seg = MaimSeg(type="text", data="Maim消息")
        
        maim_message = MaimMessageBase(
            message_info=maim_message_info,
            message_segment=maim_seg,
            raw_message="Maim消息"
        )
        
        # 序列化
        maim_dict = maim_message.to_dict()
        
        # 使用我们的类反序列化
        our_message = MessageBase.from_dict(maim_dict)
        
        assert our_message.message_content == "Maim消息"
        assert our_message.platform == "test"
        print("✅ maim_message 库兼容性测试通过")
        
    except ImportError as e:
        print(f"⚠️  跳过 maim_message 库测试（未安装）: {e}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("标准消息类更新测试 (v2.0.0 - maim_message v0.6.1+)")
    print("=" * 60)
    
    try:
        test_basic_message_creation()
        test_serialization()
        test_new_classes()
        test_message_with_new_fields()
        test_backward_compatibility()
        test_maim_message_compatibility()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
