"""
IAI EC电缸控制器主类
"""
import time
from typing import Optional, Dict, Any
from loguru import logger
from .eip_client import EIPClient
from ..utils.validator import Validator


class ECController:
    """EC电缸控制器"""

    # 信号定义（根据说明书）
    SIGNALS = {
        'ST0': 'Controller.ST0',  # 后退信号
        'ST1': 'Controller.ST1',  # 前进信号
        'RES': 'Controller.RES',  # 报警解除
        'BKRLS': 'Controller.BKRLS',  # 刹车解除
        'LS0': 'Controller.LS0',  # 后退完成
        'LS1': 'Controller.LS1',  # 前进完成
        'PE0': 'Controller.PE0',  # 后退推压完成
        'PE1': 'Controller.PE1',  # 前进推压完成
        'ALM': 'Controller.ALM',  # 报警状态
    }

    # 参数地址定义
    PARAMETERS = {
        'position': 'Controller.Position',  # 当前位置
        'speed': 'Controller.Speed',  # 速度设定
        'acceleration': 'Controller.Acceleration',  # 加速度
        'deceleration': 'Controller.Deceleration',  # 减速度
        'target_position': 'Controller.TargetPos',  # 目标位置
        'home_complete': 'Controller.HomeComplete',  # 原点复位完成
    }

    def __init__(self, config: Dict[str, Any]):
        """
        初始化控制器

        Args:
            config: 配置字典
        """
        self.config = config
        self.client = EIPClient(
            config['connection']['ip_address'],
            config['connection']['port']
        )
        self.validator = Validator(config)
        self.is_homing_complete = False

    def connect(self) -> bool:
        """连接到电缸"""
        return self.client.connect()

    def disconnect(self):
        """断开连接"""
        self.client.disconnect()

    def home(self) -> bool:
        """
        执行原点复位

        Returns:
            bool: 成功返回True，失败返回False
        """
        logger.info("开始原点复位...")

        # 检查是否已连接
        if not self.client.connected:
            logger.error("未连接到电缸")
            return False

        # 发送原点复位信号（ST0）
        if not self.client.write_tag(self.SIGNALS['ST0'], True):
            logger.error("发送原点复位信号失败")
            return False

        # 等待原点复位完成
        timeout = 30  # 30秒超时
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检查原点复位是否完成
            home_complete = self.client.read_tag(self.PARAMETERS['home_complete'])
            if home_complete:
                # 关闭ST0信号
                self.client.write_tag(self.SIGNALS['ST0'], False)
                self.is_homing_complete = True
                logger.info("原点复位完成")
                return True

            # 检查报警
            if self._check_alarm():
                logger.error("原点复位过程中发生报警")
                self.client.write_tag(self.SIGNALS['ST0'], False)
                return False

            time.sleep(0.1)

        logger.error("原点复位超时")
        self.client.write_tag(self.SIGNALS['ST0'], False)
        return False

    def move_to_position(self, position: float, speed: Optional[float] = None,
                         acceleration: Optional[float] = None) -> bool:
        """
        移动到指定位置

        Args:
            position: 目标位置（度）
            speed: 速度（度/秒），None使用默认值
            acceleration: 加速度（G），None使用默认值

        Returns:
            bool: 成功返回True，失败返回False
        """
        # 验证参数
        if not self.validator.validate_position(position):
            logger.error(f"位置 {position} 超出范围")
            return False

        if speed is not None and not self.validator.validate_speed(speed):
            logger.error(f"速度 {speed} 超出范围")
            return False

        # 检查原点复位状态
        if not self.is_homing_complete:
            logger.warning("未完成原点复位，先执行原点复位")
            if not self.home():
                return False

        # 设置运动参数
        if speed is not None:
            self.client.write_tag(self.PARAMETERS['speed'], speed)
        if acceleration is not None:
            self.client.write_tag(self.PARAMETERS['acceleration'], acceleration)
            self.client.write_tag(self.PARAMETERS['deceleration'], acceleration)

        # 设置目标位置
        self.client.write_tag(self.PARAMETERS['target_position'], position)

        # 判断运动方向并发送信号
        current_pos = self.get_current_position()
        if current_pos is None:
            logger.error("无法获取当前位置")
            return False

        if position > current_pos:
            # 前进
            signal = self.SIGNALS['ST1']
            complete_signal = self.SIGNALS['LS1']
            direction = "前进"
        else:
            # 后退
            signal = self.SIGNALS['ST0']
            complete_signal = self.SIGNALS['LS0']
            direction = "后退"

        logger.info(f"{direction}到位置 {position}度...")

        # 发送运动信号
        self.client.write_tag(signal, True)

        # 等待运动完成
        timeout = 60  # 60秒超时
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检查是否到达目标位置
            if self.client.read_tag(complete_signal):
                self.client.write_tag(signal, False)
                logger.info(f"成功到达位置 {position}度")
                return True

            # 检查报警
            if self._check_alarm():
                logger.error("运动过程中发生报警")
                self.client.write_tag(signal, False)
                return False

            time.sleep(0.05)

        logger.error("运动超时")
        self.client.write_tag(signal, False)
        return False

    def stop(self):
        """紧急停止"""
        logger.warning("执行紧急停止")
        # 关闭所有运动信号
        self.client.write_tag(self.SIGNALS['ST0'], False)
        self.client.write_tag(self.SIGNALS['ST1'], False)

    def reset_alarm(self) -> bool:
        """
        复位报警

        Returns:
            bool: 成功返回True，失败返回False
        """
        logger.info("复位报警...")
        self.client.write_tag(self.SIGNALS['RES'], True)
        time.sleep(0.5)
        self.client.write_tag(self.SIGNALS['RES'], False)

        # 检查报警是否清除
        time.sleep(0.5)
        if not self._check_alarm():
            logger.info("报警已清除")
            return True
        else:
            logger.error("报警清除失败")
            return False

    def get_current_position(self) -> Optional[float]:
        """获取当前位置"""
        return self.client.read_tag(self.PARAMETERS['position'])

    def get_status(self) -> Dict[str, Any]:
        """
        获取电缸状态

        Returns:
            包含各种状态信息的字典
        """
        status = {
            'connected': self.client.connected,
            'position': self.get_current_position(),
            'alarm': self._check_alarm(),
            'home_complete': self.is_homing_complete,
            'ls0': self.client.read_tag(self.SIGNALS['LS0']),
            'ls1': self.client.read_tag(self.SIGNALS['LS1']),
        }
        return status

    def _check_alarm(self) -> bool:
        """
        检查报警状态

        Returns:
            bool: 有报警返回True，无报警返回False
        """
        # ALM信号是b接点（负逻辑），正常时为True，报警时为False
        alarm_signal = self.client.read_tag(self.SIGNALS['ALM'])
        return alarm_signal is False if alarm_signal is not None else False