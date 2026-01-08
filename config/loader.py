"""
配置文件加载器
处理配置文件的加载、验证和自动创建
"""

import os
import sys
import shutil
import tomli
import uuid
from pathlib import Path
from typing import Optional

from .schema import Config
from src.util.logger import logger


# 配置文件路径
CONFIG_FILE = "config.toml"
CONFIG_TEMPLATE = "config/templates/config.toml.template"


def ensure_config_exists() -> bool:
    """
    确保配置文件存在
    
    Returns:
        bool: 配置文件是否已经存在（无需修改）
    
    Raises:
        SystemExit: 如果配置文件不存在，则复制模板并退出程序
    """
    if os.path.exists(CONFIG_FILE):
        logger.info(f"配置文件已存在: {CONFIG_FILE}")
        return True
    
    # 配置文件不存在，复制模板
    logger.warning(f"配置文件不存在: {CONFIG_FILE}")
    logger.info("正在从模板创建配置文件...")
    
    try:
        # 检查模板文件是否存在
        if not os.path.exists(CONFIG_TEMPLATE):
            logger.error(f"配置模板文件不存在: {CONFIG_TEMPLATE}")
            logger.error("请确保程序文件完整，或从 GitHub 重新下载")
            sys.exit(1)
        
        # 复制模板文件
        shutil.copy(CONFIG_TEMPLATE, CONFIG_FILE)
        logger.info(f"✓ 已从模板创建配置文件: {CONFIG_FILE}")
        
        # 显示提示信息
        print("\n" + "=" * 60)
        print("⚠️  配置文件已自动创建")
        print("=" * 60)
        print(f"\n配置文件位置: {os.path.abspath(CONFIG_FILE)}")
        print("\n请根据你的需求修改配置文件，然后重新运行程序。\n")
        print("主要配置项说明：")
        print("  • url: WebSocket 服务器地址（必填）")
        print("  • Nickname: 桌宠昵称")
        print("  • hide_console: 是否隐藏终端窗口")
        print("  • live2d.enabled: 是否启用 Live2D 动画")
        print("  • live2d.model_path: Live2D 模型文件路径")
        print("\n如需了解更多配置选项，请查看配置文件中的详细注释。\n")
        print("=" * 60 + "\n")
        
        # 退出程序，等待用户修改配置
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"创建配置文件失败: {e}", exc_info=True)
        logger.error(f"请手动复制 {CONFIG_TEMPLATE} 为 {CONFIG_FILE} 并修改配置")
        sys.exit(1)


def load_config() -> Config:
    """
    加载配置文件
    
    Returns:
        Config: 配置对象
    
    Raises:
        SystemExit: 如果配置文件加载失败
    """
    # 确保配置文件存在
    ensure_config_exists()
    
    try:
        # 加载 TOML 配置文件
        with open(CONFIG_FILE, "rb") as f:
            config_data = tomli.load(f)
        
        # 验证并创建配置对象
        config = Config(**config_data)
        
        # 处理多源转换（生成唯一平台 ID）
        if config.allow_multiple_source_conversion:
            config.platform = config.platform + "-" + str(uuid.uuid4())
            logger.info(f"多源转换模式已启用，平台 ID: {config.platform}")
        
        logger.info("配置文件加载成功")
        
        return config
        
    except Exception as e:
        logger.error(f"配置文件加载失败: {e}", exc_info=True)
        logger.error(f"请检查 {CONFIG_FILE} 文件格式是否正确")
        sys.exit(1)


def get_scale_factor(config: Config) -> float:
    """
    获取界面缩放倍率
    
    Args:
        config: 配置对象
    
    Returns:
        float: 缩放倍率（范围：0.5 ~ 3.0）
    """
    if config.interface and config.interface.scale_factor is not None:
        scale = float(config.interface.scale_factor)
        # 限制缩放范围在 0.5 到 3.0 之间
        return max(0.5, min(3.0, scale))
    return 1.0


def save_config(config: Config) -> bool:
    """
    保存配置文件
    
    Args:
        config: 配置对象
    
    Returns:
        bool: 是否保存成功
    """
    try:
        import tomli_w
        
        # 将配置对象转换为字典
        config_dict = config.dict()
        
        # 写入配置文件
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            f.write(tomli_w.dumps(config_dict))
        
        logger.info("配置文件保存成功")
        return True
        
    except Exception as e:
        logger.error(f"配置文件保存失败: {e}", exc_info=True)
        return False


def update_config_value(section: Optional[str], key: str, value) -> bool:
    """
    更新配置文件中的单个值
    
    Args:
        section: 配置节（如 'live2d'），如果是 None 则表示根级别
        key: 配置键
        value: 新值
    
    Returns:
        bool: 是否更新成功
    """
    try:
        import tomli
        import tomli_w
        
        # 加载现有配置
        with open(CONFIG_FILE, "rb") as f:
            config_data = tomli.load(f)
        
        # 更新值
        if section:
            if section not in config_data:
                config_data[section] = {}
            config_data[section][key] = value
        else:
            config_data[key] = value
        
        # 保存配置
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            f.write(tomli_w.dumps(config_data))
        
        logger.info(f"配置更新成功: [{section}]{key} = {value}")
        return True
        
    except Exception as e:
        logger.error(f"配置更新失败: {e}", exc_info=True)
        return False

