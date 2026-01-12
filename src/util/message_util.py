"""
消息格式转换工具
处理协议层与应用层之间的消息格式转换
"""

from typing import Dict, Any
from src.util.logger import logger


def dict_to_message_base(message: Dict[str, Any]):
    """
    将字典格式的消息转换为 maim_message.MessageBase 对象
    
    Args:
        message: 消息字典，包含 message_info 和 message_segment
    
    Returns:
        maim_message.MessageBase 对象
    
    Raises:
        ImportError: 如果 maim_message 库未安装
        KeyError: 如果缺少必要的字段
    """
    try:
        from maim_message import MessageBase, BaseMessageInfo, Seg, UserInfo, FormatInfo
    except ImportError as e:
        logger.error("maim_message 库未安装，无法转换消息格式")
        raise ImportError("请安装 maim_message 库: pip install maim_message") from e
    
    try:
        # 提取消息信息
        message_info_data = message.get('message_info', {})
        message_segment_data = message.get('message_segment', {})
        
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
        
        # 构建 BaseMessageInfo (注意：使用 BaseMessageInfo 而不是 MessageInfo)
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
        seg = Seg(
            type=message_segment_data.get('type', 'text'),
            data=message_segment_data.get('data', '')
        )
        
        # 构建 MessageBase
        message_base = MessageBase(
            message_info=message_info,
            message_segment=seg,
            raw_message=message.get('raw_message', '')
        )
        
        logger.debug(f"字典 → MessageBase 转换成功: {message_segment_data.get('data', '')[:50]}...")
        return message_base
        
    except Exception as e:
        logger.error(f"字典 → MessageBase 转换失败: {e}", exc_info=True)
        raise


def message_base_to_dict(message_base) -> Dict[str, Any]:
    """
    将 maim_message.MessageBase 对象转换为字典格式
    
    Args:
        message_base: maim_message.MessageBase 对象
    
    Returns:
        消息字典
    """
    try:
        # 提取 BaseMessageInfo (注意：是 BaseMessageInfo)
        message_info = message_base.message_info
        
        # 提取 UserInfo
        user_info = message_info.user_info
        user_info_dict = {
            'platform': user_info.platform,
            'user_id': user_info.user_id,
            'user_nickname': user_info.user_nickname,
            'user_cardname': user_info.user_cardname
        } if user_info else {}
        
        # 提取 FormatInfo
        format_info = message_info.format_info
        format_info_dict = {
            'content_format': list(format_info.content_format) if format_info.content_format else [],
            'accept_format': list(format_info.accept_format) if format_info.accept_format else []
        } if format_info else {}
        
        # 提取 sender_info
        sender_info = message_info.sender_info
        sender_info_dict = {
            'platform': sender_info.platform,
            'user_id': sender_info.user_id,
            'user_nickname': sender_info.user_nickname,
            'user_cardname': sender_info.user_cardname
        } if sender_info else {}
        
        # 提取 receiver_info
        receiver_info = message_info.receiver_info
        receiver_info_dict = {
            'platform': receiver_info.platform,
            'user_id': receiver_info.user_id,
            'user_nickname': receiver_info.user_nickname,
            'user_cardname': receiver_info.user_cardname
        } if receiver_info else {}
        
        # 提取 template_info
        template_info = message_info.template_info
        template_info_dict = {
            'template_name': template_info.template_name if template_info else None,
            'template_data': template_info.template_data if template_info else None
        } if template_info else {}
        
        # 构建 message_info 字典
        message_info_dict = {
            'platform': message_info.platform,
            'message_id': message_info.message_id,
            'time': message_info.time,
            'group_info': message_info.group_info,
            'user_info': user_info_dict,
            'format_info': format_info_dict,
            'additional_config': message_info.additional_config,
            'sender_info': sender_info_dict,
            'receiver_info': receiver_info_dict,
            'template_info': template_info_dict
        }
        
        # 提取 MessageSegment
        message_segment = message_base.message_segment
        message_segment_dict = {
            'type': message_segment.type,
            'data': message_segment.data
        }
        
        # 构建完整消息字典
        message_dict = {
            'message_info': message_info_dict,
            'message_segment': message_segment_dict,
            'raw_message': message_base.raw_message
        }
        
        logger.debug(f"MessageBase → 字典转换成功: {message_segment_dict.get('data', '')[:50]}...")
        return message_dict
        
    except Exception as e:
        logger.error(f"MessageBase → 字典转换失败: {e}", exc_info=True)
        raise


def convert_message_format(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换消息格式
    将 Maim 特有的消息格式（如 seglist）转换为统一格式
    
    Args:
        message: 原始消息
    
    Returns:
        转换后的消息
    """
    try:
        message_segment = message.get('message_segment', {})
        
        if not message_segment:
            return message
        
        msg_type = message_segment.get('type', '')
        
        # 处理 seglist 类型
        if msg_type == 'seglist':
            # 将 seglist 转换为多个独立的消息
            seg_list = message_segment.get('data', [])
            
            if not isinstance(seg_list, list):
                logger.warning(f"seglist 数据格式错误: {seg_list}")
                return message
            
            # 只提取文本片段
            text_parts = []
            for seg in seg_list:
                if seg.get('type') == 'text':
                    text_content = str(seg.get('data', ''))
                    text_parts.append(text_content)
            
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
                
                logger.debug(f"转换 seglist 为文本: {converted['message_segment']['data'][:50]}...")
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
    
    return True


def extract_text_content(message: Dict[str, Any]) -> str:
    """
    从消息中提取文本内容
    
    Args:
        message: 消息字典
    
    Returns:
        文本内容
    """
    try:
        message_segment = message.get('message_segment', {})
        msg_type = message_segment.get('type', '')
        data = message_segment.get('data', '')
        
        if msg_type == 'text':
            return str(data)
        elif msg_type == 'seglist':
            # 提取所有文本片段
            text_parts = []
            if isinstance(data, list):
                for seg in data:
                    if seg.get('type') == 'text':
                        text_parts.append(str(seg.get('data', '')))
            return ''.join(text_parts)
        else:
            return ''
        
    except Exception as e:
        logger.error(f"提取文本内容失败: {e}", exc_info=True)
        return ''
