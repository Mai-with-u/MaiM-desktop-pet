"""
动画调度器测试脚本
演示如何使用 AnimationScheduler
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_animation_scheduler():
    """测试动画调度器"""
    print("\n" + "=" * 70)
    print("动画调度器测试")
    print("=" * 70 + "\n")
    
    # 创建 QApplication
    app = QApplication(sys.argv)
    
    from src.frontend.core.managers.animation_scheduler import AnimationScheduler
    
    # 测试模型路径
    model_path = "data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json"
    
    # 检查模型文件是否存在
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        print("请先下载 Live2D 模型文件")
        return
    
    print(f"✓ 模型文件存在: {model_path}\n")
    
    try:
        # 创建调度器
        print("1. 创建动画调度器...")
        scheduler = AnimationScheduler(model_path)
        print("✓ 调度器创建成功\n")
        
        # 显示模型信息
        print("2. 模型信息:")
        idle_motions = scheduler.get_idle_motions()
        random_motions = scheduler.get_random_motions()
        print(f"  待机动作: {len(idle_motions)} 个")
        for motion in idle_motions[:3]:  # 只显示前 3 个
            print(f"    - {motion.name} ({motion.duration}s)" if motion.duration else f"    - {motion.name}")
        print(f"  随机动作: {len(random_motions)} 个")
        
        # 按组统计
        from collections import Counter
        groups = Counter(m.group for m in random_motions)
        for group, count in groups.items():
            print(f"    {group}: {count} 个")
        print()
        
        # 配置调度器
        print("3. 配置调度器...")
        scheduler.set_idle_interval(5.0, 10.0)  # 缩短测试时间
        scheduler.set_random_motion_duration(3.0)
        print("✓ 配置完成:")
        print(f"  待机间隔: 5-10 秒（测试用，实际为 30-90 秒）")
        print(f"  随机动作持续时间: 3 秒\n")
        
        # 连接信号
        print("4. 连接信号...")
        scheduler.motion_changed.connect(
            lambda group, file: print(f"📢 动作切换: {group} -> {file.split('/')[-1]}")
        )
        scheduler.state_changed.connect(
            lambda state: print(f"📊 状态切换: {state}")
        )
        print("✓ 信号连接成功\n")
        
        # 启动调度器
        print("5. 启动调度器...")
        scheduler.start()
        print("✓ 调度器已启动\n")
        
        print("6. 观察动画切换（30 秒）...")
        print("   你应该看到动作在待机和随机动作之间自动切换\n")
        
        # 运行 30 秒
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(30000)  # 30 秒后退出
        
        app.exec_()
        
        # 清理
        print("\n7. 清理资源...")
        scheduler.cleanup()
        print("✓ 清理完成\n")
        
        print("=" * 70)
        print("测试完成！")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_scheduler_with_weights():
    """测试带权重的调度器"""
    print("\n" + "=" * 70)
    print("带权重的动画调度器测试")
    print("=" * 70 + "\n")
    
    app = QApplication(sys.argv)
    
    from src.frontend.core.managers.animation_scheduler import AnimationScheduler
    
    model_path = "data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json"
    
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    try:
        scheduler = AnimationScheduler(model_path)
        
        # 设置权重
        print("设置动作组权重...")
        scheduler.set_group_weights({
            "Tap": 2.0,       # 点击动作权重 2.0（更容易被选中）
            "Flick": 1.5,     # 滑动动作权重 1.5
            "Idle": 1.0,       # 待机动作权重 1.0
        })
        print("✓ 权重设置完成\n")
        
        # 配置调度器
        scheduler.set_idle_interval(3.0, 5.0)
        scheduler.set_random_motion_duration(2.0)
        
        # 连接信号
        scheduler.motion_changed.connect(
            lambda group, file: print(f"📢 动作切换: {group} -> {file.split('/')[-1]}")
        )
        
        # 启动调度器
        scheduler.start()
        
        print("观察带权重的随机动作选择（20 秒）...")
        print("Tap 动作应该更频繁出现\n")
        
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(20000)  # 20 秒
        
        app.exec_()
        
        scheduler.cleanup()
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_scheduler_with_whitelist():
    """测试带白名单的调度器"""
    print("\n" + "=" * 70)
    print("带白名单的动画调度器测试")
    print("=" * 70 + "\n")
    
    app = QApplication(sys.argv)
    
    from src.frontend.core.managers.animation_scheduler import AnimationScheduler
    
    model_path = "data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json"
    
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    try:
        scheduler = AnimationScheduler(model_path)
        
        # 设置白名单（只使用 Tap 和 Flick 动作）
        print("设置动作组白名单: Tap, Flick...")
        scheduler.set_group_whitelist(["Tap", "Flick"])
        print("✓ 白名单设置完成\n")
        
        # 配置调度器
        scheduler.set_idle_interval(3.0, 5.0)
        scheduler.set_random_motion_duration(2.0)
        
        # 连接信号
        scheduler.motion_changed.connect(
            lambda group, file: print(f"📢 动作切换: {group} -> {file.split('/')[-1]}")
        )
        
        # 启动调度器
        scheduler.start()
        
        print("观察白名单限制（20 秒）...")
        print("应该只看到 Tap 和 Flick 动作\n")
        
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(20000)  # 20 秒
        
        app.exec_()
        
        scheduler.cleanup()
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Live2D 动画调度器测试套件")
    print("=" * 70 + "\n")
    
    # 运行基础测试
    test_animation_scheduler()
    
    # 运行权重测试
    # test_scheduler_with_weights()
    
    # 运行白名单测试
    # test_scheduler_with_whitelist()
