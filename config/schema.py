"""
配置模式定义
使用 Pydantic 进行配置验证
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class InterfaceConfig(BaseModel):
    """界面配置模型"""
    scale_factor: Optional[float] = 1.0


class RenderConfig(BaseModel):
    """渲染配置模型"""
    mode: Optional[str] = "static"
    allow_switch: Optional[bool] = True


class Live2DConfig(BaseModel):
    """Live2D 配置模型"""
    enabled: Optional[bool] = False
    model_path: Optional[str] = ""
    model_name: Optional[str] = ""
    physics_enabled: Optional[bool] = True
    render_quality: Optional[str] = "medium"
    gpu_acceleration: Optional[bool] = True
    custom_scale: Optional[float] = 0.0
    custom_offset_x: Optional[float] = 0.0
    custom_offset_y: Optional[float] = 0.0


class AnimationConfig(BaseModel):
    """动画配置模型"""
    default_state: Optional[str] = "idle"
    default_expression: Optional[str] = "normal"
    fps: Optional[int] = 60
    breathing_enabled: Optional[bool] = True


class AnimationSchedulerConfig(BaseModel):
    """动画调度器配置模型"""
    enabled: Optional[bool] = True
    idle_interval_min: Optional[float] = 30.0
    idle_interval_max: Optional[float] = 90.0
    random_motion_duration: Optional[float] = 5.0
    group_weights: Optional[dict] = None
    whitelist: Optional[list] = None
    blacklist: Optional[list] = None


class PerformanceConfig(BaseModel):
    """性能配置模型"""
    max_fps: Optional[int] = 60
    vsync: Optional[bool] = True
    texture_cache_size: Optional[int] = 256


class DatabaseConfig(BaseModel):
    """数据库配置模型"""
    type: Optional[str] = "sqlite"
    path: Optional[str] = "data/chat.db"


class ProtocolConfig(BaseModel):
    """单个协议配置模型"""
    type: str  # 协议类型: maim, openai
    # Maim 协议配置
    url: Optional[str] = None
    platform: Optional[str] = "default"
    token: Optional[str] = None
    # OpenAI 协议配置
    api_key: Optional[str] = None
    base_url: Optional[str] = "https://api.openai.com/v1"
    model: Optional[str] = "gpt-3.5-turbo"
    system_prompt: Optional[str] = None


# ===================================================================
# Model Config - 消息层配置模型
# ===================================================================

class InnerConfig(BaseModel):
    """配置文件内部信息"""
    version: str = "1.0.0"


class APIProviderConfig(BaseModel):
    """API 服务提供商配置"""
    name: str  # 服务商名称
    base_url: str  # API 基础地址
    client_type: str = "openai"  # 客户端类型: openai, gemini, maim
    api_key: Optional[str] = None
    max_retry: int = 2
    timeout: int = 30
    retry_interval: int = 10


class ModelConfig(BaseModel):
    """模型配置"""
    model_identifier: str  # 模型标识符
    name: str  # 模型名称
    api_provider: str  # API 提供商名称
    price_in: float = 0.0  # 输入价格
    price_out: float = 0.0  # 输出价格
    force_stream_mode: Optional[bool] = None  # 强制流式输出
    extra_params: Optional[Dict[str, Any]] = None  # 额外参数


class ModelTaskConfig(BaseModel):
    """模型任务配置"""
    model_list: list[str]  # 使用的模型列表
    temperature: Optional[float] = 0.7  # 温度参数
    max_tokens: Optional[int] = 800  # 最大 token 数


class ModelTaskConfigGroup(BaseModel):
    """模型任务配置组"""
    chat: Optional[ModelTaskConfig] = None
    image_recognition: Optional[ModelTaskConfig] = None
    tool_use: Optional[ModelTaskConfig] = None
    voice: Optional[ModelTaskConfig] = None
    embedding: Optional[ModelTaskConfig] = None
    expression: Optional[ModelTaskConfig] = None
    emotion: Optional[ModelTaskConfig] = None
    naming: Optional[ModelTaskConfig] = None
    relation: Optional[ModelTaskConfig] = None
    planner: Optional[ModelTaskConfig] = None


class ModelConfigFile(BaseModel):
    """消息层配置文件模型"""
    inner: InnerConfig = Field(default_factory=lambda: InnerConfig(version="1.0.0"))
    api_providers: list[APIProviderConfig] = Field(default_factory=list)
    models: list[ModelConfig] = Field(default_factory=list)
    model_task_config: Optional[ModelTaskConfigGroup] = None


# ===================================================================
# End of Model Config
# ===================================================================


class StateConfig(BaseModel):
    """状态配置模型"""
    locked: Optional[bool] = False
    position_x: Optional[int] = 100
    position_y: Optional[int] = 100


class Config(BaseModel):
    """主配置模型"""
    
    # 基础配置
    url: Optional[str] = None  # 已废弃，请使用 model_config.toml 中的协议配置
    Nickname: Optional[str] = None
    userNickname: Optional[str] = None
    platform: str = "desktop-pet"  # 已废弃，请使用 model_config.toml 中的协议配置
    hide_console: bool = True
    Screenshot_shortcuts: Optional[str] = None
    allow_multiple_source_conversion: bool = False  # 多桌宠连接适配，默认为关
    
    # 嵌套配置
    interface: Optional[InterfaceConfig] = None
    render: Optional[RenderConfig] = None
    live2d: Optional[Live2DConfig] = None
    animation: Optional[AnimationConfig] = None
    animation_scheduler: Optional[AnimationSchedulerConfig] = None
    performance: Optional[PerformanceConfig] = None
    database: Optional[DatabaseConfig] = None
    state: Optional[StateConfig] = None
    protocols: Optional[list[ProtocolConfig]] = None  # 协议配置列表（已废弃，请使用 model_config.toml）
    
    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True
