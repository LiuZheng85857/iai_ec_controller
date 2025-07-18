"""基本控制命令"""
from typing import Optional
from core.ec_actuator import ECActuator
import time


class BasicCommands:
    """基本命令类"""

    def __init__(self, actuator: ECActuator):
        self.actuator = actuator

    def initialize(self) -> bool:
        """初始化轴（原点复归）"""
        return self.actuator.home()

    def jog_forward(self, duration: Optional[float] = None):
        """点动前进

        Args:
            duration: 持续时间（秒），None表示持续运动
        """
        self.actuator.move_forward()
        if duration:
            time.sleep(duration)
            self.actuator.stop()

    def jog_backward(self, duration: Optional[float] = None):
        """点动后退"""
        self.actuator.move_backward()
        if duration:
            time.sleep(duration)
            self.actuator.stop()

    def move_to_forward_end(self) -> bool:
        """移动到前进端"""
        self.actuator.move_forward()
        result = self.actuator.wait_for_position('forward')
        self.actuator.stop()
        return result

    def move_to_backward_end(self) -> bool:
        """移动到后退端"""
        self.actuator.move_backward()
        result = self.actuator.wait_for_position('backward')
        self.actuator.stop()
        return result

    def emergency_stop(self):
        """紧急停止"""
        self.actuator.stop()

    def reset_errors(self):
        """复位错误"""
        self.actuator.reset_alarm()