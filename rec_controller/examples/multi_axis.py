"""多轴控制示例"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rec_controller import RECController
from core.ec_actuator import ECActuator
import threading
import time


def control_axis(axis: ECActuator, axis_name: str):
    """控制单个轴"""
    print(f"{axis_name}: 开始原点复归...")
    axis.home()
    print(f"{axis_name}: 原点复归完成")

    # 执行3次往复运动
    for i in range(3):
        print(f"{axis_name}: 第{i + 1}次往复")
        axis.move_forward()
        axis.wait_for_position('forward')
        axis.stop()

        time.sleep(0.5)

        axis.move_backward()
        axis.wait_for_position('backward')
        axis.stop()

        time.sleep(0.5)


def multi_axis_example():
    """多轴控制示例"""
    # 创建控制器
    controller = RECController("192.168.0.1", unit_count=1)

    if controller.connect():
        print("连接成功")

        # 创建多个轴
        axes = [
            ECActuator(controller, 0, 0),
            ECActuator(controller, 0, 1),
            ECActuator(controller, 0, 2),
            ECActuator(controller, 0, 3),
        ]

        # 创建线程列表
        threads = []

        # 为每个轴创建控制线程
        for i, axis in enumerate(axes):
            thread = threading.Thread(
                target=control_axis,
                args=(axis, f"轴{i}")
            )
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        controller.disconnect()
        print("多轴控制测试完成")


if __name__ == "__main__":
    multi_axis_example()