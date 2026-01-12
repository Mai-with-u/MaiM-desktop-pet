"""
Live2D 模型信息提取工具测试

测试两个 Live2D 模型的信息提取功能：
1. hiyori_pro_zh
2. mao_pro_zh
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.frontend.core.models.live2d_model_info import (
    Live2DModelInfoExtractor,
    extract_model_info
)


def test_hiyori_model():
    """测试 Hiyori 模型"""
    print("\n" + "="*70)
    print("测试 1: Hiyori Pro 模型")
    print("="*70)
    
    model_path = "data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json"
    
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return False
    
    try:
        # 提取模型信息
        extractor = Live2DModelInfoExtractor(model_path)
        model_info = extractor.extract()
        
        # 打印摘要
        extractor.print_summary()
        
        # 测试获取特定类型的动作
        print("\n📋 动作分组统计:")
        for group in extractor.get_motion_groups():
            motions = extractor.get_motions_by_group(group)
            print(f"  • {group}: {len(motions)} 个动作")
        
        print("\n🎵 待机动作:")
        idle_motions = extractor.get_idle_motions()
        if idle_motions:
            for motion in idle_motions[:3]:  # 只显示前3个
                duration_str = f"{motion.duration:.2f}s" if motion.duration else "未知"
                print(f"  • {motion.name} ({duration_str})")
        else:
            print("  • 无待机动作")
        
        print("\n👆 点击动作:")
        tap_motions = extractor.get_tap_motions()
        if tap_motions:
            for motion in tap_motions[:3]:  # 只显示前3个
                print(f"  • {motion.name}")
        else:
            print("  • 无点击动作")
        
        print("\n✅ Hiyori 模型测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ Hiyori 模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mao_model():
    """测试 Mao 模型"""
    print("\n" + "="*70)
    print("测试 2: Mao Pro 模型")
    print("="*70)
    
    model_path = "data/live2d/mao_pro_zh/runtime/mao_pro.model3.json"
    
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return False
    
    try:
        # 提取模型信息
        extractor = Live2DModelInfoExtractor(model_path)
        model_info = extractor.extract()
        
        # 打印摘要
        extractor.print_summary()
        
        # 测试获取特定类型的动作
        print("\n📋 动作分组统计:")
        for group in extractor.get_motion_groups():
            motions = extractor.get_motions_by_group(group)
            print(f"  • {group}: {len(motions)} 个动作")
        
        print("\n🎵 待机动作:")
        idle_motions = extractor.get_idle_motions()
        if idle_motions:
            for motion in idle_motions[:3]:  # 只显示前3个
                duration_str = f"{motion.duration:.2f}s" if motion.duration else "未知"
                print(f"  • {motion.name} ({duration_str})")
        else:
            print("  • 无待机动作")
        
        print("\n👆 点击动作:")
        tap_motions = extractor.get_tap_motions()
        if tap_motions:
            for motion in tap_motions[:3]:  # 只显示前3个
                print(f"  • {motion.name}")
        else:
            print("  • 无点击动作")
        
        print("\n✅ Mao 模型测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ Mao 模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_comparison():
    """对比两个模型的信息"""
    print("\n" + "="*70)
    print("测试 3: 模型对比")
    print("="*70)
    
    hiyori_path = "data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json"
    mao_path = "data/live2d/mao_pro_zh/runtime/mao_pro.model3.json"
    
    if not os.path.exists(hiyori_path) or not os.path.exists(mao_path):
        print("❌ 模型文件不存在")
        return False
    
    try:
        # 提取两个模型的信息
        hiyori_extractor = Live2DModelInfoExtractor(hiyori_path)
        mao_extractor = Live2DModelInfoExtractor(mao_path)
        
        hiyori_info = hiyori_extractor.extract()
        mao_info = mao_extractor.extract()
        
        # 计算总动作数
        hiyori_total = len(hiyori_extractor.get_all_motions())
        mao_total = len(mao_extractor.get_all_motions())
        
        # 对比信息
        print(f"\n📊 模型对比:")
        print(f"  {'项目':<20} {'Hiyori':<15} {'Mao':<15}")
        print(f"  {'-'*20} {'-'*15} {'-'*15}")
        print(f"  {'Live2D 版本':<20} {hiyori_info.version:<15} {mao_info.version:<15}")
        print(f"  {'动作分组数':<20} {len(hiyori_info.motions):<15} {len(mao_info.motions):<15}")
        print(f"  {'总动作数':<20} {hiyori_total:<15} {mao_total:<15}")
        print(f"  {'点击区域数':<20} {len(hiyori_info.hit_areas):<15} {len(mao_info.hit_areas):<15}")
        print(f"  {'参数分组数':<20} {len(hiyori_info.groups):<15} {len(mao_info.groups):<15}")
        
        # 对比动作分组
        print(f"\n📋 动作分组对比:")
        hiyori_groups = set(hiyori_info.motions.keys())
        mao_groups = set(mao_info.motions.keys())
        
        common_groups = hiyori_groups & mao_groups
        hiyori_only = hiyori_groups - mao_groups
        mao_only = mao_groups - hiyori_groups
        
        print(f"  共有分组: {', '.join(common_groups)}")
        if hiyori_only:
            print(f"  Hiyori 独有: {', '.join(hiyori_only)}")
        if mao_only:
            print(f"  Mao 独有: {', '.join(mao_only)}")
        
        print("\n✅ 模型对比测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 模型对比测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("Live2D 模型信息提取工具 - 综合测试")
    print("="*70)
    
    results = []
    
    # 测试 1: Hiyori 模型
    results.append(("Hiyori 模型", test_hiyori_model()))
    
    # 测试 2: Mao 模型
    results.append(("Mao 模型", test_mao_model()))
    
    # 测试 3: 模型对比
    results.append(("模型对比", test_comparison()))
    
    # 打印测试结果汇总
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
