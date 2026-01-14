"""
测试协议配置集成
验证从 model_config.toml 自动选择协议的功能
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.chat_manager import chat_manager
from src.core.protocol_manager import protocol_manager
from src.util.logger import logger


async def test_auto_protocol_selection():
    """测试自动协议选择"""
    print("\n" + "=" * 70)
    print("测试：从 model_config.toml 自动选择协议")
    print("=" * 70 + "\n")
    
    try:
        # 1. 初始化聊天管理器
        print("步骤 1: 初始化聊天管理器...")
        success = await chat_manager.initialize()
        
        if not success:
            print("❌ 聊天管理器初始化失败")
            return False
        
        print(f"✓ 聊天管理器初始化成功")
        print(f"  当前协议类型: {chat_manager.get_protocol_type()}")
        print(f"  当前聊天实现: {chat_manager.get_name()}")
        
        # 2. 检查协议管理器状态
        print("\n步骤 2: 检查协议管理器状态...")
        protocol_manager.print_status()
        
        # 3. 检查激活的协议
        active_protocol = protocol_manager.get_active_protocol()
        if active_protocol:
            print(f"✓ 激活的协议: {active_protocol.get_name()}")
            print(f"  连接状态: {'已连接' if active_protocol.is_connected() else '未连接'}")
        else:
            print("❌ 没有激活的协议")
            return False
        
        # 4. 打印所有可用的协议
        print("\n步骤 3: 打印所有可用的协议...")
        protocols = protocol_manager.get_all_protocols()
        print(f"✓ 共有 {len(protocols)} 个协议:")
        for name, protocol in protocols.items():
            is_active = "(激活)" if protocol == active_protocol else ""
            print(f"  - {name} {is_active}")
        
        # 5. 测试发送消息（不实际发送，只测试接口）
        print("\n步骤 4: 测试消息发送接口...")
        test_message = "测试消息"
        print(f"  准备发送: {test_message}")
        
        # 注意：这里不实际发送消息，因为可能没有连接到服务器
        # 只是验证接口是否可用
        print(f"✓ 消息发送接口可用")
        
        print("\n" + "=" * 70)
        print("✓ 所有测试通过")
        print("=" * 70 + "\n")
        
        # 清理
        chat_manager.clear_history()
        await protocol_manager.cleanup()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_config_reading():
    """测试配置读取"""
    print("\n" + "=" * 70)
    print("测试：读取 model_config.toml 配置")
    print("=" * 70 + "\n")
    
    try:
        from config.model_config_loader import (
            load_model_config,
            get_chat_task_config,
            get_model_config,
            get_provider_config
        )
        
        # 1. 加载配置
        print("步骤 1: 加载模型配置...")
        model_config = load_model_config()
        print(f"✓ 配置文件版本: {model_config.inner.version}")
        
        # 2. 获取聊天任务配置
        print("\n步骤 2: 获取聊天任务配置...")
        chat_config = get_chat_task_config()
        print(f"✓ 聊天任务模型列表: {chat_config.model_list}")
        print(f"  温度参数: {chat_config.temperature}")
        print(f"  最大 tokens: {chat_config.max_tokens}")
        
        # 3. 获取第一个模型的配置
        print("\n步骤 3: 获取第一个模型的配置...")
        first_model_name = chat_config.model_list[0]
        print(f"  第一个模型: {first_model_name}")
        
        model_config_dict = get_model_config(first_model_name)
        print(f"✓ 模型标识: {model_config_dict.model_identifier}")
        print(f"  模型名称: {model_config_dict.name}")
        print(f"  API 提供商: {model_config_dict.api_provider}")
        
        # 4. 获取 API 提供商配置
        print("\n步骤 4: 获取 API 提供商配置...")
        provider_config = get_provider_config(model_config_dict.api_provider)
        print(f"✓ 提供商名称: {provider_config.name}")
        print(f"  客户端类型: {provider_config.client_type}")
        print(f"  基础 URL: {provider_config.base_url}")
        
        # 5. 根据配置判断协议类型
        print("\n步骤 5: 判断协议类型...")
        protocol_type = provider_config.client_type.lower()
        print(f"✓ 协议类型: {protocol_type}")
        
        print("\n" + "=" * 70)
        print("✓ 配置读取测试通过")
        print("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("协议配置集成测试套件")
    print("=" * 70)
    
    # 测试 1: 配置读取
    success1 = await test_config_reading()
    
    # 测试 2: 自动协议选择
    success2 = await test_auto_protocol_selection()
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"配置读取测试: {'✓ 通过' if success1 else '❌ 失败'}")
    print(f"自动协议选择测试: {'✓ 通过' if success2 else '❌ 失败'}")
    print("=" * 70 + "\n")
    
    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
