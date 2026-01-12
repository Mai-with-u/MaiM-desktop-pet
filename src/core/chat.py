"""
聊天模块 - 处理消息发送和创建
"""

from maim_message import UserInfo, Seg, MessageBase, BaseMessageInfo, FormatInfo
from typing import Optional
import time
import uuid

from config import load_config
from src.core.protocol_manager import protocol_manager

# 加载配置
config = load_config()
from src.util.logger import logger
from src.database import db_manager


class Chat:
    """聊天工具类 - 负责创建和发送消息"""
    
    def __init__(self):
        """初始化聊天工具"""
        self.format_info = FormatInfo(
            # 消息内容中包含的Seg的type列表
            content_format=["text", "image", "emoji"],
            # 消息发出后，期望最终的消息中包含的消息类型
            accept_format=["text", "image", "emoji"],
        )
        self.default_user_id = "0"
        
        # 获取默认昵称，确保不为空
        default_nick = getattr(config, 'userNickname', '')
        self.default_sender_nickname = default_nick if default_nick else getattr(config, 'Nickname', '桌面宠物')
    
    def _create_user_info(
        self,
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None
    ) -> UserInfo:
        """创建用户信息
        
        参数:
            user_id: 用户ID（默认使用配置的ID）
            user_nickname: 用户昵称（默认使用配置的昵称）
            user_cardname: 用户群名片（默认使用昵称）
        
        返回:
            UserInfo: 用户信息对象
        """
        # 确保 platform 不为空
        platform = getattr(config, 'platform', 'desktop-pet')
        
        # 确保 user_id 不为空
        uid = user_id or self.default_user_id
        
        # 确保 user_nickname 不为空
        nickname = user_nickname if user_nickname else self.default_sender_nickname
        
        # 确保 user_cardname 不为空
        cardname = user_cardname if user_cardname else nickname
        
        return UserInfo(
            platform=platform,
            user_id=uid,
            user_nickname=nickname,
            user_cardname=cardname,
        )
    
    def _create_message_info(
        self,
        user_info: UserInfo,
        additional_config: Optional[dict] = None
    ) -> BaseMessageInfo:
        """创建消息信息
        
        参数:
            user_info: 用户信息
            additional_config: 附加配置
        
        返回:
            BaseMessageInfo: 消息信息对象
        """
        config_dict = additional_config or {}
        config_dict.setdefault("maimcore_reply_probability_gain", 1)
        
        return BaseMessageInfo(
            platform=config.platform,
            message_id=str(uuid.uuid4()),
            time=time.time(),
            group_info=None,
            user_info=user_info,
            format_info=self.format_info,
            additional_config=config_dict,
        )
    
    def _create_message(
        self,
        text: str,
        msg_type: str = "text",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> MessageBase:
        """创建消息对象
        
        参数:
            text: 消息内容
            msg_type: 消息类型（text/image/emoji等）
            user_id: 用户ID
            user_nickname: 用户昵称
            user_cardname: 用户群名片
            additional_config: 附加配置
        
        返回:
            MessageBase: 消息对象
        """
        user_info = self._create_user_info(user_id, user_nickname, user_cardname)
        message_info = self._create_message_info(user_info, additional_config)
        message_segment = Seg(type=msg_type, data=text)
        
        return MessageBase(
            message_info=message_info,
            message_segment=message_segment,
            raw_message=text
        )
    
    async def send(
        self,
        text: str,
        msg_type: str = "text",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """发送消息
        
        参数:
            text: 消息内容
            msg_type: 消息类型（默认为 "text"）
            user_id: 用户ID
            user_nickname: 用户昵称
            user_cardname: 用户群名片
            additional_config: 附加配置
        
        返回:
            bool: 是否发送成功
        
        异常:
            会捕获并记录异常，返回 False
        """
        try:
            # 验证输入
            if not text or not isinstance(text, str):
                logger.warning(f"无效的消息内容: {text}")
                return False
            
            if not isinstance(msg_type, str):
                logger.warning(f"无效的消息类型: {msg_type}")
                return False
            
            # 创建消息
            message_base = self._create_message(
                text=text,
                msg_type=msg_type,
                user_id=user_id,
                user_nickname=user_nickname,
                user_cardname=user_cardname,
                additional_config=additional_config
            )
            
            # 使用协议管理器发送消息
            send_success = await protocol_manager.send_message(message_base.to_dict())
            
            if not send_success:
                logger.warning(f"消息发送失败 - 协议管理器返回失败")
                return False
            
            # 将发送的消息保存到数据库
            try:
                if db_manager.is_initialized():
                    save_success = await db_manager.save_message(message_base.to_dict())
                    if save_success:
                        logger.debug(f"发送消息已保存到数据库")
                    else:
                        logger.warning(f"发送消息保存到数据库失败")
                else:
                    logger.debug(f"数据库未初始化，跳过消息存储")
            except Exception as db_error:
                logger.error(f"保存发送消息到数据库时出错: {db_error}", exc_info=True)
            
            logger.info(f"消息发送成功 - ID: {message_base.message_info.message_id}, "
                       f"内容: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            return True
            
        except Exception as e:
            logger.error(f"消息发送失败 - 错误: {e}", exc_info=True)
            return False
    
    async def easy_to_send(
        self,
        text: str,
        msg_type: str = "text"
    ) -> bool:
        """简化版消息发送（保持向后兼容）
        
        参数:
            text: 消息内容
            msg_type: 消息类型
        
        返回:
            bool: 是否发送成功
        """
        return await self.send(text=text, msg_type=msg_type)
    
    async def send_text(self, text: str) -> bool:
        """发送文本消息
        
        参数:
            text: 文本内容
        
        返回:
            bool: 是否发送成功
        """
        return await self.send(text=text, msg_type="text")
    
    async def send_image(self, image_data: str) -> bool:
        """发送图片消息
        
        参数:
            image_data: 图片数据（URL或base64等）
        
        返回:
            bool: 是否发送成功
        """
        return await self.send(text=image_data, msg_type="image")
    
    async def send_emoji(self, emoji: str) -> bool:
        """发送表情消息
        
        参数:
            emoji: 表情内容
        
        返回:
            bool: 是否发送成功
        """
        return await self.send(text=emoji, msg_type="emoji")


# 创建全局实例
chat_util = Chat()


# 向后兼容的别名
chat = Chat()
