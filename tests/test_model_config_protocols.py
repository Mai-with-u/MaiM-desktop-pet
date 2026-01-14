#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
协议使用示例 - 演示如何分别使用 Maim 和 OpenAI 协议

本示例展示：
1. 从 model_config.toml 加载协议配置
2. 分别初始化和使用 Maim 协议
3. 分别初始化和使用 OpenAI 协议
4. 协议切换功能
5. 消息发送和接收
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.protocol_manager import protocol_manager
from src.core.protocols.protocol_factory import ProtocolFactory
from src.core.protocols.maim_protocol import MaimProtocol
from src.core.protocols.openai_protocol import OpenAIProtocol
from config import (
    load_model_config,
    load_protocol_configs,
    get_model_config_by_task,
    get_models_by_provider,
    get_model_config,
    validate_protocol_configs
)
from src.util.logger import logger


class ExampleMessageHandler:
    """示例消息处理器"""
    
    def __init__(self, name):
        self.name = name
        self.messages = []
    
    async def __call__(self, message):
        """处理接收到的消息"""
        self.messages.append(message)
        
        # 解析消息
        msg_type = message.get('message_segment', {}).get('type', 'unknown')
        msg_data = message.get('message_segment', {}).get('data', '')
        
        logger.info(f"[{self.name}] 收到消息 - 类型: {msg_type}")
        logger.info(f"[{self.name}] 内容: {str(msg_data)[:100]}...")


# ============================================================================
# 示例 1: 使用 model_config.toml 初始化协议管理器（推荐方式）
# ============================================================================

async def example1_protocol_manager_with_model_config():
    """
    示例 1: 使用 model_config.toml 初始化协议管理器
    
    这是推荐的方式，所有协议配置都在 model_config.toml 中统一管理
    """
    print("\n" + "=" * 80)
    print("示例 1: 使用 model_config.toml 初始化协议管理器")
    print("=" * 80)
    
    try:
        # 步骤 1: 检查 model_config.toml 是否存在
        model_config_path = project_root / "model_config.toml"
        if not model_config_path.exists():
            print(f"❌ model_config.toml 不存在: {model_config_path}")
            print("请先创建 model_config.toml 文件")
            return False
        
        print(f"✅ model_config.toml 存在")
        
        # 步骤 2: 使用协议管理器的新方法初始化
        print("\n📋 从 model_config.toml 初始化协议管理器...")
        await protocol_manager.initialize_from_model_config()
        
        # 步骤 3: 查看已加载的协议
        protocols = protocol_manager.get_protocol_names()
        print(f"\n✅ 已加载 {len(protocols)} 个协议:")
        for i, name in enumerate(protocols, 1):
            protocol = protocol_manager.get_protocol(name)
            connected = "已连接" if protocol.is_connected() else "未连接"
            print(f"  {i}. {name} ({connected})")
        
        # 步骤 4: 注册消息处理器
        handler = ExampleMessageHandler("协议管理器示例")
        protocol_manager.register_message_handler(handler)
        print(f"\n✅ 消息处理器已注册")
        
        # 步骤 5: 发送测试消息
        if protocols:
            active = protocol_manager.get_active_protocol()
            if active:
                print(f"\n📤 使用 {active.get_name()} 协议发送测试消息...")
                success = await protocol_manager.send_message({
                    'message_segment': {
                        'type': 'text',
                        'data': '这是一条测试消息 - 来自 model_config.toml'
                    }
                })
                print(f"✅ 发送{'成功' if success else '失败'}")
        
        # 步骤 6: 协议切换（如果有多个协议）
        if len(protocols) > 1:
            print(f"\n🔄 演示协议切换...")
            for i in range(min(3, len(protocols))):
                current = protocol_manager.get_active_protocol()
                current_name = current.get_name() if current else "None"
                
                # 切换到下一个协议
                next_idx = (i + 1) % len(protocols)
                next_name = protocols[next_idx]
                
                print(f"  {current_name} → {next_name}")
                success = await protocol_manager.switch_protocol(next_name)
                
                if success:
                    print(f"  ✅ 切换成功")
                    await asyncio.sleep(1)  # 等待连接建立
                else:
                    print(f"  ❌ 切换失败")
        
        # 步骤 7: 打印状态
        print("\n📊 协议管理器状态:")
        protocol_manager.print_status()
        
        print("\n✅ 示例 1 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 示例 1 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 示例 2: 直接使用 Maim 协议
# ============================================================================

async def example2_maim_protocol():
    """
    示例 2: 直接使用 Maim 协议
    
    展示如何单独创建和使用 Maim 协议，不依赖协议管理器
    """
    print("\n" + "=" * 80)
    print("示例 2: 直接使用 Maim 协议")
    print("=" * 80)
    
    try:
        # 步骤 1: 加载模型配置
        model_config = load_model_config()
        
        # 步骤 2: 获取 Maim 提供商配置
        maim_providers = [p for p in model_config.api_providers 
                        if p.provider_type == 'maim']
        
        if not maim_providers:
            print("❌ 未找到 Maim 协议配置")
            return False
        
        maim_provider = maim_providers[0]
        print(f"✅ 找到 Maim 配置: {maim_provider.name}")
        print(f"   URL: {maim_provider.url}")
        print(f"   Platform: {maim_provider.platform}")
        
        # 步骤 3: 创建 Maim 协议实例
        protocol = MaimProtocol()
        print(f"\n✅ Maim 协议实例创建成功")
        
        # 步骤 4: 准备配置字典
        config_dict = {
            'url': maim_provider.url,
            'platform': maim_provider.platform or 'default',
        }
        if maim_provider.api_key:
            config_dict['token'] = maim_provider.api_key
        
        # 步骤 5: 初始化协议
        print(f"\n📋 初始化 Maim 协议...")
        init_success = await protocol.initialize(config_dict)
        
        if not init_success:
            print(f"❌ 协议初始化失败")
            return False
        
        print(f"✅ 协议初始化成功")
        
        # 步骤 6: 注册消息处理器
        handler = ExampleMessageHandler("Maim 协议示例")
        protocol.register_message_handler(handler)
        print(f"✅ 消息处理器已注册")
        
        # 步骤 7: 连接协议
        print(f"\n🔗 连接 Maim 协议...")
        connect_success = await protocol.connect()
        
        if not connect_success:
            print(f"❌ 协议连接失败（可能是因为服务器未运行）")
            print(f"   这是正常的，请确保 Maim 服务器正在运行")
            # 继续执行，不返回 False
        else:
            print(f"✅ 协议连接成功")
        
        # 步骤 8: 发送测试消息
        if protocol.is_connected():
            print(f"\n📤 发送测试消息...")
            success = await protocol.send_message({
                'message_segment': {
                    'type': 'text',
                    'data': '这是直接使用 Maim 协议发送的测试消息'
                }
            })
            print(f"✅ 发送{'成功' if success else '失败'}")
        else:
            print(f"\n⚠️  协议未连接，跳过发送消息")
        
        # 步骤 9: 等待接收消息
        if protocol.is_connected():
            print(f"\n⏳ 等待 5 秒接收消息...")
            await asyncio.sleep(5)
            
            if handler.messages:
                print(f"✅ 收到 {len(handler.messages)} 条消息")
            else:
                print(f"ℹ️  未收到消息（正常，可能没有发送者）")
        
        # 步骤 10: 断开连接
        print(f"\n🔌 断开连接...")
        await protocol.disconnect()
        print(f"✅ 已断开连接")
        
        # 步骤 11: 清理资源
        await protocol.cleanup()
        print(f"✅ 资源已清理")
        
        print(f"\n✅ 示例 2 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 示例 2 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 示例 3: 直接使用 OpenAI 协议
# ============================================================================

async def example3_openai_protocol():
    """
    示例 3: 直接使用 OpenAI 协议
    
    展示如何单独创建和使用 OpenAI 协议
    """
    print("\n" + "=" * 80)
    print("示例 3: 直接使用 OpenAI 协议")
    print("=" * 80)
    
    try:
        # 步骤 1: 加载模型配置
        model_config = load_model_config()
        
        # 步骤 2: 获取 OpenAI 提供商配置
        openai_providers = [p for p in model_config.api_providers 
                          if p.provider_type == 'openai']
        
        if not openai_providers:
            print("❌ 未找到 OpenAI 协议配置")
            return False
        
        openai_provider = openai_providers[0]
        print(f"✅ 找到 OpenAI 配置: {openai_provider.name}")
        print(f"   URL: {openai_provider.url}")
        
        # 步骤 3: 创建 OpenAI 协议实例
        protocol = OpenAIProtocol()
        print(f"\n✅ OpenAI 协议实例创建成功")
        
        # 步骤 4: 准备配置字典
        config_dict = {
            'api_key': openai_provider.api_key,
            'base_url': openai_provider.url,
        }
        
        # 添加额外参数
        if openai_provider.extra_params:
            config_dict.update(openai_provider.extra_params)
            print(f"   额外参数: {openai_provider.extra_params}")
        
        # 步骤 5: 初始化协议
        print(f"\n📋 初始化 OpenAI 协议...")
        init_success = await protocol.initialize(config_dict)
        
        if not init_success:
            print(f"❌ 协议初始化失败")
            return False
        
        print(f"✅ 协议初始化成功")
        print(f"   模型: {protocol._model}")
        
        # 步骤 6: 连接协议
        print(f"\n🔗 连接 OpenAI 协议...")
        connect_success = await protocol.connect()
        
        if not connect_success:
            print(f"❌ 协议连接失败（可能是因为 API Key 无效或网络问题）")
            print(f"   请检查 API Key 和网络连接")
            return False
        
        print(f"✅ 协议连接成功")
        
        # 步骤 7: 注册消息处理器
        handler = ExampleMessageHandler("OpenAI 协议示例")
        protocol.register_message_handler(handler)
        print(f"✅ 消息处理器已注册")
        
        # 步骤 8: 发送测试消息
        print(f"\n📤 发送测试消息给 OpenAI...")
        success = await protocol.send_message({
            'message_segment': {
                'type': 'text',
                'data': '你好，请介绍一下你自己'
            }
        })
        
        if success:
            print(f"✅ 消息发送成功")
            
            # 等待接收 OpenAI 的回复
            print(f"\n⏳ 等待 OpenAI 回复...")
            await asyncio.sleep(5)
            
            if handler.messages:
                reply = handler.messages[0].get('message_segment', {}).get('data', '')
                print(f"✅ 收到 OpenAI 回复:")
                print(f"   {reply[:200]}...")
            else:
                print(f"❌ 未收到回复")
        else:
            print(f"❌ 消息发送失败")
        
        # 步骤 9: 断开连接
        print(f"\n🔌 断开连接...")
        await protocol.disconnect()
        print(f"✅ 已断开连接")
        
        # 步骤 10: 清理资源
        await protocol.cleanup()
        print(f"✅ 资源已清理")
        
        print(f"\n✅ 示例 3 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 示例 3 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 示例 4: 使用协议工厂
# ============================================================================

async def example4_protocol_factory():
    """
    示例 4: 使用协议工厂创建协议
    
    展示如何使用 ProtocolFactory 动态创建协议
    """
    print("\n" + "=" * 80)
    print("示例 4: 使用协议工厂创建协议")
    print("=" * 80)
    
    try:
        # 步骤 1: 加载模型配置
        model_config = load_model_config()
        
        # 步骤 2: 转换为协议配置列表
        protocol_configs = load_protocol_configs(model_config)
        print(f"✅ 转换了 {len(protocol_configs)} 个协议配置")
        
        # 步骤 3: 验证配置
        if not validate_protocol_configs(protocol_configs):
            print(f"❌ 协议配置验证失败")
            return False
        
        print(f"✅ 协议配置验证通过")
        
        # 步骤 4: 使用工厂创建协议
        protocols = []
        for config_dict in protocol_configs:
            protocol = ProtocolFactory.create_from_dict(config_dict)
            protocols.append(protocol)
            
            protocol_type = config_dict.get('type')
            print(f"\n✅ 创建 {protocol_type} 协议: {protocol.get_name()}")
        
        # 步骤 5: 获取支持的协议类型
        supported = ProtocolFactory.get_supported_protocols()
        print(f"\n📋 支持的协议类型: {', '.join(supported)}")
        
        # 步骤 6: 检查协议是否支持
        for protocol_type in ['maim', 'openai']:
            is_supported = ProtocolFactory.is_protocol_supported(protocol_type)
            status = "✅ 支持" if is_supported else "❌ 不支持"
            print(f"   {protocol_type}: {status}")
        
        # 步骤 7: 初始化第一个协议
        if protocols:
            protocol = protocols[0]
            print(f"\n📋 初始化 {protocol.get_name()} 协议...")
            
            init_success = await protocol.initialize(protocol_configs[0])
            if init_success:
                print(f"✅ 初始化成功")
            else:
                print(f"❌ 初始化失败")
        
        # 步骤 8: 清理所有协议
        print(f"\n🧹 清理所有协议...")
        for protocol in protocols:
            await protocol.cleanup()
        print(f"✅ 清理完成")
        
        print(f"\n✅ 示例 4 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 示例 4 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 示例 5: 查询模型配置
# ============================================================================

async def example5_query_model_config():
    """
    示例 5: 查询模型配置
    
    展示如何使用配置加载器查询模型配置
    """
    print("\n" + "=" * 80)
    print("示例 5: 查询模型配置")
    print("=" * 80)
    
    try:
        # 步骤 1: 加载模型配置
        model_config = load_model_config()
        print(f"✅ 模型配置加载成功")
        
        # 步骤 2: 查询对话任务配置
        print(f"\n📋 查询 'chat' 任务配置...")
        chat_config = get_model_config_by_task(model_config, 'chat')
        
        if chat_config:
            print(f"✅ 找到对话任务配置:")
            print(f"   默认提供商: {chat_config.get('default_provider', 'N/A')}")
            print(f"   模型列表: {chat_config.get('model_list', [])}")
        else:
            print(f"❌ 未找到对话任务配置")
        
        # 步骤 3: 查询 OpenAI 提供商的所有模型
        print(f"\n📋 查询 OpenAI 提供商的模型...")
        openai_models = get_models_by_provider(model_config, 'openai')
        
        if openai_models:
            print(f"✅ 找到 {len(openai_models)} 个模型:")
            for model in openai_models:
                print(f"   • ID: {model.get('id')}")
                print(f"     名称: {model.get('name')}")
                print(f"     类型: {model.get('model_type')}")
                print(f"     最大 Token: {model.get('max_tokens')}")
        else:
            print(f"❌ 未找到 OpenAI 模型")
        
        # 步骤 4: 根据 ID 查询特定模型
        print(f"\n📋 查询模型 'gpt-3.5-turbo'...")
        model_config_obj = get_model_config(model_config, 'gpt-3.5-turbo')
        
        if model_config_obj:
            print(f"✅ 找到模型配置:")
            print(f"   ID: {model_config_obj.id}")
            print(f"   名称: {model_config_obj.name}")
            print(f"   提供商: {model_config_obj.provider}")
            print(f"   最大 Token: {model_config_obj.max_tokens}")
        else:
            print(f"❌ 未找到模型 'gpt-3.5-turbo'")
        
        # 步骤 5: 列出所有提供商
        print(f"\n📋 列出所有 API 提供商:")
        for provider in model_config.api_providers:
            print(f"   • {provider.name} ({provider.provider_type})")
            print(f"     URL: {provider.url}")
        
        print(f"\n✅ 示例 5 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 示例 5 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 80)
    print("协议使用示例 - 完整演示")
    print("=" * 80)
    print()
    print("本示例演示如何使用新的 model_config.toml 配置系统")
    print("分别展示 Maim 和 OpenAI 协议的使用方法")
    print()
    
    results = []
    
    # 运行示例 1: 使用协议管理器（推荐方式）
    # results.append(("示例1: 协议管理器", await example1_protocol_manager_with_model_config()))
    
    # 运行示例 2: 直接使用 Maim 协议
    # results.append(("示例2: Maim 协议", await example2_maim_protocol()))
    
    # 运行示例 3: 直接使用 OpenAI 协议
    # results.append(("示例3: OpenAI 协议", await example3_openai_protocol()))
    
    # 运行示例 4: 使用协议工厂
    # results.append(("示例4: 协议工厂", await example4_protocol_factory()))
    
    # 运行示例 5: 查询模型配置
    results.append(("示例5: 查询配置", await example5_query_model_config()))
    
    # 总结结果
    print("\n" + "=" * 80)
    print("示例运行结果汇总")
    print("=" * 80)
    
    for name, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 示例成功")
    
    if passed == total:
        print("🎉 所有示例运行成功！")
        return 0
    else:
        print(f"⚠️  有 {total - passed} 个示例失败")
        return 1


if __name__ == "__main__":
    # 运行示例
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
