"""
Minimal maim_message echo endpoint for local communication testing.

Usage:
    python tests/maim_message_echo_endpoint.py --host 127.0.0.1 --port 8000 --path /ws
"""

import argparse
import asyncio
import time
import uuid
from typing import Any, Dict

from maim_message import (
    BaseMessageInfo,
    FormatInfo,
    MessageBase,
    MessageServer,
    Seg,
    UserInfo,
)


def _extract_text(message: MessageBase) -> str:
    segment = message.message_segment
    if segment.type == "text":
        return str(segment.data or "")
    if segment.type == "seglist" and isinstance(segment.data, list):
        parts = []
        for item in segment.data:
            if getattr(item, "type", None) == "text":
                parts.append(str(getattr(item, "data", "") or ""))
            elif getattr(item, "type", None) == "image":
                parts.append("[image]")
            elif getattr(item, "type", None) == "emoji":
                parts.append("[emoji]")
        return "".join(parts)
    return f"[{segment.type}]"


def _build_reply(incoming: MessageBase, text: str) -> MessageBase:
    platform = incoming.message_info.platform or "desktop-pet"
    user_info = UserInfo(
        platform="maim-echo",
        user_id="maim-echo",
        user_nickname="Maim Echo",
        user_cardname="",
    )
    message_info = BaseMessageInfo(
        platform=platform,
        message_id=str(uuid.uuid4()),
        time=time.time(),
        user_info=user_info,
        format_info=FormatInfo(content_format=["text"], accept_format=["text"]),
    )
    return MessageBase(
        message_info=message_info,
        message_segment=Seg(type="text", data=f"echo: {text}"),
        raw_message=text,
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal maim_message echo endpoint.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/ws")
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    server = MessageServer(
        host=args.host,
        port=args.port,
        path=args.path,
        mode="ws",
        enable_token=bool(args.token),
        enable_custom_uvicorn_logger=True,
    )
    if args.token:
        server.add_valid_token(args.token)

    async def handle_message(raw_message: Dict[str, Any]) -> None:
        incoming = MessageBase.from_dict(raw_message)
        text = _extract_text(incoming)
        print(f"[recv] {incoming.message_info.platform}: {text}")
        reply = _build_reply(incoming, text)
        success = await server.send_message(reply)
        print(f"[send] {reply.message_info.platform}: {success}")

    server.register_message_handler(handle_message)

    print(f"maim_message echo endpoint listening on ws://{args.host}:{args.port}{args.path}")
    print("Press Ctrl+C to stop.")
    try:
        await server.run()
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
