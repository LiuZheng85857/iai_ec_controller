"""基本运动示例"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rec_controller import RECController
from core.ec_actuator import ECActuator
import time


def basic_motion_example():
    """基本运动控制示例"""
    # 创建控制器
    controller = RECController("192.168.0.1")

    if controller.connect():
        print("连接成功")

        # 创建轴控制实例
        axis = ECActuator(controller, 0, 0)

        # 原点复归
        print("执行原点复归...")
        axis.home()

        # 往复运动3次
        for i in range(3):
            print(f"第{i + 1}次往复运动")

            # 前进
            axis.move_forward()
            axis.wait_for_position('forward')
            axis.stop()
            time.sleep(0.5)

            # 后退
            axis.move_backward()
            axis.wait_for_position('backward')
            axis.stop()
            time.sleep(0.5)

        controller.disconnect()
        print("测试完成")


if __name__ == "__main__":
    basic_motion_example()