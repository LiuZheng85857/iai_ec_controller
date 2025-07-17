"""
数据转换工具
用于各种单位和数据格式的转换
"""
from typing import Union, List, Tuple
import struct


class Converter:
    """数据转换器"""

    @staticmethod
    def degree_to_pulse(degree: float, reduction_ratio: int = 45,
                        encoder_resolution: int = 800) -> int:
        """
        角度转换为脉冲数

        Args:
            degree: 角度值
            reduction_ratio: 减速比
            encoder_resolution: 编码器分辨率

        Returns:
            int: 脉冲数
        """
        pulses_per_degree = (encoder_resolution * reduction_ratio) / 360
        return int(degree * pulses_per_degree)

    @staticmethod
    def pulse_to_degree(pulse: int, reduction_ratio: int = 45,
                        encoder_resolution: int = 800) -> float:
        """
        脉冲数转换为角度

        Args:
            pulse: 脉冲数
            reduction_ratio: 减速比
            encoder_resolution: 编码器分辨率

        Returns:
            float: 角度值
        """
        pulses_per_degree = (encoder_resolution * reduction_ratio) / 360
        return pulse / pulses_per_degree

    @staticmethod
    def rpm_to_degree_per_second(rpm: float) -> float:
        """
        转速(RPM)转换为角速度(度/秒)

        Args:
            rpm: 转速(转/分钟)

        Returns:
            float: 角速度(度/秒)
        """
        return rpm * 6.0  # RPM * 360度 / 60秒

    @staticmethod
    def degree_per_second_to_rpm(degree_per_second: float) -> float:
        """
        角速度(度/秒)转换为转速(RPM)

        Args:
            degree_per_second: 角速度(度/秒)

        Returns:
            float: 转速(转/分钟)
        """
        return degree_per_second / 6.0

    @staticmethod
    def g_to_degree_per_second2(g: float) -> float:
        """
        G值转换为角加速度(度/秒²)

        Args:
            g: 加速度(G)

        Returns:
            float: 角加速度(度/秒²)
        """
        return g * 9807  # 1G = 9807度/秒²

    @staticmethod
    def degree_per_second2_to_g(degree_per_second2: float) -> float:
        """
        角加速度(度/秒²)转换为G值

        Args:
            degree_per_second2: 角加速度(度/秒²)

        Returns:
            float: 加速度(G)
        """
        return degree_per_second2 / 9807

    @staticmethod
    def percentage_to_current_limit(percentage: int) -> float:
        """
        百分比转换为电流限制值
        用于推压力设置

        Args:
            percentage: 百分比(20-70%)

        Returns:
            float: 电流限制值(A)
        """
        # 假设100%对应1.2A（根据说明书马达额定电流）
        return percentage * 0.012

    @staticmethod
    def torque_to_push_force(torque: float, radius: float = 0.015) -> float:
        """
        扭矩转换为推力

        Args:
            torque: 扭矩(N·m)
            radius: 作用半径(m)，默认15mm

        Returns:
            float: 推力(N)
        """
        return torque / radius

    @staticmethod
    def bytes_to_float(bytes_data: bytes, byteorder: str = 'little') -> float:
        """
        字节数据转换为浮点数

        Args:
            bytes_data: 字节数据
            byteorder: 字节序('little' 或 'big')

        Returns:
            float: 浮点数
        """
        if len(bytes_data) == 4:
            return struct.unpack('<f' if byteorder == 'little' else '>f', bytes_data)[0]
        else:
            raise ValueError("字节数据长度必须为4")

    @staticmethod
    def float_to_bytes(value: float, byteorder: str = 'little') -> bytes:
        """
        浮点数转换为字节数据

        Args:
            value: 浮点数
            byteorder: 字节序('little' 或 'big')

        Returns:
            bytes: 字节数据
        """
        return struct.pack('<f' if byteorder == 'little' else '>f', value)

    @staticmethod
    def calculate_inertia(mass: float, radius: float) -> float:
        """
        计算圆盘转动惯量

        Args:
            mass: 质量(kg)
            radius: 半径(mm)

        Returns:
            float: 转动惯量(kg·m²)
        """
        radius_m = radius * 0.001  # mm转m
        return mass * (radius_m ** 2) / 8

    @staticmethod
    def calculate_motion_time(distance: float, speed: float,
                              acceleration: float) -> Tuple[float, float, float]:
        """
        计算运动时间

        Args:
            distance: 移动距离(度)
            speed: 最大速度(度/秒)
            acceleration: 加速度(G)

        Returns:
            Tuple[float, float, float]: (加速时间, 匀速时间, 总时间)
        """
        acc_deg_s2 = acceleration * 9807  # G转度/秒²

        # 加速时间
        t_acc = speed / acc_deg_s2

        # 加速距离
        s_acc = 0.5 * acc_deg_s2 * (t_acc ** 2)

        # 如果加减速距离大于总距离
        if 2 * s_acc >= distance:
            # 无法达到最大速度
            t_acc = (distance / acc_deg_s2) ** 0.5
            t_const = 0
            t_total = 2 * t_acc
        else:
            # 可以达到最大速度
            s_const = distance - 2 * s_acc
            t_const = s_const / speed
            t_total = 2 * t_acc + t_const

        return t_acc, t_const, t_total