"""位置控制命令"""
from typing import List, Tuple
from core.ec_actuator import ECActuator
import time


class PositionCommands:
    """位置控制命令类"""

    def __init__(self, actuator: ECActuator):
        self.actuator = actuator
        self.positions = {
            'home': 0.0,
            'forward_end': 100.0,  # 根据实际行程设置
            'backward_end': 0.0
        }

    def set_position(self, name: str, value: float):
        """设置位置点"""
        self.positions[name] = value

    def get_position(self, name: str) -> float:
        """获取位置点"""
        return self.positions.get(name, 0.0)

    def cycle_motion(self, cycles: int = 1, dwell_time: float = 0.5) -> bool:
        """往复运动

        Args:
            cycles: 循环次数
            dwell_time: 停留时间（秒）

        Returns:
            是否成功完成所有循环
        """
        for i in range(cycles):
            # 前进
            if not self.actuator.move_forward():
                return False
            if not self.actuator.wait_for_position('forward'):
                return False
            self.actuator.stop()
            time.sleep(dwell_time)

            # 后退
            if not self.actuator.move_backward():
                return False
            if not self.actuator.wait_for_position('backward'):
                return False
            self.actuator.stop()
            time.sleep(dwell_time)

        return True

    def move_sequence(self, sequence: List[Tuple[str, float]]) -> bool:
        """按序列移动

        Args:
            sequence: 移动序列 [(位置, 停留时间), ...]

        Returns:
            是否成功完成序列
        """
        for position, dwell in sequence:
            if position == 'forward':
                success = self.actuator.move_forward() and \
                          self.actuator.wait_for_position('forward')
            elif position == 'backward':
                success = self.actuator.move_backward() and \
                          self.actuator.wait_for_position('backward')
            else:
                success = False

            if not success:
                return False

            self.actuator.stop()
            time.sleep(dwell)

        return True