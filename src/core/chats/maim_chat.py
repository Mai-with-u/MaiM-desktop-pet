"""
Maim 聊天实现 - 专为 Maim 协议设计的聊天功能

支持的消息类型：
- text: 纯文本消息
- image: 图片消息（base64编码，无头部）
- emoji: 表情消息（base64编码，无头部）
- seglist: 复合消息，包含多个不同类型的 Seg
"""

from maim_message import UserInfo, Seg, MessageBase, BaseMessageInfo, FormatInfo
from typing import Optional, List, Union
import time
import uuid

from config import load_config
from src.core.protocol_manager import protocol_manager
from src.util.image_util import pixmap_to_base64
from src.core.chats.interfaces import IChat
from src.util.logger import logger
from src.database import db_manager

# 加载配置
config = load_config()


class MaimChat(IChat):
    """Maim 聊天实现 - 专为 Maim 协议设计"""
    
    def __init__(self):
        """初始化 Maim 聊天"""
        self.format_info = FormatInfo(
            content_format=["text", "image", "emoji"],
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
        
        注意：
            platform 字段用于标识消息来源平台
            虽然 config.platform 已标记为废弃，但此处用于消息构建，保留向后兼容
            未来建议从当前激活的协议获取 platform 信息
        """
        # 确保 platform 不为空
        # 注意：config.platform 已废弃，此处保留用于向后兼容
        # 未来可从 protocol_manager.get_active_protocol() 获取
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
            platform=getattr(config, 'platform', 'desktop-pet'),  # 已废弃，保留用于向后兼容
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
    
    async def send_text(self, text: str, additional_config: Optional[dict] = None) -> bool:
        """
        发送文本消息
        
        参数:
            text: 消息文本
            additional_config: 附加配置（如回复概率增益等）
        
        返回:
            bool: 是否发送成功
        """
        return await self.send(text=text, msg_type="text", additional_config=additional_config)
    
    async def send_image(self, image_data: str) -> bool:
        """发送图片消息"""
        return await self.send(text=image_data, msg_type="image")
    
    async def send_emoji(self, emoji: str) -> bool:
        """发送表情消息"""
        return await self.send(text=emoji, msg_type="emoji")
    
    def _create_seglist_segment(
        self,
        segments: List[Union[Seg, tuple]]
    ) -> Seg:
        """创建 seglist 类型的消息片段"""
        seg_list = []
        
        for seg in segments:
            if isinstance(seg, Seg):
                seg_list.append(seg)
            elif isinstance(seg, tuple) and len(seg) == 2:
                seg_type, seg_data = seg
                
                # 确保 seg_data 是字符串类型
                if isinstance(seg_data, dict):
                    import json
                    seg_data = json.dumps(seg_data, ensure_ascii=False)
                elif not isinstance(seg_data, str):
                    seg_data = str(seg_data)
                
                seg_list.append(Seg(type=seg_type, data=seg_data))
            else:
                logger.warning(f"无效的段格式，已跳过: {seg}")
        
        return Seg(type="seglist", data=seg_list)
    
    async def send_seglist(
        self,
        segments: List[Union[Seg, tuple]],
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """发送复合消息"""
        try:
            # 创建 seglist 段
            seglist = self._create_seglist_segment(segments)
            
            # 创建用户信息
            user_info = self._create_user_info(user_id, user_nickname, user_cardname)
            message_info = self._create_message_info(user_info, additional_config)
            
            # 创建消息
            message_base = MessageBase(
                message_info=message_info,
                message_segment=seglist,
                raw_message=""
            )
            
            # 使用协议管理器发送消息
            send_success = await protocol_manager.send_message(message_base.to_dict())
            
            if not send_success:
                logger.warning(f"seglist 消息发送失败 - 协议管理器返回失败")
                return False
            
            # 将发送的消息保存到数据库
            try:
                if db_manager.is_initialized():
                    save_success = await db_manager.save_message(message_base.to_dict())
                    if save_success:
                        logger.debug(f"seglist 消息已保存到数据库")
                    else:
                        logger.warning(f"seglist 消息保存到数据库失败")
                else:
                    logger.debug(f"数据库未初始化，跳过消息存储")
            except Exception as db_error:
                logger.error(f"保存 seglist 消息到数据库时出错: {db_error}", exc_info=True)
            
            logger.info(f"seglist 消息发送成功 - ID: {message_base.message_info.message_id}, "
                       f"段数: {len(segments)}")
            
            return True
            
        except Exception as e:
            logger.error(f"seglist 消息发送失败 - 错误: {e}", exc_info=True)
            return False
    
    async def send_text_and_image(
        self,
        text: str,
        image_data: str,
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """发送文本+图片的复合消息"""
        return await self.send_seglist([
            ("text", text),
            ("image", image_data),
        ], user_id, user_nickname, user_cardname, additional_config)
    
    async def send_pixmap_with_text(
        self,
        pixmap,
        text: str = "",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """发送 QPixmap 图片（带可选文本）"""
        try:
            # 将 QPixmap 转换为 base64（无头部）
            image_base64 = pixmap_to_base64(pixmap, add_header=False)
            
            if text:
                return await self.send_text_and_image(
                    text, image_base64, user_id, user_nickname, user_cardname, additional_config
                )
            else:
                return await self.send_image(image_base64)
                
        except Exception as e:
            logger.error(f"发送 QPixmap 失败 - 错误: {e}", exc_info=True)
            return False
    
    def get_name(self) -> str:
        """获取聊天实现名称"""
        return "Maim"
    
    def is_supported_message_type(self, msg_type: str) -> bool:
        """检查是否支持指定的消息类型"""
        return msg_type in ["text", "image", "emoji", "seglist"]
    
    def get_supported_message_types(self) -> List[str]:
        """获取支持的消息类型列表"""
        return ["text", "image", "emoji", "seglist"]


# 创建全局实例（向后兼容）
maim_chat_util = MaimChat()
chat_util = maim_chat_util  # 别名，保持向后兼容
chat = maim_chat_util  # 别名，保持向后兼容
