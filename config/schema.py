"""
配置模式定义
定义三层配置结构：供应商 -> 模型 -> 任务使用
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ===================================================================
# 第一层：API 供应商配置
# ===================================================================

class APIProviderConfig(BaseModel):
    """API 供应商配置"""
    name: str = Field(..., description="供应商名称")
    base_url: str = Field(..., description="API 地址")
    client_type: str = Field("openai", description="客户端类型: maim/openai/gemini")
    api_key: str = Field("", description="API 密钥")
    max_retry: int = Field(2, description="最大重试次数")
    timeout: int = Field(30, description="超时时间(秒)")
    retry_interval: int = Field(5, description="重试间隔(秒)")


# ===================================================================
# 第二层：模型配置
# ===================================================================

class ModelConfig(BaseModel):
    """模型配置"""
    model_identifier: str = Field(..., description="模型标识符")
    name: str = Field(..., description="模型名称")
    api_provider: str = Field(..., description="使用的供应商名称")
    price_in: float = Field(0.0, description="输入价格")
    price_out: float = Field(0.0, description="输出价格")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")


# ===================================================================
# 第三层：任务配置
# ===================================================================

class TaskConfig(BaseModel):
    """任务配置"""
    model_list: List[str] = Field(..., description="使用的模型列表（按优先级排序）")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大输出token数")
    timeout: Optional[int] = Field(None, description="超时时间(秒)，优先级高于供应商配置")


class ModelTaskConfig(BaseModel):
    """模型任务配置组"""
    chat: Optional[TaskConfig] = Field(None, description="对话任务")
    image_recognition: Optional[TaskConfig] = Field(None, description="识图任务")
    tool_use: Optional[TaskConfig] = Field(None, description="工具调用任务")
    voice: Optional[TaskConfig] = Field(None, description="语音识别任务")
    embedding: Optional[TaskConfig] = Field(None, description="文本嵌入任务")
    expression: Optional[TaskConfig] = Field(None, description="表达器任务")
    emotion: Optional[TaskConfig] = Field(None, description="情绪分析任务")
    naming: Optional[TaskConfig] = Field(None, description="取名任务")
    relation: Optional[TaskConfig] = Field(None, description="关系提取任务")
    planner: Optional[TaskConfig] = Field(None, description="决策任务")


# ===================================================================
# 配置文件结构
# ===================================================================

class InnerConfig(BaseModel):
    """内部配置"""
    version: str = Field("1.0.0", description="配置文件版本")


class ModelConfigFile(BaseModel):
    """模型配置文件"""
    inner: InnerConfig = Field(..., description="内部配置")
    api_providers: List[APIProviderConfig] = Field(..., description="API 供应商列表")
    models: List[ModelConfig] = Field(..., description="模型列表")
    model_task_config: ModelTaskConfig = Field(..., description="任务配置")


# ===================================================================
# 主配置（保留原有）
# ===================================================================

class InterfaceConfig(BaseModel):
    """界面配置"""
    scale_factor: float = Field(1.0, description="界面缩放倍率")


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = Field("sqlite", description="数据库类型")
    path: str = Field("data/chat.db", description="数据库路径")


class Live2DConfig(BaseModel):
    """Live2D 配置"""
    enabled: bool = Field(False, description="是否启用 Live2D")
    model_path: Optional[str] = Field(None, description="模型路径")
    model_name: Optional[str] = Field(None, description="模型名称")
    physics_enabled: bool = Field(True, description="是否启用物理模拟")
    render_quality: str = Field("high", description="渲染质量")
    gpu_acceleration: bool = Field(True, description="是否启用 GPU 加速")
    custom_scale: float = Field(1.0, description="自定义缩放")
    custom_offset_x: float = Field(0.0, description="自定义水平偏移")
    custom_offset_y: float = Field(0.0, description="自定义垂直偏移")


class RenderConfig(BaseModel):
    """渲染配置"""
    mode: str = Field("static", description="渲染模式: static/live2d")
    allow_switch: bool = Field(True, description="是否允许运行时切换渲染模式")


class AnimationConfig(BaseModel):
    """动画配置"""
    default_state: str = Field("idle", description="默认动画状态")
    default_expression: str = Field("normal", description="默认表情")
    fps: int = Field(60, description="动画帧率")
    breathing_enabled: bool = Field(True, description="是否启用呼吸效果")


class AnimationSchedulerConfig(BaseModel):
    """动画调度器配置"""
    enabled: bool = Field(True, description="是否启用动画调度器")
    idle_interval_min: float = Field(30.0, description="待机动作最小间隔")
    idle_interval_max: float = Field(90.0, description="待机动作最大间隔")
    random_motion_duration: float = Field(5.0, description="随机动作持续时间")
    group_weights: Dict[str, float] = Field(default_factory=dict, description="动作组权重")
    whitelist: List[str] = Field(default_factory=list, description="动作组白名单")
    blacklist: List[str] = Field(default_factory=list, description="动作组黑名单")


class PerformanceConfig(BaseModel):
    """性能配置"""
    max_fps: int = Field(60, description="最大帧率限制")
    vsync: bool = Field(True, description="是否启用垂直同步")
    texture_cache_size: int = Field(256, description="纹理缓存大小 MB")


class StateConfig(BaseModel):
    """持久化状态配置"""
    window_locked: bool = Field(False, description="窗口是否锁定")
    window_visible: bool = Field(True, description="窗口是否可见")
    console_visible: bool = Field(True, description="终端是否可见")


class PromptConfig(BaseModel):
    """Prompt 拼接配置"""
    persona: str = Field(
        "你活泼、亲切，愿意陪伴用户。回复时尽量简短自然，可以有一点桌面宠物的可爱感，但不要影响信息表达。",
        description="桌宠人设",
    )
    context_limit: int = Field(8, description="拼接最近上下文消息条数")
    context_message_max_chars: int = Field(500, description="单条上下文最大字符数")
    include_time: bool = Field(True, description="是否在 prompt 中拼接当前时间")
    include_context: bool = Field(True, description="是否拼接最近聊天上下文")


class Config(BaseModel):
    """主配置"""
    url: str = Field("ws://127.0.0.1:19000/ws", description="WebSocket 地址")
    Nickname: str = Field("麦麦", description="桌宠昵称")
    userNickname: str = Field("", description="用户昵称")
    platform: str = Field("desktop-pet", description="平台标识")
    hide_console: bool = Field(False, description="是否隐藏终端")
    Screenshot_shortcuts: str = Field("Ctrl+Shift+A", description="截图快捷键")
    allow_multiple_source_conversion: bool = Field(False, description="允许多源转换")
    
    interface: Optional[InterfaceConfig] = Field(None, description="界面配置")
    render: Optional[RenderConfig] = Field(None, description="渲染配置")
    database: Optional[DatabaseConfig] = Field(None, description="数据库配置")
    live2d: Optional[Live2DConfig] = Field(None, description="Live2D 配置")
    animation: Optional[AnimationConfig] = Field(None, description="动画配置")
    animation_scheduler: Optional[AnimationSchedulerConfig] = Field(None, description="动画调度器配置")
    performance: Optional[PerformanceConfig] = Field(None, description="性能配置")
    state: Optional[StateConfig] = Field(None, description="持久化状态配置")
    prompt: Optional[PromptConfig] = Field(None, description="Prompt 拼接配置")
