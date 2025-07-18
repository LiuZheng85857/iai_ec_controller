"""EC电缸控制类"""
import time
from typing import Optional
from .rec_controller import RECController


class ECActuator:
    """EC电缸控制类"""

    def __init__(self, controller: RECController, unit_index: int, axis_index: int):
        self.controller = controller
        self.unit_index = unit_index
        self.axis_index = axis_index

    def home(self, timeout: float = 30.0) -> bool:
        """执行原点复归

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否成功完成原点复归
        """
        # 发送原点复归命令(ST0或ST1都可以)
        self.controller.send_axis_command(self.unit_index, self.axis_index, 'ST0', True)

        # 等待原点复归完成
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.controller.read_axis_status(self.unit_index, self.axis_index)
            if status and (status['ls0_pe0'] or status['ls1_pe1']):
                # 停止命令
                self.controller.send_axis_command(self.unit_index, self.axis_index, 'ST0', False)
                return True
            time.sleep(0.1)

        # 超时停止
        self.controller.send_axis_command(self.unit_index, self.axis_index, 'ST0', False)
        return False

    def move_forward(self) -> bool:
        """前进到前进端"""
        return self.controller.send_axis_command(self.unit_index, self.axis_index, 'ST1', True)

    def move_backward(self) -> bool:
        """后退到后退端"""
        return self.controller.send_axis_command(self.unit_index, self.axis_index, 'ST0', True)

    def stop(self):
        """停止运动"""
        self.controller.send_axis_command(self.unit_index, self.axis_index, 'ST0', False)
        self.controller.send_axis_command(self.unit_index, self.axis_index, 'ST1', False)

    def reset_alarm(self):
        """复位报警"""
        self.controller.send_axis_command(self.unit_index, self.axis_index, 'RES', True)
        time.sleep(0.1)
        self.controller.send_axis_command(self.unit_index, self.axis_index, 'RES', False)

    def wait_for_position(self, position: str, timeout: float = 10.0) -> bool:
        """等待到达指定位置

        Args:
            position: 'forward' 或 'backward'
            timeout: 超时时间

        Returns:
            是否成功到达位置
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.controller.read_axis_status(self.unit_index, self.axis_index)
            if status:
                if position == 'forward' and status['ls1_pe1']:
                    return True
                elif position == 'backward' and status['ls0_pe0']:
                    return True
            time.sleep(0.05)
        return False

    def get_status(self) -> Optional[dict]:
        """获取当前状态"""
        return self.controller.read_axis_status(self.unit_index, self.axis_index)