"""
运动控制命令模块
"""
from typing import List, Optional
from loguru import logger


class MotionCommands:
    """运动控制命令类"""

    def __init__(self, controller):
        """
        初始化运动命令

        Args:
            controller: EC控制器实例
        """
        self.controller = controller

    def jog_forward(self, speed: float = 30.0) -> bool:
        """
        正向点动

        Args:
            speed: 点动速度（度/秒）
        """
        logger.info(f"正向点动，速度: {speed}度/秒")

        # 设置速度
        self.controller.client.write_tag(
            self.controller.PARAMETERS['speed'], speed
        )

        # 发送前进信号
        return self.controller.client.write_tag(
            self.controller.SIGNALS['ST1'], True
        )

    def jog_backward(self, speed: float = 30.0) -> bool:
        """
        反向点动

        Args:
            speed: 点动速度（度/秒）
        """
        logger.info(f"反向点动，速度: {speed}度/秒")

        # 设置速度
        self.controller.client.write_tag(
            self.controller.PARAMETERS['speed'], speed
        )

        # 发送后退信号
        return self.controller.client.write_tag(
            self.controller.SIGNALS['ST0'], True
        )

    def stop_jog(self):
        """停止点动"""
        self.controller.client.write_tag(self.controller.SIGNALS['ST0'], False)
        self.controller.client.write_tag(self.controller.SIGNALS['ST1'], False)
        logger.info("停止点动")

    def move_sequence(self, positions: List[float], speed: float = 100.0,
                     dwell_time: float = 1.0) -> bool:
        """
        按顺序移动到多个位置

        Args:
            positions: 位置列表
            speed: 移动速度
            dwell_time: 每个位置的停留时间（秒）

        Returns:
            bool: 全部成功返回True
        """
        logger.info(f"开始序列运动，共{len(positions)}个位置")

        for i, pos in enumerate(positions):
            logger.info(f"移动到第{i+1}个位置: {pos}度")

            if not self.controller.move_to_position(pos, speed):
                logger.error(f"移动到位置{pos}失败")
                return False

            # 停留
            import time
            time.sleep(dwell_time)

        logger.info("序列运动完成")
        return True

    def push_operation(self, push_position: float, push_force: int = 50,
                      approach_speed: float = 100.0) -> bool:
        """
        执行推压操作

        Args:
            push_position: 推压位置（度）
            push_force: 推压力（20-70%）
            approach_speed: 接近速度（度/秒）

        Returns:
            bool: 成功返回True
        """
        logger.info(f"执行推压操作，位置: {push_position}度，推压力: {push_force}%")

        # 验证推压力范围
        if not 20 <= push_force <= 70:
            logger.error("推压力必须在20-70%范围内")
            return False

        # 设置推压参数
        # 注意：实际的标签名需要根据电缸的具体实现确定
        self.controller.client.write_tag('Controller.PushForce', push_force)
        self.controller.client.write_tag('Controller.PushPosition', push_position)
        self.controller.client.write_tag('Controller.PushMode', True)

        # 移动到推压位置
        result = self.controller.move_to_position(push_position, approach_speed)

        # 关闭推压模式
        self.controller.client.write_tag('Controller.PushMode', False)

        return result