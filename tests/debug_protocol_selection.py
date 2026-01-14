"""
调试协议选择逻辑
"""
import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.chat_manager import chat_manager
from src.core.protocol_manager import protocol_manager
from config.model_config_loader import (
    load_model_config,
    get_chat_task_config,
    get_model_config,
    get_provider_config
)

async def main():
    print("=" * 70)
    print("调试协议选择逻辑")
    print("=" * 70)
    
    # 1. 读取配置
    print("\n1. 读取 model_config.toml 配置...")
    model_config = load_model_config()
    
    # 2. 获取聊天任务配置
    print("\n2. 获取聊天任务配置...")
    chat_config = get_chat_task_config()
    print(f"   模型列表: {chat_config.model_list}")
    
    # 3. 获取第一个模型的配置
    print("\n3. 获取第一个模型配置...")
    first_model = chat_config.model_list[0]
    print(f"   第一个模型: {first_model}")
    
    model_config_dict = get_model_config(first_model)
    print(f"   模型标识: {model_config_dict.model_identifier}")
    print(f"   API 提供商: {model_config_dict.api_provider}")
    
    # 4. 获取 API 提供商配置
    print("\n4. 获取 API 提供商配置...")
    provider_config = get_provider_config(model_config_dict.api_provider)
    print(f"   提供商名称: {provider_config.name}")
    print(f"   客户端类型: {provider_config.client_type}")
    print(f"   Base URL: {provider_config.base_url}")
    print(f"   API Key: {provider_config.api_key[:8]}..." if provider_config.api_key else "***")
    
    # 5. 转换为协议配置列表
    print("\n5. 转换为协议配置...")
    from config.protocol_config_loader import load_protocol_configs
    protocol_configs = load_protocol_configs(model_config)
    
    print(f"\n   协议配置列表:")
    for i, config in enumerate(protocol_configs):
        print(f"   [{i}] {config.get('type')} - {config.get('platform', config.get('base_url', ''))}")
        if config.get('type') == 'openai':
            print(f"       API Key: {config.get('api_key', '')[:8]}...")
    
    # 6. 初始化协议管理器
    print("\n6. 初始化协议管理器...")
    await protocol_manager.initialize(protocol_configs)
    
    print("\n   所有已加载的协议:")
    for name, protocol in protocol_manager.get_all_protocols().items():
        print(f"   - {name}")
    
    print(f"\n   当前激活的协议: {protocol_manager.get_active_protocol().get_name()}")
    
    # 7. 初始化聊天管理器
    print("\n7. 初始化聊天管理器...")
    await chat_manager.initialize()
    
    print(f"\n   聊天管理器协议类型: {chat_manager.get_protocol_type()}")
    print(f"   当前激活的协议: {protocol_manager.get_active_protocol().get_name()}")
    
    # 8. 检查协议配置是否正确传递
    print("\n8. 检查协议配置...")
    active_protocol = protocol_manager.get_active_protocol()
    
    if active_protocol.get_name() == "OpenAI":
        # 这是 OpenAI 协议，检查配置
        from src.core.protocols.openai_protocol import OpenAIProtocol
        if isinstance(active_protocol, OpenAIProtocol):
            print(f"   协议类型: OpenAI")
            print(f"   Base URL: {active_protocol._base_url}")
            print(f"   Model: {active_protocol._model}")
            print(f"   API Key: {active_protocol._api_key[:8] if active_protocol._api_key else 'None'}...")
    
    print("\n" + "=" * 70)
    
    # 清理
    await protocol_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
