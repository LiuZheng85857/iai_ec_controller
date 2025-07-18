"""状态查询命令"""
from typing import Dict, Optional
from core.rec_controller import RECController
from core.ec_actuator import ECActuator


class StatusCommands:
    """状态查询命令类"""

    def __init__(self, controller: RECController):
        self.controller = controller

    def get_gateway_status(self) -> Optional[Dict]:
        """获取网关状态"""
        return self.controller.read_gateway_status()

    def get_axis_status(self, unit_index: int, axis_index: int) -> Optional[Dict]:
        """获取轴状态"""
        return self.controller.read_axis_status(unit_index, axis_index)

    def get_all_axes_status(self) -> Dict:
        """获取所有轴状态"""
        status = {}
        for unit in range(self.controller.unit_count):
            for axis in range(4):
                key = f"unit{unit}_axis{axis}"
                status[key] = self.get_axis_status(unit, axis)
        return status

    def check_alarm(self, unit_index: int, axis_index: int) -> bool:
        """检查是否有报警"""
        status = self.get_axis_status(unit_index, axis_index)
        return status['alarm'] if status else True

    def check_ready(self, unit_index: int, axis_index: int) -> bool:
        """检查是否准备就绪"""
        status = self.get_axis_status(unit_index, axis_index)
        return status['ready'] if status else False