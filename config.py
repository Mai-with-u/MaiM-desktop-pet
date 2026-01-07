import tomli
import uuid
from pydantic import BaseModel

class Config(BaseModel):
    url: str = None
    Nickname: str = None
    userNickname: str = None
    platform: str = "desktop-pet"
    hide_console: bool = True
    Screenshot_shortcuts: str = None
    allow_multiple_source_conversion:bool = False #多桌宠连接适配，默认为关
    interface: dict = None
    database: dict = None



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

if config.allow_multiple_source_conversion :
    config.platform = config.platform + "-" + str(uuid.uuid4())
