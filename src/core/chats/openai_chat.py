"""
OpenAI 聊天实现 - 专为 OpenAI 兼容协议设计的聊天功能

支持的消息类型：
- text: 纯文本消息（所有模型）
- image: 图片消息（仅视觉模型，如 GPT-4 Vision、GPT-4o、通义千问 Vision 等）
- seglist: 复合消息（支持文本+图片组合）

注意：
- 文本消息：所有 OpenAI 兼容模型都支持
- 图片消息：仅支持 Vision API 的模型（GPT-4 Vision、GPT-4o、通义千问 Vision 等）
- 如果模型不支持视觉，发送图片时会收到错误
- 有对话历史管理功能
"""

from typing import Optional, List
from PyQt5.QtGui import QPixmap

from src.core.chats.interfaces import IChat
from src.core.protocol_manager import protocol_manager
from src.util.logger import logger
from src.database import db_manager


class OpenAIChat(IChat):
    """OpenAI 聊天实现 - 专为 OpenAI 协议设计"""
    
    def __init__(self):
        """初始化 OpenAI 聊天"""
        self.default_user_id = "openai_user"
    
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
        
        注意：
            OpenAI 协议只支持文本消息
            user_id、user_nickname 等参数会被忽略（OpenAI 不需要这些信息）
        """
        try:
            # 验证输入
            if not text or not isinstance(text, str):
                logger.warning(f"无效的消息内容: {text}")
                return False
            
            # 只支持文本消息
            if msg_type != "text":
                logger.warning(f"OpenAI 协议不支持的消息类型: {msg_type}，只支持 'text'")
                return False
            
            # 创建统一格式的消息
            message = {
                'message_segment': {
                    'type': 'text',
                    'data': text
                }
            }
            
            # 使用协议管理器发送消息
            send_success = await protocol_manager.send_message(message)
            
            if not send_success:
                logger.warning(f"OpenAI 消息发送失败")
                return False
            
            # 将发送的消息保存到数据库
            try:
                if db_manager.is_initialized():
                    save_success = await db_manager.save_message(message)
                    if save_success:
                        logger.debug(f"OpenAI 发送消息已保存到数据库")
                    else:
                        logger.warning(f"OpenAI 发送消息保存到数据库失败")
                else:
                    logger.debug(f"数据库未初始化，跳过消息存储")
            except Exception as db_error:
                logger.error(f"保存 OpenAI 发送消息到数据库时出错: {db_error}", exc_info=True)
            
            logger.info(f"OpenAI 消息发送成功 - 内容: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            return True
            
        except Exception as e:
            logger.error(f"OpenAI 消息发送失败 - 错误: {e}", exc_info=True)
            return False
    
    async def send_text(self, text: str, additional_config: Optional[dict] = None) -> bool:
        """
        发送文本消息
        
        注意：
            OpenAI 协议不需要 additional_config 参数，此参数会被忽略
            additional_config 参数是为了与 MaimChat 保持接口一致
        
        Args:
            text: 消息文本
            additional_config: 附加配置（会被忽略，OpenAI 协议不需要）
        
        Returns:
            是否发送成功
        """
        # OpenAI 协议忽略 additional_config 参数
        # 这个参数只是为了与 MaimChat 保持接口一致
        return await self.send(text=text, msg_type="text")
    
    async def send_image(self, image_data: str) -> bool:
        """
        发送图片消息
        
        注意：
        - 仅支持 Vision API 的模型才能处理图片（如 GPT-4 Vision、GPT-4o、通义千问 Vision 等）
        - image_data 应为 base64 编码的图片数据
        
        Args:
            image_data: base64 编码的图片数据
        
        Returns:
            是否发送成功
        """
        try:
            # 创建包含图片的 seglist 消息
            message = {
                'message_segment': {
                    'type': 'seglist',
                    'data': [
                        {'type': 'image', 'data': image_data}
                    ]
                }
            }
            
            # 使用协议管理器发送消息
            send_success = await protocol_manager.send_message(message)
            
            if not send_success:
                logger.warning("OpenAI 图片消息发送失败（可能是模型不支持视觉 API）")
                return False
            
            logger.info("OpenAI 图片消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI 图片消息发送失败 - 错误: {e}", exc_info=True)
            return False
    
    async def send_emoji(self, emoji: str) -> bool:
        """
        发送表情消息
        
        注意：OpenAI 协议不支持表情消息
        """
        logger.warning("OpenAI 协议不支持表情消息")
        return False
    
    async def send_seglist(
        self,
        segments: List,
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """
        发送复合消息（支持文本+图片）
        
        注意：
        - 如果包含图片，仅支持 Vision API 的模型才能处理
        - 参数 user_id、user_nickname、user_cardname 会被忽略（OpenAI 不需要这些信息）
        
        Args:
            segments: 段列表，每个段格式：
                - {'type': 'text', 'data': '文本内容'}
                - {'type': 'image', 'data': 'base64图片数据'}
                - 或使用元组格式: ('text', '文本内容')
        
        Returns:
            是否发送成功
        """
        try:
            # 转换段格式
            seg_list = []
            for seg in segments:
                if hasattr(seg, 'type') and hasattr(seg, 'data'):
                    # 对象格式
                    seg_list.append({
                        'type': seg.type,
                        'data': seg.data
                    })
                elif isinstance(seg, tuple) and len(seg) == 2:
                    # 元组格式
                    seg_list.append({
                        'type': seg[0],
                        'data': seg[1]
                    })
            
            if not seg_list:
                logger.warning("seglist 中没有有效的段")
                return False
            
            # 创建统一格式的消息
            message = {
                'message_segment': {
                    'type': 'seglist',
                    'data': seg_list
                }
            }
            
            # 使用协议管理器发送消息
            send_success = await protocol_manager.send_message(message)
            
            if not send_success:
                logger.warning("OpenAI seglist 消息发送失败")
                return False
            
            # 检查是否包含图片
            has_image = any(seg.get('type') == 'image' for seg in seg_list)
            if has_image:
                logger.info(f"OpenAI seglist 消息发送成功（包含 {len(seg_list)} 个段，含图片）")
            else:
                logger.info(f"OpenAI seglist 消息发送成功（包含 {len(seg_list)} 个文本段）")
            
            return True
            
        except Exception as e:
            logger.error(f"OpenAI seglist 消息发送失败 - 错误: {e}", exc_info=True)
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
        """
        发送文本+图片的复合消息
        
        注意：
        - 仅支持 Vision API 的模型才能处理图片
        - 参数 user_id、user_nickname、user_cardname 会被忽略（OpenAI 不需要这些信息）
        
        Args:
            text: 文本内容
            image_data: base64 编码的图片数据
        
        Returns:
            是否发送成功
        """
        try:
            # 创建包含文本和图片的 seglist 消息
            message = {
                'message_segment': {
                    'type': 'seglist',
                    'data': [
                        {'type': 'text', 'data': text},
                        {'type': 'image', 'data': image_data}
                    ]
                }
            }
            
            # 使用协议管理器发送消息
            send_success = await protocol_manager.send_message(message)
            
            if not send_success:
                logger.warning("OpenAI 文本+图片消息发送失败（可能是模型不支持视觉 API）")
                return False
            
            logger.info("OpenAI 文本+图片消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI 文本+图片消息发送失败 - 错误: {e}", exc_info=True)
            return False
    
    async def send_pixmap_with_text(
        self,
        pixmap: QPixmap,
        text: str = "",
        user_id: Optional[str] = None,
        user_nickname: Optional[str] = None,
        user_cardname: Optional[str] = None,
        additional_config: Optional[dict] = None
    ) -> bool:
        """
        发送 QPixmap 图片（带可选文本）
        
        注意：
        - 仅支持 Vision API 的模型才能处理图片
        - 需要将 QPixmap 转换为 base64 格式
        - 参数 user_id、user_nickname、user_cardname 会被忽略（OpenAI 不需要这些信息）
        
        Args:
            pixmap: QPixmap 图片对象
            text: 可选的文本描述
        
        Returns:
            是否发送成功
        """
        try:
            # 将 QPixmap 转换为 base64
            from io import BytesIO
            from PyQt5.QtCore import QBuffer
            
            # 保存到 buffer
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            pixmap.save(buffer, "JPEG")
            image_data = buffer.data().toBase64().data().decode('utf-8')
            buffer.close()
            
            # 根据是否有文本决定发送方式
            if text:
                return await self.send_text_and_image(text, image_data)
            else:
                return await self.send_image(image_data)
            
        except Exception as e:
            logger.error(f"OpenAI QPixmap 消息发送失败 - 错误: {e}", exc_info=True)
            return False
    
    def get_name(self) -> str:
        """获取聊天实现名称"""
        return "OpenAI"
    
    def is_supported_message_type(self, msg_type: str) -> bool:
        """
        检查是否支持指定的消息类型
        
        注意：
        - 所有模型都支持 text
        - image 和 seglist 需要模型支持 Vision API
        - 此方法仅返回功能支持状态，实际可用性取决于配置的模型
        
        Args:
            msg_type: 消息类型
        
        Returns:
            是否支持该消息类型（功能层面）
        """
        return msg_type in ["text", "image", "seglist"]
    
    def get_supported_message_types(self) -> List[str]:
        """
        获取支持的消息类型列表
        
        注意：
        - 返回功能支持的消息类型列表
        - 实际可用性取决于配置的模型是否支持 Vision API
        - 建议在配置中使用支持视觉的模型（如 GPT-4o、GPT-4 Vision、通义千问 Vision 等）
        
        Returns:
            支持的消息类型列表
        """
        return ["text", "image", "seglist"]
    
    def clear_history(self):
        """
        清除对话历史（保留系统提示词）
        
        这是一个便捷方法，调用 OpenAI 协议的 clear_history
        """
        try:
            # 获取 OpenAI 协议实例
            protocol = protocol_manager.get_protocol('OpenAI')
            if protocol and hasattr(protocol, 'clear_history'):
                protocol.clear_history()
                logger.info("OpenAI 对话历史已清除")
            else:
                logger.warning("无法清除对话历史：OpenAI 协议未找到或不支持清除历史")
        except Exception as e:
            logger.error(f"清除对话历史失败: {e}", exc_info=True)
    
    def get_history(self) -> List:
        """
        获取对话历史
        
        这是一个便捷方法，调用 OpenAI 协议的 get_history
        """
        try:
            # 获取 OpenAI 协议实例
            protocol = protocol_manager.get_protocol('OpenAI')
            if protocol and hasattr(protocol, 'get_history'):
                return protocol.get_history()
            else:
                logger.warning("无法获取对话历史：OpenAI 协议未找到或不支持获取历史")
                return []
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}", exc_info=True)
            return []


# 创建全局实例
openai_chat_util = OpenAIChat()
