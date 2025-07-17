"""
数据验证工具
"""
from typing import Dict, Any
from loguru import logger


class Validator:
    """参数验证器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化验证器

        Args:
            config: 配置字典
        """
        self.config = config
        self.max_rotation = config['controller']['max_rotation']

        # 根据型号设置速度限制
        model = config['controller']['model']
        if model == 'EC-RTC9':
            self.max_speed = 600
            self.max_acceleration = 0.5
        elif model == 'EC-RTC12':
            self.max_speed = 600
            self.max_acceleration = 0.7
        else:
            self.max_speed = 500
            self.max_acceleration = 0.5

    def validate_position(self, position: float) -> bool:
        """
        验证位置参数

        Args:
            position: 位置值（度）

        Returns:
            bool: 有效返回True
        """
        if 0 <= position <= self.max_rotation:
            return True
        else:
            logger.error(f"位置 {position} 超出范围 [0, {self.max_rotation}]")
            return False

    def validate_speed(self, speed: float) -> bool:
        """
        验证速度参数

        Args:
            speed: 速度值（度/秒）

        Returns:
            bool: 有效返回True
        """
        if 20 <= speed <= self.max_speed:
            return True
        else:
            logger.error(f"速度 {speed} 超出范围 [20, {self.max_speed}]")
            return False

    def validate_acceleration(self, acceleration: float) -> bool:
        """
        验证加速度参数

        Args:
            acceleration: 加速度值（G）

        Returns:
            bool: 有效返回True
        """
        if 0.1 <= acceleration <= self.max_acceleration:
            return True
        else:
            logger.error(f"加速度 {acceleration} 超出范围 [0.1, {self.max_acceleration}]")
            return False