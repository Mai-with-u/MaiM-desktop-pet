"""
Prompt 管理器
负责构建和管理对话的 prompt 结构，包括人设信息
"""

from typing import List, Dict
from src.util.logger import logger


class PromptManager:
    """Prompt 管理器"""

    def __init__(self):
        # 暂时硬编码人设信息（后续可从配置文件读取）
        self._system_prompt = """你是麦麦，一个可爱的桌面宠物助手。

你的特点：
- 活泼开朗，喜欢和用户互动
- 会用可爱的语气说话
- 关心用户的状态和感受
- 有时会撒娇或卖萌
- 使用简短的语句回复

请用亲切、活泼的语气回复用户的消息。"""

        logger.info("Prompt 管理器初始化完成")
        logger.debug(f"人设信息: {self._system_prompt[:50]}...")

    def build_messages(self, user_content: str, user_id: str = '0', user_name: str = '麦麦') -> List[Dict[str, str]]:
        """
        构建完整的消息列表（包含 system message 和 user message）

        Args:
            user_content: 用户消息内容
            user_id: 用户 ID
            user_name: 用户昵称

        Returns:
            OpenAI 格式的消息列表
        """
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_content}
        ]

        logger.debug(f"构建消息列表: {len(messages)} 条")
        return messages

    def set_system_prompt(self, prompt: str):
        """
        设置人设信息（用于后续从配置文件读取）

        Args:
            prompt: 人设 prompt
        """
        self._system_prompt = prompt
        logger.info(f"更新人设信息: {prompt[:50]}...")

    def get_system_prompt(self) -> str:
        """
        获取当前人设信息

        Returns:
            当前的人设 prompt
        """
        return self._system_prompt


# 全局单例
prompt_manager = PromptManager()