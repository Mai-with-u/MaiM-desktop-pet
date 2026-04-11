"""
消息格式转换工具
处理协议层与应用层之间的消息格式转换
"""

from typing import Dict, Any, Optional
from src.util.logger import logger

# 在模块级别导入 maim_message，避免每次调用都导入
try:
    from maim_message import MessageBase, BaseMessageInfo, Seg, UserInfo, FormatInfo
    MAIM_MESSAGE_AVAILABLE = True
except ImportError:
    logger.warning("maim_message 库未安装，消息转换功能将受限")
    MAIM_MESSAGE_AVAILABLE = False
    MessageBase = None
    BaseMessageInfo = None
    Seg = None
    UserInfo = None
    FormatInfo = None


def dict_to_message_base(message: Dict[str, Any]):
    """
    将字典格式的消息转换为 maim_message.MessageBase 对象

    Args:
        message: 消息字典，包含 message_info 和 message_segment

    Returns:
        maim_message.MessageBase 对象

    Raises:
        ImportError: 如果 maim_message 库未安装
        ValueError: 如果消息格式无效
    """
    if not MAIM_MESSAGE_AVAILABLE:
        raise ImportError("请安装 maim_message 库: pip install maim_message")

    # 验证输入
    if not message or not isinstance(message, dict):
        raise ValueError("message 参数必须是非空字典")

    try:
        # 提取消息信息
        message_info_data = message.get('message_info', {})
        message_segment_data = message.get('message_segment', {})

        if not message_info_data:
            raise ValueError("消息缺少 message_info 字段")

        # 构建 UserInfo
        user_info_data = message_info_data.get('user_info', {})
        user_info = UserInfo(
            platform=user_info_data.get('platform', 'desktop-pet'),
            user_id=user_info_data.get('user_id', '0'),
            user_nickname=user_info_data.get('user_nickname', ''),
            user_cardname=user_info_data.get('user_cardname', '')
        )

        # 构建 FormatInfo
        format_info_data = message_info_data.get('format_info', {})
        format_info = FormatInfo(
            content_format=format_info_data.get('content_format', ['text']),
            accept_format=format_info_data.get('accept_format', ['text'])
        )

        # 构建 BaseMessageInfo
        message_info = BaseMessageInfo(
            platform=message_info_data.get('platform', 'desktop-pet'),
            message_id=message_info_data.get('message_id', ''),
            time=message_info_data.get('time', 0),
            group_info=message_info_data.get('group_info'),
            user_info=user_info,
            format_info=format_info,
            additional_config=message_info_data.get('additional_config', {}),
            sender_info=message_info_data.get('sender_info'),
            receiver_info=message_info_data.get('receiver_info'),
            template_info=message_info_data.get('template_info')
        )

        # 构建 Seg
        msg_type = message_segment_data.get('type', 'text')
        seg_data = message_segment_data.get('data', '')

        # 处理 seglist 类型
        if msg_type == 'seglist':
            seg_list = []
            if isinstance(seg_data, list):
                for item in seg_data:
                    if item is None:
                        continue
                    if isinstance(item, dict):
                        sub_seg = Seg(
                            type=item.get('type', 'text'),
                            data=item.get('data', '')
                        )
                        seg_list.append(sub_seg)
                    elif isinstance(item, Seg):
                        seg_list.append(item)
            seg = Seg(type='seglist', data=seg_list)
        else:
            seg = Seg(
                type=msg_type,
                data=seg_data if isinstance(seg_data, str) else str(seg_data) if seg_data else ''
            )

        # 构建 MessageBase
        message_base = MessageBase(
            message_info=message_info,
            message_segment=seg,
            raw_message=message.get('raw_message', '')
        )

        logger.debug(f"字典 → MessageBase 转换成功")
        return message_base

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"字典 → MessageBase 转换失败: {e}", exc_info=True)
        raise ValueError(f"消息转换失败: {e}") from e


def message_base_to_dict(message_base) -> Dict[str, Any]:
    """
    将 maim_message.MessageBase 对象转换为字典格式

    Args:
        message_base: maim_message.MessageBase 对象

    Returns:
        消息字典

    Raises:
        ValueError: 如果 message_base 无效
    """
    if message_base is None:
        raise ValueError("message_base 参数不能为 None")

    try:
        # 提取 BaseMessageInfo
        message_info = getattr(message_base, 'message_info', None)
        if message_info is None:
            raise ValueError("message_base 缺少 message_info 属性")

        # 提取 UserInfo（使用 getattr 防止空值）
        user_info = getattr(message_info, 'user_info', None)
        user_info_dict = {}
        if user_info:
            user_info_dict = {
                'platform': getattr(user_info, 'platform', ''),
                'user_id': getattr(user_info, 'user_id', ''),
                'user_nickname': getattr(user_info, 'user_nickname', ''),
                'user_cardname': getattr(user_info, 'user_cardname', '')
            }

        # 提取 FormatInfo
        format_info = getattr(message_info, 'format_info', None)
        format_info_dict = {}
        if format_info:
            content_format = getattr(format_info, 'content_format', None)
            accept_format = getattr(format_info, 'accept_format', None)
            format_info_dict = {
                'content_format': list(content_format) if content_format else [],
                'accept_format': list(accept_format) if accept_format else []
            }

        # 提取 sender_info
        sender_info = getattr(message_info, 'sender_info', None)
        sender_info_dict = {}
        if sender_info:
            sender_info_dict = {
                'platform': getattr(sender_info, 'platform', ''),
                'user_id': getattr(sender_info, 'user_id', ''),
                'user_nickname': getattr(sender_info, 'user_nickname', ''),
                'user_cardname': getattr(sender_info, 'user_cardname', '')
            }

        # 提取 receiver_info
        receiver_info = getattr(message_info, 'receiver_info', None)
        receiver_info_dict = {}
        if receiver_info:
            receiver_info_dict = {
                'platform': getattr(receiver_info, 'platform', ''),
                'user_id': getattr(receiver_info, 'user_id', ''),
                'user_nickname': getattr(receiver_info, 'user_nickname', ''),
                'user_cardname': getattr(receiver_info, 'user_cardname', '')
            }

        # 提取 template_info
        template_info = getattr(message_info, 'template_info', None)
        template_info_dict = {}
        if template_info:
            template_info_dict = {
                'template_name': getattr(template_info, 'template_name', None),
                'template_data': getattr(template_info, 'template_data', None)
            }

        # 构建 message_info 字典
        message_info_dict = {
            'platform': getattr(message_info, 'platform', ''),
            'message_id': getattr(message_info, 'message_id', ''),
            'time': getattr(message_info, 'time', 0),
            'group_info': getattr(message_info, 'group_info', None),
            'user_info': user_info_dict,
            'format_info': format_info_dict,
            'additional_config': getattr(message_info, 'additional_config', {}),
            'sender_info': sender_info_dict,
            'receiver_info': receiver_info_dict,
            'template_info': template_info_dict
        }

        # 提取 MessageSegment
        message_segment = getattr(message_base, 'message_segment', None)
        message_segment_dict = {}
        if message_segment:
            message_segment_dict = {
                'type': getattr(message_segment, 'type', ''),
                'data': getattr(message_segment, 'data', '')
            }

        # 构建完整消息字典
        message_dict = {
            'message_info': message_info_dict,
            'message_segment': message_segment_dict,
            'raw_message': getattr(message_base, 'raw_message', '')
        }

        logger.debug(f"MessageBase → 字典转换成功")
        return message_dict

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"MessageBase → 字典转换失败: {e}", exc_info=True)
        raise ValueError(f"消息转换失败: {e}") from e


def convert_message_format(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换消息格式
    将 Maim 特有的消息格式（如 seglist）转换为统一格式

    Args:
        message: 原始消息

    Returns:
        转换后的消息
    """
    if not message or not isinstance(message, dict):
        logger.warning("无效的消息输入")
        return message

    try:
        message_segment = message.get('message_segment', {})

        if not message_segment:
            return message

        msg_type = message_segment.get('type', '')

        # 处理 seglist 类型
        if msg_type == 'seglist':
            seg_list = message_segment.get('data', [])

            if not isinstance(seg_list, list):
                logger.warning(f"seglist 数据格式错误")
                return message

            # 只提取文本片段
            text_parts = []
            for seg in seg_list:
                if seg is None:
                    continue
                if isinstance(seg, dict) and seg.get('type') == 'text':
                    text_content = str(seg.get('data', '') or '')
                    text_parts.append(text_content)
                elif hasattr(seg, 'type') and seg.type == 'text':
                    text_parts.append(str(seg.data or ''))

            # 将合并后的文本作为普通文本消息
            if text_parts:
                converted = {
                    'message_segment': {
                        'type': 'text',
                        'data': ''.join(text_parts)
                    }
                }

                # 保留原始消息的其他信息
                for key, value in message.items():
                    if key != 'message_segment':
                        converted[key] = value

                logger.debug(f"转换 seglist 为文本")
                return converted

        # 其他类型直接返回
        return message

    except Exception as e:
        logger.error(f"消息格式转换失败: {e}", exc_info=True)
        return message


def is_valid_message(message: Dict[str, Any]) -> bool:
    """
    检查消息格式是否有效

    Args:
        message: 消息字典

    Returns:
        是否有效
    """
    if not isinstance(message, dict):
        return False

    if 'message_segment' not in message:
        return False

    if 'message_info' not in message:
        return False

    # 验证 message_segment 结构
    segment = message.get('message_segment')
    if not isinstance(segment, dict):
        return False
    if 'type' not in segment or 'data' not in segment:
        return False

    # 验证 message_info 结构
    info = message.get('message_info')
    if not isinstance(info, dict):
        return False

    return True


def extract_text_content(message: Dict[str, Any]) -> str:
    """
    从消息中提取文本内容

    Args:
        message: 消息字典

    Returns:
        文本内容
    """
    if not message or not isinstance(message, dict):
        return ''

    try:
        message_segment = message.get('message_segment', {})
        if not message_segment:
            return ''

        msg_type = message_segment.get('type', '')
        data = message_segment.get('data', '')

        if msg_type == 'text':
            return str(data or '')
        elif msg_type == 'seglist':
            # 提取所有文本片段
            text_parts = []
            if isinstance(data, list):
                for seg in data:
                    if seg is None:
                        continue
                    if isinstance(seg, dict) and seg.get('type') == 'text':
                        text_parts.append(str(seg.get('data', '') or ''))
                    elif hasattr(seg, 'type') and seg.type == 'text':
                        text_parts.append(str(seg.data or ''))
            return ''.join(text_parts)
        else:
            return ''

    except Exception as e:
        logger.error(f"提取文本内容失败: {e}", exc_info=True)
        return ''
