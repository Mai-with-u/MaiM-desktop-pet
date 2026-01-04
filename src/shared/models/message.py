"""
标准消息类定义
兼容 maim_message 库的消息结构 (v0.6.1+)
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import time
import uuid


@dataclass
class UserInfo:
    """用户信息"""
    platform: str
    user_id: str
    user_nickname: str = ""
    user_cardname: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class GroupInfo:
    """群组信息"""
    group_id: str = ""
    group_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class FormatInfo:
    """格式信息"""
    content_format: List[str] = field(default_factory=lambda: ["text", "image", "emoji"])
    accept_format: List[str] = field(default_factory=lambda: ["text", "image", "emoji"])
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class TemplateInfo:
    """模板信息"""
    template_id: str = ""
    template_name: str = ""
    template_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class SenderInfo:
    """发送者信息类"""
    platform: str = ""
    user_id: str = ""
    user_nickname: str = ""
    user_cardname: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ReceiverInfo:
    """接收者信息类"""
    platform: str = ""
    user_id: str = ""
    user_nickname: str = ""
    user_cardname: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class BaseMessageInfo:
    """基础消息信息"""
    platform: str
    message_id: str
    time: float
    user_info: UserInfo
    format_info: FormatInfo
    group_info: Optional[GroupInfo] = None
    template_info: Optional[TemplateInfo] = None
    sender_info: Optional[SenderInfo] = None
    receiver_info: Optional[ReceiverInfo] = None
    additional_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 将嵌套对象也转换为字典
        if self.user_info:
            data['user_info'] = self.user_info.to_dict()
        if self.format_info:
            data['format_info'] = self.format_info.to_dict()
        if self.group_info:
            data['group_info'] = self.group_info.to_dict()
        if self.template_info:
            data['template_info'] = self.template_info.to_dict()
        if self.sender_info:
            data['sender_info'] = self.sender_info.to_dict()
        if self.receiver_info:
            data['receiver_info'] = self.receiver_info.to_dict()
        return data


@dataclass
class Seg:
    """消息段"""
    type: str
    data: Any
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class MessageBase:
    """消息基类 - 兼容 maim_message 的 MessageBase"""
    message_info: BaseMessageInfo
    message_segment: Seg
    raw_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 将嵌套对象也转换为字典
        if self.message_info:
            data['message_info'] = self.message_info.to_dict()
        if self.message_segment:
            data['message_segment'] = self.message_segment.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageBase':
        """从字典创建消息对象"""
        # 解析 message_info
        message_info_dict = data.get('message_info', {})
        user_info_dict = message_info_dict.get('user_info', {})
        format_info_dict = message_info_dict.get('format_info', {})
        group_info_dict = message_info_dict.get('group_info', {})
        template_info_dict = message_info_dict.get('template_info', {})
        sender_info_dict = message_info_dict.get('sender_info', {})
        receiver_info_dict = message_info_dict.get('receiver_info', {})
        
        user_info = UserInfo(
            platform=user_info_dict.get('platform', ''),
            user_id=user_info_dict.get('user_id', ''),
            user_nickname=user_info_dict.get('user_nickname', ''),
            user_cardname=user_info_dict.get('user_cardname', ''),
        )
        
        format_info = FormatInfo(
            content_format=format_info_dict.get('content_format', ['text', 'image', 'emoji']),
            accept_format=format_info_dict.get('accept_format', ['text', 'image', 'emoji']),
        )
        
        group_info = None
        if group_info_dict:
            group_info = GroupInfo(
                group_id=group_info_dict.get('group_id', ''),
                group_name=group_info_dict.get('group_name', ''),
            )
        
        template_info = None
        if template_info_dict:
            template_info = TemplateInfo(
                template_id=template_info_dict.get('template_id', ''),
                template_name=template_info_dict.get('template_name', ''),
                template_data=template_info_dict.get('template_data', {}),
            )
        
        sender_info = None
        if sender_info_dict:
            sender_info = SenderInfo(
                platform=sender_info_dict.get('platform', ''),
                user_id=sender_info_dict.get('user_id', ''),
                user_nickname=sender_info_dict.get('user_nickname', ''),
                user_cardname=sender_info_dict.get('user_cardname', ''),
            )
        
        receiver_info = None
        if receiver_info_dict:
            receiver_info = ReceiverInfo(
                platform=receiver_info_dict.get('platform', ''),
                user_id=receiver_info_dict.get('user_id', ''),
                user_nickname=receiver_info_dict.get('user_nickname', ''),
                user_cardname=receiver_info_dict.get('user_cardname', ''),
            )
        
        message_info = BaseMessageInfo(
            platform=message_info_dict.get('platform', ''),
            message_id=message_info_dict.get('message_id', ''),
            time=message_info_dict.get('time', time.time()),
            user_info=user_info,
            format_info=format_info,
            group_info=group_info,
            template_info=template_info,
            sender_info=sender_info,
            receiver_info=receiver_info,
            additional_config=message_info_dict.get('additional_config', {}),
        )
        
        # 解析 message_segment
        segment_dict = data.get('message_segment', {})
        message_segment = Seg(
            type=segment_dict.get('type', 'text'),
            data=segment_dict.get('data', ''),
        )
        
        return cls(
            message_info=message_info,
            message_segment=message_segment,
            raw_message=data.get('raw_message', ''),
        )
    
    @classmethod
    def create_text_message(cls, 
                           text: str, 
                           platform: str = "desktop-pet",
                           user_id: str = "0",
                           user_nickname: str = "",
                           msg_type: str = "text") -> 'MessageBase':
        """创建文本消息的便捷方法
        
        参数:
            text: 消息文本
            platform: 平台类型
            user_id: 用户ID
            user_nickname: 用户昵称
            msg_type: 消息类型（text/image/emoji）
        
        返回:
            MessageBase: 消息对象
        """
        user_info = UserInfo(
            platform=platform,
            user_id=user_id,
            user_nickname=user_nickname,
            user_cardname=user_nickname,
        )
        
        format_info = FormatInfo()
        
        message_info = BaseMessageInfo(
            platform=platform,
            message_id=str(uuid.uuid4()),
            time=time.time(),
            user_info=user_info,
            format_info=format_info,
            additional_config={},
        )
        
        message_segment = Seg(
            type=msg_type,
            data=text,
        )
        
        return cls(
            message_info=message_info,
            message_segment=message_segment,
            raw_message=text,
        )
    
    @classmethod
    def create_received_message(cls, text: str, user_nickname: str = "用户") -> 'MessageBase':
        """创建接收消息的便捷方法"""
        return cls.create_text_message(
            text=text,
            platform="desktop-pet",
            user_id="1",
            user_nickname=user_nickname,
            msg_type="text",
        )
    
    @classmethod
    def create_sent_message(cls, text: str, user_nickname: str = "桌面宠物") -> 'MessageBase':
        """创建发送消息的便捷方法"""
        return cls.create_text_message(
            text=text,
            platform="desktop-pet",
            user_id="0",
            user_nickname=user_nickname,
            msg_type="text",
        )
    
    @property
    def message_type(self) -> str:
        """获取消息类型"""
        return self.message_segment.type
    
    @property
    def message_content(self) -> Any:
        """获取消息内容"""
        return self.message_segment.data
    
    @property
    def platform(self) -> str:
        """获取平台类型"""
        return self.message_info.platform
    
    @property
    def message_id(self) -> str:
        """获取消息ID"""
        return self.message_info.message_id
    
    @property
    def timestamp(self) -> float:
        """获取时间戳"""
        return self.message_info.time
    
    @property
    def user_id(self) -> str:
        """获取用户ID"""
        return self.message_info.user_info.user_id
    
    @property
    def user_nickname(self) -> str:
        """获取用户昵称"""
        return self.message_info.user_info.user_nickname
