"""位置控制示例"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rec_controller import RECController
from core.ec_actuator import ECActuator
from commands.position_commands import PositionCommands
import time


def position_control_example():
    """位置控制示例"""
    # 创建控制器
    controller = RECController("192.168.0.1")

    if controller.connect():
        print("连接成功")

        # 创建轴控制实例
        axis = ECActuator(controller, 0, 0)
        commands = PositionCommands(axis)

        # 原点复归
        print("执行原点复归...")
        axis.home()

        # 执行位置序列
        sequence = [
            ('forward', 1.0),  # 前进端，停留1秒
            ('backward', 0.5),  # 后退端，停留0.5秒
            ('forward', 0.5),  # 前进端，停留0.5秒
            ('backward', 1.0),  # 后退端，停留1秒
        ]

        print("执行位置序列...")
        if commands.move_sequence(sequence):
            print("序列执行完成")
        else:
            print("序列执行失败")

        controller.disconnect()
        print("测试完成")


if __name__ == "__main__":
    position_control_example()