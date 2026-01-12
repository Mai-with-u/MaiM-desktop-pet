"""
Live2D 模型信息提取工具

该工具用于从 Live2D 模型文件中提取模型支持的动作、状态等信息。
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MotionInfo:
    """动作信息"""
    group: str  # 动作分组名称
    file: str  # 动作文件路径
    name: str  # 动作名称（从文件名提取）
    duration: Optional[float] = None  # 动作持续时间（秒）
    fps: Optional[float] = None  # 帧率
    loop: bool = False  # 是否循环
    sound: Optional[str] = None  # 关联的声音文件


@dataclass
class ParameterInfo:
    """参数信息"""
    id: str  # 参数 ID
    target: str  # 目标类型（Parameter/PartOpacity）
    name: Optional[str] = None  # 参数名称（如果有）


@dataclass
class HitAreaInfo:
    """点击区域信息"""
    id: str  # 区域 ID
    name: str  # 区域名称


@dataclass
class Live2DModelInfo:
    """Live2D 模型信息"""
    model_path: str  # 模型配置文件路径
    version: int  # Live2D 版本
    motions: Dict[str, List[MotionInfo]] = field(default_factory=dict)  # 动作分组
    parameters: List[ParameterInfo] = field(default_factory=list)  # 参数列表
    hit_areas: List[HitAreaInfo] = field(default_factory=list)  # 点击区域
    groups: Dict[str, List[str]] = field(default_factory=dict)  # 参数分组
    
    # 资源文件路径
    moc_file: Optional[str] = None
    texture_files: List[str] = field(default_factory=list)
    physics_file: Optional[str] = None
    pose_file: Optional[str] = None
    display_info_file: Optional[str] = None


class Live2DModelInfoExtractor:
    """Live2D 模型信息提取器"""
    
    def __init__(self, model_path: str):
        """
        初始化提取器
        
        Args:
            model_path: Live2D 模型的 model3.json 文件路径
        """
        self.model_path = model_path
        self.model_dir = os.path.dirname(model_path)
        self.model_info: Optional[Live2DModelInfo] = None
    
    def extract(self) -> Live2DModelInfo:
        """
        提取模型信息
        
        Returns:
            Live2DModelInfo: 模型信息对象
        """
        # 读取模型配置文件
        with open(self.model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        # 创建模型信息对象
        self.model_info = Live2DModelInfo(
            model_path=self.model_path,
            version=model_data.get('Version', 0)
        )
        
        # 提取动作信息
        self._extract_motions(model_data)
        
        # 提取资源文件信息
        self._extract_file_references(model_data)
        
        # 提取参数分组
        self._extract_groups(model_data)
        
        # 提取点击区域
        self._extract_hit_areas(model_data)
        
        return self.model_info
    
    def _extract_motions(self, model_data: dict):
        """提取动作信息"""
        motions_data = model_data.get('FileReferences', {}).get('Motions', {})
        
        for group_name, motion_list in motions_data.items():
            if group_name not in self.model_info.motions:
                self.model_info.motions[group_name] = []
            
            for motion_item in motion_list:
                motion_file = motion_item.get('File', '')
                
                # 提取动作名称
                motion_name = os.path.basename(motion_file).replace('.motion3.json', '')
                
                # 创建动作信息
                motion_info = MotionInfo(
                    group=group_name,
                    file=motion_file,
                    name=motion_name
                )
                
                # 读取动作文件获取详细信息
                full_motion_path = os.path.join(self.model_dir, motion_file)
                if os.path.exists(full_motion_path):
                    self._load_motion_details(full_motion_path, motion_info, motion_item)
                
                self.model_info.motions[group_name].append(motion_info)
    
    def _load_motion_details(self, motion_path: str, motion_info: MotionInfo, motion_item: dict):
        """加载动作详细信息"""
        try:
            with open(motion_path, 'r', encoding='utf-8') as f:
                motion_data = json.load(f)
            
            meta = motion_data.get('Meta', {})
            motion_info.duration = meta.get('Duration')
            motion_info.fps = meta.get('Fps')
            motion_info.loop = meta.get('Loop', False)
            
            # 检查是否有声音文件
            sound = motion_item.get('Sound')
            if sound:
                motion_info.sound = sound
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: 无法读取动作文件 {motion_path}: {e}")
    
    def _extract_file_references(self, model_data: dict):
        """提取资源文件信息"""
        file_refs = model_data.get('FileReferences', {})
        
        # Moc 文件
        self.model_info.moc_file = file_refs.get('Moc')
        
        # 纹理文件
        self.model_info.texture_files = file_refs.get('Textures', [])
        
        # 物理文件
        self.model_info.physics_file = file_refs.get('Physics')
        
        # 姿势文件
        self.model_info.pose_file = file_refs.get('Pose')
        
        # 显示信息文件
        self.model_info.display_info_file = file_refs.get('DisplayInfo')
    
    def _extract_groups(self, model_data: dict):
        """提取参数分组"""
        groups = model_data.get('Groups', [])
        
        for group in groups:
            name = group.get('Name', '')
            ids = group.get('Ids', [])
            
            if name and ids:
                self.model_info.groups[name] = ids
    
    def _extract_hit_areas(self, model_data: dict):
        """提取点击区域"""
        hit_areas = model_data.get('HitAreas', [])
        
        for area in hit_areas:
            area_info = HitAreaInfo(
                id=area.get('Id', ''),
                name=area.get('Name', '')
            )
            self.model_info.hit_areas.append(area_info)
    
    def get_motion_groups(self) -> List[str]:
        """获取所有动作分组"""
        return list(self.model_info.motions.keys())
    
    def get_motions_by_group(self, group: str) -> List[MotionInfo]:
        """获取指定分组的所有动作"""
        return self.model_info.motions.get(group, [])
    
    def get_all_motions(self) -> List[MotionInfo]:
        """获取所有动作"""
        all_motions = []
        for motion_list in self.model_info.motions.values():
            all_motions.extend(motion_list)
        return all_motions
    
    def get_idle_motions(self) -> List[MotionInfo]:
        """获取待机动作"""
        return self.get_motions_by_group('Idle')
    
    def get_tap_motions(self) -> List[MotionInfo]:
        """获取点击动作"""
        return self.get_motions_by_group('Tap')
    
    def get_flick_motions(self) -> List[MotionInfo]:
        """获取滑动动作"""
        return self.get_motions_by_group('Flick')
    
    def print_summary(self):
        """打印模型信息摘要"""
        print(f"\n{'='*60}")
        print(f"Live2D 模型信息")
        print(f"{'='*60}")
        print(f"模型路径: {self.model_info.model_path}")
        print(f"Live2D 版本: {self.model_info.version}")
        print(f"\n动作分组 ({len(self.model_info.motions)} 个):")
        
        for group_name, motion_list in self.model_info.motions.items():
            print(f"  - {group_name}: {len(motion_list)} 个动作")
            for motion in motion_list:
                duration_str = f"{motion.duration:.2f}s" if motion.duration else "未知"
                loop_str = " (循环)" if motion.loop else ""
                print(f"    • {motion.name}: {duration_str}{loop_str}")
        
        print(f"\n参数分组 ({len(self.model_info.groups)} 个):")
        for group_name, param_ids in self.model_info.groups.items():
            print(f"  - {group_name}: {', '.join(param_ids)}")
        
        print(f"\n点击区域 ({len(self.model_info.hit_areas)} 个):")
        for area in self.model_info.hit_areas:
            print(f"  - {area.name} ({area.id})")
        
        print(f"\n资源文件:")
        print(f"  - Moc: {self.model_info.moc_file}")
        print(f"  - 纹理: {len(self.model_info.texture_files)} 个")
        print(f"  - 物理: {self.model_info.physics_file}")
        print(f"  - 姿势: {self.model_info.pose_file}")
        print(f"{'='*60}\n")


def extract_model_info(model_path: str) -> Live2DModelInfo:
    """
    便捷函数：提取模型信息
    
    Args:
        model_path: Live2D 模型的 model3.json 文件路径
        
    Returns:
        Live2DModelInfo: 模型信息对象
    """
    extractor = Live2DModelInfoExtractor(model_path)
    return extractor.extract()


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        # 使用默认模型路径
        model_path = "data/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json"
    
    if not os.path.exists(model_path):
        print(f"错误: 模型文件不存在: {model_path}")
        sys.exit(1)
    
    # 提取并打印模型信息
    extractor = Live2DModelInfoExtractor(model_path)
    model_info = extractor.extract()
    
    # 打印摘要
    extractor.print_summary()
    
    # 示例：获取特定类型的动作
    print("\n待机动作:")
    for motion in extractor.get_idle_motions():
        print(f"  - {motion.name} ({motion.duration}s)")
    
    print("\n点击动作:")
    for motion in extractor.get_tap_motions():
        print(f"  - {motion.name}")
