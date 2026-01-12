"""
Live2D 动画调度器
负责管理 Live2D 模型的动画播放调度，实现随机动作切换
"""

import random
import time
import logging
from typing import Optional, List, Dict, Set
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from ..models.live2d_model_info import (
    Live2DModelInfoExtractor,
    MotionInfo,
    Live2DModelInfo
)

logger = logging.getLogger(__name__)


class AnimationScheduler(QObject):
    """
    Live2D 动画调度器
    
    功能：
    1. 定时播放待机动作
    2. 随机时间后执行其他动作
    3. 支持动作组权重配置
    4. 支持动作组白名单和黑名单
    """
    
    # 信号：动作改变
    motion_changed = pyqtSignal(str, str)  # (group_name, motion_file)
    
    # 信号：状态改变
    state_changed = pyqtSignal(str)  # "idle" | "random_motion"
    
    def __init__(self, model_path: str, 
                 idle_interval_min: float = 30.0,
                 idle_interval_max: float = 90.0,
                 random_motion_duration: float = 5.0,
                 group_weights: Optional[Dict[str, float]] = None,
                 whitelist: Optional[List[str]] = None,
                 blacklist: Optional[List[str]] = None,
                 enabled: bool = True,
                 parent=None):
        """
        初始化动画调度器
        
        Args:
            model_path: Live2D 模型文件路径
            idle_interval_min: 待机动作最小间隔（秒）
            idle_interval_max: 待机动作最大间隔（秒）
            random_motion_duration: 随机动作持续时间（秒）
            group_weights: 动作组权重字典
            whitelist: 动作组白名单
            blacklist: 动作组黑名单
            enabled: 是否启用调度器
            parent: 父对象
        """
        super().__init__(parent)
        
        self.model_path = model_path
        self.extractor: Optional[Live2DModelInfoExtractor] = None
        self.model_info: Optional[Live2DModelInfo] = None
        
        # 待机动作列表
        self.idle_motions: List[MotionInfo] = []
        # 可用的随机动作列表（不包括待机动作）
        self.random_motions: List[MotionInfo] = []
        
        # 定时器
        self.idle_timer: Optional[QTimer] = None
        self.random_motion_timer: Optional[QTimer] = None
        
        # 当前状态
        self._current_state = "idle"  # "idle" | "random_motion"
        
        # 配置参数（从构造函数参数初始化）
        self.idle_interval_min = idle_interval_min
        self.idle_interval_max = idle_interval_max
        self.random_motion_duration = random_motion_duration
        
        # 动作组权重（用于随机选择）
        self.group_weights: Dict[str, float] = group_weights if group_weights else {}
        
        # 动作组白名单和黑名单
        self.group_whitelist: Optional[Set[str]] = set(whitelist) if whitelist else None
        self.group_blacklist: Optional[Set[str]] = set(blacklist) if blacklist else None
        
        # 是否启用调度器
        self._enabled = enabled
        
        # 加载模型信息
        self._load_model_info()
    
    def _load_model_info(self):
        """加载模型信息"""
        try:
            self.extractor = Live2DModelInfoExtractor(self.model_path)
            self.model_info = self.extractor.extract()
            
            # 提取待机动作
            self.idle_motions = self.extractor.get_idle_motions()
            
            # 提取所有动作，然后过滤掉待机动作
            all_motions = self.extractor.get_all_motions()
            idle_motion_names = {m.name for m in self.idle_motions}
            self.random_motions = [m for m in all_motions if m.name not in idle_motion_names]
            
            logger.info(f"模型信息加载成功:")
            logger.info(f"  待机动作: {len(self.idle_motions)} 个")
            logger.info(f"  随机动作: {len(self.random_motions)} 个")
            
        except Exception as e:
            logger.error(f"加载模型信息失败: {e}")
            raise
    
    def set_idle_interval(self, min_seconds: float, max_seconds: float):
        """
        设置待机动作间隔
        
        Args:
            min_seconds: 最小间隔（秒）
            max_seconds: 最大间隔（秒）
        """
        if min_seconds <= 0 or max_seconds <= 0:
            raise ValueError("间隔时间必须大于 0")
        
        if min_seconds >= max_seconds:
            raise ValueError("最小间隔必须小于最大间隔")
        
        self.idle_interval_min = min_seconds
        self.idle_interval_max = max_seconds
        logger.info(f"待机动作间隔设置为: {min_seconds}-{max_seconds} 秒")
    
    def set_random_motion_duration(self, seconds: float):
        """
        设置随机动作持续时间
        
        Args:
            seconds: 持续时间（秒）
        """
        if seconds <= 0:
            raise ValueError("持续时间必须大于 0")
        
        self.random_motion_duration = seconds
        logger.info(f"随机动作持续时间设置为: {seconds} 秒")
    
    def set_group_weights(self, weights: Dict[str, float]):
        """
        设置动作组权重（用于随机选择）
        
        Args:
            weights: 动作组名称到权重的映射
                     权重越大，被选中的概率越高
        """
        self.group_weights = weights
        logger.info(f"动作组权重已更新: {weights}")
    
    def set_group_whitelist(self, groups: List[str]):
        """
        设置动作组白名单（只使用这些组中的动作）
        
        Args:
            groups: 动作组名称列表
        """
        if groups:
            self.group_whitelist = set(groups)
            self.group_blacklist = None  # 清空黑名单
            logger.info(f"动作组白名单: {groups}")
        else:
            self.group_whitelist = None
            logger.info("已清空动作组白名单")
    
    def set_group_blacklist(self, groups: List[str]):
        """
        设置动作组黑名单（不使用这些组中的动作）
        
        Args:
            groups: 动作组名称列表
        """
        if groups:
            self.group_blacklist = set(groups)
            self.group_whitelist = None  # 清空白名单
            logger.info(f"动作组黑名单: {groups}")
        else:
            self.group_blacklist = None
            logger.info("已清空动作组黑名单")
    
    def set_enabled(self, enabled: bool):
        """
        启用或禁用调度器
        
        Args:
            enabled: 是否启用
        """
        self._enabled = enabled
        
        if enabled:
            logger.info("动画调度器已启用")
            if not self.idle_timer or not self.idle_timer.isActive():
                self.start()
        else:
            logger.info("动画调度器已禁用")
            self.stop()
    
    def is_enabled(self) -> bool:
        """返回调度器是否启用"""
        return self._enabled
    
    def start(self):
        """启动调度器"""
        if not self._enabled:
            logger.warning("调度器已禁用，无法启动")
            return
        
        if self.idle_timer is None:
            self.idle_timer = QTimer(self)
            self.idle_timer.setSingleShot(True)
            self.idle_timer.timeout.connect(self._on_idle_timeout)
        
        if self.random_motion_timer is None:
            self.random_motion_timer = QTimer(self)
            self.random_motion_timer.setSingleShot(True)
            self.random_motion_timer.timeout.connect(self._on_random_motion_timeout)
        
        # 立即播放一个待机动作
        self._play_idle_motion()
        
        # 启动待机定时器
        self._schedule_idle_motion()
        
        logger.info("动画调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.idle_timer:
            self.idle_timer.stop()
        
        if self.random_motion_timer:
            self.random_motion_timer.stop()
        
        logger.info("动画调度器已停止")
    
    def _schedule_idle_motion(self):
        """调度下一个待机动作"""
        if not self._enabled:
            return
        
        # 随机选择间隔时间
        interval = random.uniform(self.idle_interval_min, self.idle_interval_max)
        
        logger.debug(f"将在 {interval:.1f} 秒后切换随机动作")
        
        # 启动定时器（转换为毫秒）
        if self.idle_timer:
            self.idle_timer.start(int(interval * 1000))
    
    def _schedule_random_motion(self):
        """调度随机动作"""
        if not self._enabled:
            return
        
        logger.debug(f"将在 {self.random_motion_duration} 秒后返回待机动作")
        
        # 启动定时器（转换为毫秒）
        if self.random_motion_timer:
            self.random_motion_timer.start(int(self.random_motion_duration * 1000))
    
    def _play_idle_motion(self):
        """播放待机动作"""
        if not self.idle_motions:
            logger.warning("没有可用的待机动作")
            return
        
        # 随机选择一个待机动作
        motion = random.choice(self.idle_motions)
        
        logger.debug(f"播放待机动作: {motion.name}")
        
        # 发射信号
        self.motion_changed.emit(motion.group, motion.file)
        
        # 更新状态
        self._current_state = "idle"
        self.state_changed.emit("idle")
    
    def _play_random_motion(self):
        """播放随机动作"""
        if not self.random_motions:
            logger.warning("没有可用的随机动作")
            return
        
        # 过滤动作（根据白名单和黑名单）
        filtered_motions = self._filter_motions(self.random_motions)
        
        if not filtered_motions:
            logger.warning("过滤后没有可用的随机动作")
            return
        
        # 根据权重选择动作
        motion = self._select_motion_by_weight(filtered_motions)
        
        logger.debug(f"播放随机动作: {motion.name} (组: {motion.group})")
        
        # 发射信号
        self.motion_changed.emit(motion.group, motion.file)
        
        # 更新状态
        self._current_state = "random_motion"
        self.state_changed.emit("random_motion")
    
    def _filter_motions(self, motions: List[MotionInfo]) -> List[MotionInfo]:
        """
        根据白名单和黑名单过滤动作
        
        Args:
            motions: 动作列表
            
        Returns:
            过滤后的动作列表
        """
        # 如果有白名单，只保留白名单中的动作
        if self.group_whitelist:
            return [m for m in motions if m.group in self.group_whitelist]
        
        # 如果有黑名单，排除黑名单中的动作
        if self.group_blacklist:
            return [m for m in motions if m.group not in self.group_blacklist]
        
        # 没有过滤条件，返回所有动作
        return motions
    
    def _select_motion_by_weight(self, motions: List[MotionInfo]) -> MotionInfo:
        """
        根据权重选择动作
        
        Args:
            motions: 动作列表
            
        Returns:
            选中的动作
        """
        # 如果没有设置权重，随机选择
        if not self.group_weights:
            return random.choice(motions)
        
        # 计算每个动作的权重
        weights = []
        for motion in motions:
            weight = self.group_weights.get(motion.group, 1.0)
            weights.append(weight)
        
        # 根据权重选择
        return random.choices(motions, weights=weights, k=1)[0]
    
    def _on_idle_timeout(self):
        """待机定时器超时回调"""
        logger.debug("待机时间到，切换到随机动作")
        
        # 播放随机动作
        self._play_random_motion()
        
        # 调度返回待机动作
        self._schedule_random_motion()
    
    def _on_random_motion_timeout(self):
        """随机动作定时器超时回调"""
        logger.debug("随机动作结束，返回待机动作")
        
        # 播放待机动作
        self._play_idle_motion()
        
        # 调度下一个随机动作
        self._schedule_idle_motion()
    
    def trigger_idle_now(self):
        """立即切换到待机动作"""
        logger.debug("立即切换到待机动作")
        
        # 停止所有定时器
        if self.idle_timer:
            self.idle_timer.stop()
        if self.random_motion_timer:
            self.random_motion_timer.stop()
        
        # 播放待机动作
        self._play_idle_motion()
        
        # 重新调度
        self._schedule_idle_motion()
    
    def trigger_random_motion_now(self):
        """立即播放随机动作"""
        logger.debug("立即播放随机动作")
        
        # 停止所有定时器
        if self.idle_timer:
            self.idle_timer.stop()
        if self.random_motion_timer:
            self.random_motion_timer.stop()
        
        # 播放随机动作
        self._play_random_motion()
        
        # 调度返回待机动作
        self._schedule_random_motion()
    
    def get_current_state(self) -> str:
        """获取当前状态"""
        return self._current_state
    
    def get_idle_motions(self) -> List[MotionInfo]:
        """获取待机动作列表"""
        return self.idle_motions.copy()
    
    def get_random_motions(self) -> List[MotionInfo]:
        """获取随机动作列表"""
        return self.random_motions.copy()
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        
        if self.idle_timer:
            self.idle_timer.deleteLater()
            self.idle_timer = None
        
        if self.random_motion_timer:
            self.random_motion_timer.deleteLater()
            self.random_motion_timer = None
        
        logger.info("动画调度器已清理")
