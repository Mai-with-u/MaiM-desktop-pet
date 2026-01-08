#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置文件测试 - 读取并打印 config.toml 内容
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import tomli
except ImportError:
    print("错误: 需要安装 tomli 库")
    print("请运行: pip install tomli")
    sys.exit(1)


def print_config():
    """读取并打印配置文件"""
    config_path = project_root / "config.toml"
    
    print("=" * 80)
    print("配置文件测试")
    print("=" * 80)
    print()
    
    # 检查配置文件是否存在
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    print(f"✅ 配置文件路径: {config_path}")
    print(f"✅ 配置文件大小: {config_path.stat().st_size} 字节")
    print()
    
    # 读取配置文件
    print("-" * 80)
    print("配置文件内容:")
    print("-" * 80)
    
    try:
        with open(config_path, 'rb') as f:
            config = tomli.load(f)
        
        # 打印完整的配置内容
        import json
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
        print()
        print("-" * 80)
        print("配置解析详情:")
        print("-" * 80)
        
        # 逐节打印配置
        print("\n[1] 基础配置")
        print("-" * 40)
        print(f"  URL: {config.get('url', 'N/A')}")
        print(f"  昵称: {config.get('Nickname', 'N/A')}")
        print(f"  平台: {config.get('platform', 'N/A')}")
        print(f"  隐藏终端: {config.get('hide_console', 'N/A')}")
        print(f"  截图快捷键: {config.get('Screenshot_shortcuts', 'N/A')}")
        
        if 'interface' in config:
            print("\n[2] 界面配置")
            print("-" * 40)
            interface = config['interface']
            print(f"  缩放因子: {interface.get('scale_factor', 'N/A')}")
        
        if 'render' in config:
            print("\n[3] 渲染配置")
            print("-" * 40)
            render = config['render']
            print(f"  渲染模式: {render.get('mode', 'N/A')}")
            print(f"  允许切换: {render.get('allow_switch', 'N/A')}")
        
        if 'live2d' in config:
            print("\n[4] Live2D 配置")
            print("-" * 40)
            live2d = config['live2d']
            print(f"  启用 Live2D: {live2d.get('enabled', 'N/A')}")
            print(f"  模型路径: {live2d.get('model_path', 'N/A')}")
            print(f"  模型名称: {live2d.get('model_name', 'N/A')}")
            print(f"  物理模拟: {live2d.get('physics_enabled', 'N/A')}")
            print(f"  渲染质量: {live2d.get('render_quality', 'N/A')}")
            print(f"  GPU 加速: {live2d.get('gpu_acceleration', 'N/A')}")
            
            # 检查模型文件是否存在
            model_path = live2d.get('model_path', '')
            if model_path:
                model_file = project_root / model_path
                if model_file.exists():
                    print(f"  ✅ 模型文件存在")
                else:
                    print(f"  ❌ 模型文件不存在: {model_file}")
        
        if 'animation' in config:
            print("\n[5] 动画配置")
            print("-" * 40)
            animation = config['animation']
            print(f"  默认状态: {animation.get('default_state', 'N/A')}")
            print(f"  默认表情: {animation.get('default_expression', 'N/A')}")
            print(f"  帧率: {animation.get('fps', 'N/A')} FPS")
            print(f"  呼吸效果: {animation.get('breathing_enabled', 'N/A')}")
        
        if 'performance' in config:
            print("\n[6] 性能配置")
            print("-" * 40)
            performance = config['performance']
            print(f"  最大帧率: {performance.get('max_fps', 'N/A')} FPS")
            print(f"  垂直同步: {performance.get('vsync', 'N/A')}")
            print(f"  纹理缓存: {performance.get('texture_cache_size', 'N/A')} MB")
        
        if 'database' in config:
            print("\n[7] 数据库配置")
            print("-" * 40)
            database = config['database']
            print(f"  数据库类型: {database.get('type', 'N/A')}")
            print(f"  数据库路径: {database.get('path', 'N/A')}")
            
            # 检查数据库文件是否存在
            db_path = project_root / database.get('path', '')
            if db_path.exists():
                print(f"  ✅ 数据库文件存在")
            else:
                print(f"  ⚠️  数据库文件不存在: {db_path}")
        
        if 'state' in config:
            print("\n[8] 状态配置")
            print("-" * 40)
            state = config['state']
            print(f"  窗口锁定: {state.get('window_locked', 'N/A')}")
            print(f"  窗口可见: {state.get('window_visible', 'N/A')}")
            print(f"  终端可见: {state.get('console_visible', 'N/A')}")
        
        print()
        print("-" * 80)
        print("✅ 配置文件解析成功")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 解析配置文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_module():
    """测试 config.py 模块"""
    print("\n" + "=" * 80)
    print("测试 config.py 模块")
    print("=" * 80)
    print()
    
    try:
        from config import config
        
        print("✅ config 模块导入成功")
        print()
        
        # 测试访问配置
        print("-" * 80)
        print("config 对象属性:")
        print("-" * 40)
        print(f"  类型: {type(config)}")
        print(f"  属性数量: {len(dir(config))}")
        print()
        
        # 打印主要配置项
        print("-" * 80)
        print("主要配置项:")
        print("-" * 40)
        
        # 基础配置
        if hasattr(config, 'url'):
            print(f"  URL: {config.url}")
        if hasattr(config, 'Nickname'):
            print(f"  昵称: {config.Nickname}")
        if hasattr(config, 'platform'):
            print(f"  平台: {config.platform}")
        
        # 渲染配置
        if hasattr(config, 'render'):
            print(f"\n  渲染配置:")
            print(f"    mode: {config.render.get('mode', 'N/A')}")
            print(f"    allow_switch: {config.render.get('allow_switch', 'N/A')}")
        
        # Live2D 配置
        if hasattr(config, 'live2d'):
            print(f"\n  Live2D 配置:")
            print(f"    enabled: {config.live2d.get('enabled', 'N/A')}")
            print(f"    model_path: {config.live2d.get('model_path', 'N/A')}")
        
        # 数据库配置
        if hasattr(config, 'database'):
            print(f"\n  数据库配置:")
            print(f"    type: {config.database.get('type', 'N/A')}")
            print(f"    path: {config.database.get('path', 'N/A')}")
        
        print()
        print("-" * 80)
        print("✅ config 模块测试成功")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ config 模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("配置文件测试工具")
    print("=" * 80)
    print()
    
    # 测试 1: 直接读取配置文件
    result1 = print_config()
    
    # 测试 2: 测试 config.py 模块
    result2 = test_config_module()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"配置文件读取: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"config 模块: {'✅ 通过' if result2 else '❌ 失败'}")
    print()
    
    if result1 and result2:
        print("✅ 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())