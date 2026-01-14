"""
测试聊天管理器的配置加载功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.chat_manager import chat_manager
from config.model_config_loader import (
    load_model_config,
    get_chat_task_config,
    get_model_config,
    get_provider_config
)


def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1: 配置加载")
    print("=" * 60)
    
    try:
        # 加载模型配置
        config = load_model_config()
        print(f"✓ 配置加载成功")
        print(f"  配置版本: {config.inner.version if config.inner else 'N/A'}")
        print(f"  API 提供商数量: {len(config.api_providers) if config.api_providers else 0}")
        print(f"  模型数量: {len(config.models) if config.models else 0}")
        print()
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        print()
        return False


def test_chat_task_config():
    """测试聊天任务配置"""
    print("=" * 60)
    print("测试 2: 聊天任务配置")
    print("=" * 60)
    
    try:
        # 获取聊天任务配置
        chat_config = get_chat_task_config()
        if not chat_config:
            print("✗ 聊天任务配置不存在")
            print()
            return False
        
        print(f"✓ 聊天任务配置加载成功")
        print(f"  模型列表: {chat_config.model_list}")
        print(f"  温度参数: {chat_config.temperature}")
        print(f"  最大 token 数: {chat_config.max_tokens}")
        print()
        return True
    except Exception as e:
        print(f"✗ 聊天任务配置加载失败: {e}")
        print()
        return False


def test_protocol_type_determination():
    """测试协议类型确定"""
    print("=" * 60)
    print("测试 3: 协议类型确定")
    print("=" * 60)
    
    try:
        # 获取聊天任务配置
        chat_config = get_chat_task_config()
        if not chat_config or not chat_config.model_list:
            print("✗ 聊天任务配置不存在或模型列表为空")
            print()
            return False
        
        # 获取第一个模型
        first_model_name = chat_config.model_list[0]
        print(f"第一个模型: {first_model_name}")
        
        # 获取模型配置
        model_config = get_model_config(first_model_name)
        if not model_config:
            print(f"✗ 模型配置未找到: {first_model_name}")
            print()
            return False
        
        print(f"模型标识符: {model_config.model_identifier}")
        print(f"API 提供商: {model_config.api_provider}")
        
        # 获取 API 提供商配置
        provider_config = get_provider_config(model_config.api_provider)
        if not provider_config:
            print(f"✗ API 提供商配置未找到: {model_config.api_provider}")
            print()
            return False
        
        protocol_type = provider_config.client_type.lower()
        print(f"✓ 协议类型: {protocol_type}")
        print(f"  提供商名称: {provider_config.name}")
        print(f"  基础 URL: {provider_config.base_url}")
        print()
        return True
    except Exception as e:
        print(f"✗ 协议类型确定失败: {e}")
        print()
        return False


async def test_chat_manager_initialization():
    """测试聊天管理器初始化"""
    print("=" * 60)
    print("测试 4: 聊天管理器初始化")
    print("=" * 60)
    
    try:
        # 初始化聊天管理器（不指定协议类型，从配置读取）
        success = await chat_manager.initialize()
        if not success:
            print("✗ 聊天管理器初始化失败")
            print()
            return False
        
        print(f"✓ 聊天管理器初始化成功")
        print(f"  协议类型: {chat_manager.get_protocol_type()}")
        print(f"  聊天实现: {chat_manager.get_name()}")
        print(f"  支持的消息类型: {', '.join(chat_manager.get_supported_message_types())}")
        print()
        return True
    except Exception as e:
        print(f"✗ 聊天管理器初始化失败: {e}")
        print()
        return False


def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print("* 聊天管理器配置加载测试")
    print("*" * 60)
    print("\n")
    
    # 运行所有测试
    results = []
    results.append(("配置加载", test_config_loading()))
    results.append(("聊天任务配置", test_chat_task_config()))
    results.append(("协议类型确定", test_protocol_type_determination()))
    results.append(("聊天管理器初始化", asyncio.run(test_chat_manager_initialization())))
    
    # 打印总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print()
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print()
    
    if passed == total:
        print("所有测试通过！")
        return 0
    else:
        print("部分测试失败，请检查日志")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
