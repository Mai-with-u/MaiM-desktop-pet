#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试配置系统
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("测试1: 导入配置模块...")
    from config import load_config, get_scale_factor, Config
    print("✓ 配置模块导入成功")
    
    print("\n测试2: 加载配置文件...")
    config = load_config()
    print("✓ 配置文件加载成功")
    
    print("\n测试3: 获取缩放倍率...")
    scale_factor = get_scale_factor(config)
    print(f"✓ 缩放倍率: {scale_factor}")
    
    print("\n测试4: 访问配置属性...")
    print(f"  URL: {config.url}")
    print(f"  昵称: {config.Nickname}")
    print(f"  平台: {config.platform}")
    print(f"  渲染模式: {config.render.mode if config.render else 'N/A'}")
    print(f"  Live2D 启用: {config.live2d.enabled if config.live2d else 'N/A'}")
    print("✓ 配置属性访问成功")
    
    print("\n" + "=" * 50)
    print("✓ 所有测试通过！配置系统工作正常")
    print("=" * 50)
    
except ImportError as e:
    print(f"\n✗ 导入错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)