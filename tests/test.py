import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import load_config, get_scale_factor

# 加载配置
config = load_config()
scale_factor = get_scale_factor(config)

# 读取 Live2D 模型路径
model_path = config.live2d.get('model_path', '')
print(f"Live2D 模型路径: {model_path}")

# 也可以读取其他配置
print(f"\n=== 配置信息 ===")
print(f"渲染模式: {config.render.get('mode', 'N/A')}")
print(f"启用 Live2D: {config.live2d.get('enabled', 'N/A')}")
print(f"模型名称: {config.live2d.get('model_name', 'N/A')}")
print(f"界面缩放: {scale_factor}")

# 直接访问配置属性
print(f"\n=== 直接访问属性 ===")
print(f"URL: {config.url}")
print(f"昵称: {config.Nickname}")
print(f"平台: {config.platform}")

# 读取嵌套配置
print(f"\n=== 嵌套配置示例 ===")
if config.interface:
    print(f"界面缩放因子: {config.interface.get('scale_factor', 'N/A')}")

if config.render:
    print(f"渲染模式: {config.render.get('mode', 'N/A')}")
    print(f"允许切换: {config.render.get('allow_switch', 'N/A')}")

if config.live2d:
    print(f"Live2D 启用: {config.live2d.get('enabled', 'N/A')}")
    print(f"Live2D 模型路径: {config.live2d.get('model_path', 'N/A')}")
    print(f"渲染质量: {config.live2d.get('render_quality', 'N/A')}")

if config.database:
    print(f"数据库类型: {config.database.get('type', 'N/A')}")
    print(f"数据库路径: {config.database.get('path', 'N/A')}")

if config.performance:
    print(f"最大帧率: {config.performance.get('max_fps', 'N/A')} FPS")
    print(f"纹理缓存: {config.performance.get('texture_cache_size', 'N/A')} MB")
