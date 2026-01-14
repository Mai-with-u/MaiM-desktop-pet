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

from .schema import Config, ModelConfigFile
from src.util.logger import logger


# 配置文件路径
CONFIG_FILE = "config.toml"
CONFIG_TEMPLATE = "config/templates/config.toml.template"

# 消息层配置文件路径
MODEL_CONFIG_FILE = "model_config.toml"
MODEL_CONFIG_TEMPLATE = "config/templates/model_config.toml.template"


def _ensure_config_file_exists(
    config_file: str,
    template_file: str,
    config_type: str,
    config_description: str,
    config_items: list[str]
) -> bool:
    """
    通用的配置文件存在性检查（内部函数）
    
    Args:
        config_file: 配置文件路径
        template_file: 模板文件路径
        config_type: 配置类型（如"主配置"、"消息层配置"）
        config_description: 配置描述
        config_items: 主要配置项说明列表
    
    Returns:
        bool: 配置文件是否已经存在（无需修改）
    
    Raises:
        SystemExit: 如果配置文件不存在，则复制模板并退出程序
    """
    if os.path.exists(config_file):
        logger.info(f"{config_type}已存在: {config_file}")
        return True
    
    # 配置文件不存在，复制模板
    logger.warning(f"{config_type}不存在: {config_file}")
    logger.info(f"正在从模板创建{config_description}...")
    
    try:
        # 检查模板文件是否存在
        if not os.path.exists(template_file):
            logger.error(f"{config_description}模板文件不存在: {template_file}")
            logger.error("请确保程序文件完整，或从 GitHub 重新下载")
            sys.exit(1)
        
        # 复制模板文件
        shutil.copy(template_file, config_file)
        logger.info(f"✓ 已从模板创建{config_description}: {config_file}")
        
        # 显示提示信息
        print("\n" + "=" * 60)
        print(f"⚠️  {config_description}已自动创建")
        print("=" * 60)
        print(f"\n配置文件位置: {os.path.abspath(config_file)}")
        print(f"\n请根据你的需求修改配置文件，然后重新运行程序。\n")
        print("主要配置项说明：")
        for item in config_items:
            print(f"  • {item}")
        print("\n如需了解更多配置选项，请查看配置文件中的详细注释。\n")
        print("=" * 60 + "\n")
        
        input("按回车键继续...")
        
        # 退出程序，等待用户修改配置
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"创建{config_description}失败: {e}", exc_info=True)
        logger.error(f"请手动复制 {template_file} 为 {config_file} 并修改配置")
        sys.exit(1)


def ensure_config_exists() -> bool:
    """
    确保主配置文件存在
    
    Returns:
        bool: 配置文件是否已经存在（无需修改）
    
    Raises:
        SystemExit: 如果配置文件不存在，则复制模板并退出程序
    """
    return _ensure_config_file_exists(
        config_file=CONFIG_FILE,
        template_file=CONFIG_TEMPLATE,
        config_type="主配置文件",
        config_description="主配置文件",
        config_items=[
            "url: WebSocket 服务器地址（必填）",
            "Nickname: 桌宠昵称",
            "hide_console: 是否隐藏终端窗口",
            "live2d.enabled: 是否启用 Live2D 动画",
            "live2d.model_path: Live2D 模型文件路径"
        ]
    )


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


# ===================================================================
# 消息层配置加载器
# ===================================================================

def ensure_model_config_exists() -> bool:
    """
    确保消息层配置文件存在
    
    Returns:
        bool: 配置文件是否已经存在（无需修改）
    
    Raises:
        SystemExit: 如果配置文件不存在，则复制模板并退出程序
    """
    return _ensure_config_file_exists(
        config_file=MODEL_CONFIG_FILE,
        template_file=MODEL_CONFIG_TEMPLATE,
        config_type="消息层配置文件",
        config_description="消息层配置文件",
        config_items=[
            "api_providers: API 服务提供商配置",
            "models: 可用的模型列表",
            "model_task_config: 不同任务使用的模型配置"
        ]
    )


def load_model_config() -> ModelConfigFile:
    """
    加载消息层配置文件
    
    Returns:
        ModelConfigFile: 消息层配置对象
    
    Raises:
        SystemExit: 如果配置文件加载失败
    """
    # 确保配置文件存在
    ensure_model_config_exists()
    
    try:
        # 加载 TOML 配置文件
        with open(MODEL_CONFIG_FILE, "rb") as f:
            config_data = tomli.load(f)
        
        # 验证并创建配置对象
        config = ModelConfigFile(**config_data)
        
        logger.info(f"消息层配置文件加载成功，版本: {config.inner.version}")
        logger.info(f"  - API 提供商数量: {len(config.api_providers)}")
        logger.info(f"  - 模型数量: {len(config.models)}")
        
        return config
        
    except Exception as e:
        logger.error(f"消息层配置文件加载失败: {e}", exc_info=True)
        logger.error(f"请检查 {MODEL_CONFIG_FILE} 文件格式是否正确")
        sys.exit(1)


def save_model_config(config: ModelConfigFile) -> bool:
    """
    保存消息层配置文件
    
    Args:
        config: 消息层配置对象
    
    Returns:
        bool: 是否保存成功
    """
    try:
        import tomli_w
        
        # 将配置对象转换为字典
        config_dict = config.dict()
        
        # 写入配置文件
        with open(MODEL_CONFIG_FILE, "w", encoding='utf-8') as f:
            f.write(tomli_w.dumps(config_dict))
        
        logger.info("消息层配置文件保存成功")
        return True
        
    except Exception as e:
        logger.error(f"消息层配置文件保存失败: {e}", exc_info=True)
        return False
