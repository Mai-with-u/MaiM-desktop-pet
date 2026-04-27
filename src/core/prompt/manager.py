"""
Prompt 管理器。

负责为 OpenAI 兼容接口构建 messages，并动态拼接当前时间、身份信息、
桌宠设定和最近上下文。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.util.logger import logger


DEFAULT_PERSONA = (
    "你活泼、亲切，愿意陪伴用户。回复时尽量简短自然，"
    "可以有一点桌面宠物的可爱感，但不要影响信息表达。"
)


class PromptManager:
    """Prompt 管理器。"""

    def __init__(self):
        self._system_prompt_override: Optional[str] = None
        logger.info("Prompt 管理器初始化完成")

    def build_messages(
        self,
        user_content: str,
        user_id: str = "0",
        user_name: str = "用户",
        context_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, str]]:
        """
        构建 OpenAI 兼容格式的 messages。

        Args:
            user_content: 当前用户消息内容
            user_id: 用户 ID
            user_name: 当前调用传入的用户昵称兜底值
            context_messages: 最近历史消息，按时间正序传入

        Returns:
            OpenAI 兼容格式的消息列表
        """
        runtime_config = self._load_runtime_config()
        pet_name = self._resolve_pet_name(runtime_config)
        user_nickname = self._resolve_user_name(runtime_config, user_name)

        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": self._build_system_prompt(runtime_config, pet_name, user_nickname),
            }
        ]

        if self._get_bool(runtime_config, "include_context", True):
            messages.extend(
                self._format_context_messages(
                    runtime_config=runtime_config,
                    context_messages=context_messages or [],
                    current_content=user_content,
                    pet_name=pet_name,
                    user_nickname=user_nickname,
                )
            )

        messages.append({"role": "user", "content": f"{user_nickname}: {user_content}"})
        logger.debug(f"构建 OpenAI messages: {len(messages)} 条")
        return messages

    def get_context_limit(self) -> int:
        """读取 prompt 上下文条数配置。"""
        return self._get_context_limit(self._load_runtime_config())

    def set_system_prompt(self, prompt: str):
        """
        设置运行时人设兜底文本。

        这里保留旧接口兼容性；动态时间、昵称和上下文仍会继续拼接。
        """
        self._system_prompt_override = prompt
        logger.info(f"更新运行时人设: {prompt[:50]}...")

    def get_system_prompt(self) -> str:
        """获取当前动态 system prompt 预览。"""
        runtime_config = self._load_runtime_config()
        pet_name = self._resolve_pet_name(runtime_config)
        user_nickname = self._resolve_user_name(runtime_config, "用户")
        return self._build_system_prompt(runtime_config, pet_name, user_nickname)

    def _load_runtime_config(self) -> Any:
        try:
            from config import load_config

            return load_config()
        except SystemExit as e:
            logger.warning(f"读取 prompt 配置触发退出，使用默认人设: {e}")
        except Exception as e:
            logger.warning(f"读取 prompt 配置失败，使用默认人设: {e}")
        return None

    def _build_system_prompt(self, runtime_config: Any, pet_name: str, user_nickname: str) -> str:
        persona = self._system_prompt_override or self._get_prompt_value(
            runtime_config,
            "persona",
            DEFAULT_PERSONA,
        )
        if not str(persona).strip():
            persona = DEFAULT_PERSONA

        lines: List[str] = []
        if self._get_bool(runtime_config, "include_time", True):
            now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            lines.append(f"当前时间：{now}")

        lines.extend(
            [
                f"你的名字是：{pet_name}",
                f"用户昵称是：{user_nickname}",
                "你是一个运行在用户电脑上的桌面宠物。",
                f"你的设定：{persona}",
                "",
                "对话要求：",
                "- 结合当前时间和最近上下文自然回复。",
                "- 保持桌面宠物身份，语气亲切，但不要过度卖萌。",
                "- 无法确认的信息要直接说明，不要编造。",
            ]
        )
        return "\n".join(lines)

    def _format_context_messages(
        self,
        runtime_config: Any,
        context_messages: List[Dict[str, Any]],
        current_content: str,
        pet_name: str,
        user_nickname: str,
    ) -> List[Dict[str, str]]:
        max_chars = self._get_int(runtime_config, "context_message_max_chars", 500)
        current_text = self._normalize_text(current_content, max_chars)
        extracted_context = []
        for index, item in enumerate(context_messages):
            text = self._extract_message_text(item, max_chars)
            if not text:
                continue
            extracted_context.append((index, item, text))

        skip_current_index: Optional[int] = None
        for index, item, text in reversed(extracted_context):
            if str(item.get("user_id", "")) == "0" and text == current_text:
                skip_current_index = index
                break

        formatted: List[Dict[str, str]] = []
        for index, item, text in extracted_context:
            is_user_message = str(item.get("user_id", "")) == "0"
            if skip_current_index is not None and index == skip_current_index:
                continue

            role = "user" if is_user_message else "assistant"
            speaker = user_nickname if is_user_message else pet_name
            timestamp = self._format_timestamp(item.get("timestamp"))
            prefix = f"[{timestamp}] {speaker}" if timestamp else speaker
            formatted.append({"role": role, "content": f"{prefix}: {text}"})

        context_limit = self._get_context_limit(runtime_config)
        if context_limit <= 0:
            return []
        return formatted[-context_limit:]

    def _extract_message_text(self, item: Dict[str, Any], max_chars: int) -> str:
        raw_message = item.get("raw_message")
        if raw_message:
            return self._normalize_text(str(raw_message), max_chars)

        content = item.get("message_content")
        if isinstance(content, str):
            return self._normalize_text(content, max_chars)
        if isinstance(content, dict):
            for key in ("text", "content", "data", "value"):
                value = content.get(key)
                if isinstance(value, str):
                    return self._normalize_text(value, max_chars)
            return self._normalize_text(str(content), max_chars)
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    value = part.get("text") or part.get("content") or part.get("data")
                    if value is not None:
                        parts.append(str(value))
            return self._normalize_text(" ".join(parts), max_chars)
        if content is not None:
            return self._normalize_text(str(content), max_chars)
        return ""

    def _normalize_text(self, text: str, max_chars: int) -> str:
        normalized = " ".join(str(text).split())
        if max_chars > 0 and len(normalized) > max_chars:
            return normalized[:max_chars].rstrip() + "..."
        return normalized

    def _format_timestamp(self, timestamp: Any) -> str:
        try:
            if timestamp is None:
                return ""
            return datetime.fromtimestamp(float(timestamp)).strftime("%m-%d %H:%M")
        except (TypeError, ValueError, OSError):
            return ""

    def _resolve_pet_name(self, runtime_config: Any) -> str:
        nickname = getattr(runtime_config, "Nickname", None) if runtime_config else None
        return str(nickname).strip() or "麦麦"

    def _resolve_user_name(self, runtime_config: Any, fallback: str) -> str:
        user_nickname = getattr(runtime_config, "userNickname", None) if runtime_config else None
        return str(user_nickname or fallback or "用户").strip() or "用户"

    def _get_prompt_value(self, runtime_config: Any, key: str, default: Any) -> Any:
        prompt_config = getattr(runtime_config, "prompt", None) if runtime_config else None
        if prompt_config is None:
            return default
        value = getattr(prompt_config, key, default)
        return default if value is None else value

    def _get_context_limit(self, runtime_config: Any) -> int:
        if not self._get_bool(runtime_config, "include_context", True):
            return 0
        return self._get_int(runtime_config, "context_limit", 8)

    def _get_int(self, runtime_config: Any, key: str, default: int) -> int:
        value = self._get_prompt_value(runtime_config, key, default)
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    def _get_bool(self, runtime_config: Any, key: str, default: bool) -> bool:
        value = self._get_prompt_value(runtime_config, key, default)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)


# 全局单例
prompt_manager = PromptManager()
