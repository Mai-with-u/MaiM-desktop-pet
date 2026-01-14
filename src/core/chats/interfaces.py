"""
聊天层接口定义
定义所有聊天实现必须实现的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union


class IChat(ABC):
    """聊天接口 - 定义所有聊天实现的通用行为"""
    
    @abstractmethod
    async def send(
        self,
        text: str,
        msg_type: str = "text",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """
        发送消息
        
        Args:
            text: 消息内容
            msg_type: 消息类型（默认为 "text"）
            user_id: 用户ID
            user_nickname: 用户昵称
            user_cardname: 用户群名片
            additional_config: 附加配置
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def send_text(self, text: str) -> bool:
        """
        发送文本消息
        
        Args:
            text: 文本内容
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def send_image(self, image_data: str) -> bool:
        """
        发送图片消息
        
        Args:
            image_data: 图片数据（URL或base64等）
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def send_emoji(self, emoji: str) -> bool:
        """
        发送表情消息
        
        Args:
            emoji: 表情内容（base64编码）
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def send_seglist(
        self,
        segments: List[Union[Any, tuple]],
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """
        发送复合消息
        
        Args:
            segments: 消息段列表（具体类型由实现决定）
            user_id: 用户ID
            user_nickname: 用户昵称
            user_cardname: 用户群名片
            additional_config: 附加配置
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def send_text_and_image(
        self,
        text: str,
        image_data: str,
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """
        发送文本+图片的复合消息（便捷方法）
        
        Args:
            text: 文本内容
            image_data: 图片数据
            user_id: 用户ID
            user_nickname: 用户昵称
            user_cardname: 用户群名片
            additional_config: 附加配置
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def send_pixmap_with_text(
        self,
        pixmap,
        text: str = "",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """
        发送 QPixmap 图片（带可选文本）
        
        Args:
            pixmap: PyQt5.QtGui.QPixmap 对象
            text: 可选的文本说明
            user_id: 用户ID
            user_nickname: 用户昵称
            user_cardname: 用户群名片
            additional_config: 附加配置
        
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取聊天实现名称"""
        pass
    
    @abstractmethod
    def is_supported_message_type(self, msg_type: str) -> bool:
        """
        检查是否支持指定的消息类型
        
        Args:
            msg_type: 消息类型
        
        Returns:
            是否支持
        """
        pass
    
    @abstractmethod
    def get_supported_message_types(self) -> List[str]:
        """获取支持的消息类型列表"""
        pass
