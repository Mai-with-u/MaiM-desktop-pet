import tomli
import uuid
from pydantic import BaseModel
from typing import Optional, Dict

class Config(BaseModel):
    url: Optional[str] = None
    Nickname: Optional[str] = None
    userNickname: Optional[str] = None
    platform: str = "desktop-pet"
    hide_console: bool = True
    Screenshot_shortcuts: Optional[str] = None
    allow_multiple_source_conversion: bool = False #多桌宠连接适配，默认为关
    interface: Optional[Dict] = None
    render: Optional[Dict] = None
    live2d: Optional[Dict] = None
    animation: Optional[Dict] = None
    performance: Optional[Dict] = None
    database: Optional[Dict] = None
    state: Optional[Dict] = None
 
 
# 加载 TOML 配置文件
with open("config.toml", "rb") as f:
    config_data = tomli.load(f)

config = Config(**config_data)

# 获取界面缩放倍率，默认为1.0
def get_scale_factor() -> float:
    """获取界面缩放倍率"""
    if config.interface and 'scale_factor' in config.interface:
        scale = float(config.interface['scale_factor'])
        # 限制缩放范围在0.5到3.0之间
        return max(0.5, min(3.0, scale))
    return 1.0

# 全局缩放倍率
scale_factor = get_scale_factor()

if config.allow_multiple_source_conversion:
    config.platform = config.platform + "-" + str(uuid.uuid4())
