"""
测试配置加载功能
验证自定义缩放和偏移参数是否能正确加载
"""

from config import load_config

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置加载功能")
    print("=" * 60)
    
    try:
        # 加载配置
        config = load_config()
        
        print("\n✓ 配置文件加载成功\n")
        
        # 显示基础配置
        print("基础配置:")
        print(f"  URL: {config.url}")
        print(f"  昵称: {config.Nickname}")
        print(f"  平台: {config.platform}")
        print()
        
        # 显示渲染配置
        print("渲染配置:")
        if config.render:
            print(f"  模式: {config.render.mode}")
            print(f"  允许切换: {config.render.allow_switch}")
        else:
            print("  (未配置)")
        print()
        
        # 显示 Live2D 配置
        print("Live2D 配置:")
        if config.live2d:
            print(f"  启用: {config.live2d.enabled}")
            print(f"  模型路径: {config.live2d.model_path}")
            print(f"  模型名称: {config.live2d.model_name}")
            print(f"  物理模拟: {config.live2d.physics_enabled}")
            print(f"  渲染质量: {config.live2d.render_quality}")
            print(f"  GPU 加速: {config.live2d.gpu_acceleration}")
            print(f"  自定义缩放: {config.live2d.custom_scale}")
            print(f"  自定义偏移 X: {config.live2d.custom_offset_x}")
            print(f"  自定义偏移 Y: {config.live2d.custom_offset_y}")
        else:
            print("  (未配置)")
        print()
        
        # 验证自定义参数是否正确加载
        print("验证自定义参数:")
        if config.live2d:
            if config.live2d.custom_scale is not None:
                print(f"  ✓ custom_scale = {config.live2d.custom_scale}")
            else:
                print(f"  ✗ custom_scale 未正确加载")
            
            if config.live2d.custom_offset_x is not None:
                print(f"  ✓ custom_offset_x = {config.live2d.custom_offset_x}")
            else:
                print(f"  ✗ custom_offset_x 未正确加载")
            
            if config.live2d.custom_offset_y is not None:
                print(f"  ✓ custom_offset_y = {config.live2d.custom_offset_y}")
            else:
                print(f"  ✗ custom_offset_y 未正确加载")
        else:
            print("  ✗ Live2D 配置未加载")
        print()
        
        # 显示动画配置
        print("动画配置:")
        if config.animation:
            print(f"  默认状态: {config.animation.default_state}")
            print(f"  默认表情: {config.animation.default_expression}")
            print(f"  帧率: {config.animation.fps}")
            print(f"  呼吸效果: {config.animation.breathing_enabled}")
        else:
            print("  (未配置)")
        print()
        
        print("=" * 60)
        print("配置加载测试完成")
        print("=" * 60)
        
        return config
        
    except Exception as e:
        print(f"\n✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_config_loading()