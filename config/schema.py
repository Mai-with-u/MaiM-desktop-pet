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
    custom_scale: float = Field(1.0, description="自定义缩放")


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
    database: Optional[DatabaseConfig] = Field(None, description="数据库配置")
    live2d: Optional[Live2DConfig] = Field(None, description="Live2D 配置")