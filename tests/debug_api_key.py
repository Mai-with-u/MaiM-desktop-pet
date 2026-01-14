"""
调试 API key 加载
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.model_config_loader import load_model_config
from config.protocol_config_loader import load_protocol_configs

def main():
    print("=" * 70)
    print("调试 API Key 加载")
    print("=" * 70)
    
    # 加载模型配置
    print("\n1. 加载 model_config.toml...")
    model_config = load_model_config()
    print(f"✓ 配置文件版本: {model_config.inner.version}")
    
    # 显示所有 API 提供商
    print("\n2. API 提供商列表:")
    for i, provider in enumerate(model_config.api_providers):
        print(f"\n[{i}] {provider.name}")
        print(f"    类型: {provider.client_type}")
        print(f"    Base URL: {provider.base_url}")
        masked_key = provider.api_key[:8] + "..." if provider.api_key and len(provider.api_key) > 8 else "***"
        print(f"    API Key: {masked_key}")
        print(f"    完整 Key: {provider.api_key}")
    
    # 转换为协议配置
    print("\n3. 转换为协议配置:")
    protocol_configs = load_protocol_configs(model_config)
    
    for i, config in enumerate(protocol_configs):
        print(f"\n[{i}] 协议类型: {config.get('type')}")
        if config.get('type') == 'maim':
            print(f"    URL: {config.get('url')}")
            print(f"    Platform: {config.get('platform')}")
            token = config.get('token')
            masked_token = token[:8] + "..." if token and len(token) > 8 else "***"
            print(f"    Token: {masked_token}")
        elif config.get('type') == 'openai':
            api_key = config.get('api_key')
            masked_key = api_key[:8] + "..." if api_key and len(api_key) > 8 else "***"
            print(f"    Base URL: {config.get('base_url')}")
            print(f"    API Key: {masked_key}")
            print(f"    完整 Key: {api_key}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
