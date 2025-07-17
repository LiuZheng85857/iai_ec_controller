"""
状态监控命令模块
用于监控电缸运行状态和诊断信息
"""
import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger


class StatusCommands:
    """状态监控命令类"""

    def __init__(self, controller):
        """
        初始化状态命令

        Args:
            controller: EC控制器实例
        """
        self.controller = controller
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.status_callback: Optional[Callable] = None

    def get_full_status(self) -> Dict[str, Any]:
        """
        获取完整状态信息

        Returns:
            Dict[str, Any]: 状态字典
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'connection': {
                'connected': self.controller.client.connected,
                'ip_address': self.controller.client.ip_address,
            },
            'position': {
                'current': self.controller.get_current_position(),
                'unit': 'degree'
            },
            'signals': {
                'ST0': self._read_signal('ST0'),
                'ST1': self._read_signal('ST1'),
                'LS0': self._read_signal('LS0'),
                'LS1': self._read_signal('LS1'),
                'PE0': self._read_signal('PE0'),
                'PE1': self._read_signal('PE1'),
                'ALM': self._read_signal('ALM'),
                'RES': self._read_signal('RES'),
            },
            'motion': {
                'home_complete': self.controller.is_homing_complete,
                'speed': self._read_parameter('speed'),
                'acceleration': self._read_parameter('acceleration'),
                'deceleration': self._read_parameter('deceleration'),
            },
            'alarm': {
                'active': self.controller._check_alarm(),
                'code': self._get_alarm_code(),
                'description': self._get_alarm_description(),
            },
            'maintenance': {
                'total_moves': self._read_maintenance_counter('total_moves'),
                'travel_distance': self._read_maintenance_counter('travel_distance'),
                'overload_level': self._read_maintenance_counter('overload_level'),
            }
        }

        return status

    def get_io_status(self) -> Dict[str, bool]:
        """
        获取I/O状态

        Returns:
            Dict[str, bool]: I/O信号状态
        """
        io_status = {}
        for signal in ['ST0', 'ST1', 'LS0', 'LS1', 'PE0', 'PE1', 'ALM', 'RES']:
            io_status[signal] = self._read_signal(signal)
        return io_status

    def start_monitoring(self, interval: float = 0.1,
                         callback: Optional[Callable] = None):
        """
        开始状态监控

        Args:
            interval: 监控间隔(秒)
            callback: 状态更新回调函数
        """
        if self.monitoring:
            logger.warning("监控已在运行")
            return

        self.monitoring = True
        self.status_callback = callback
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("状态监控已启动")

    def stop_monitoring(self):
        """停止状态监控"""
        if not self.monitoring:
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("状态监控已停止")

    def check_alarm_history(self) -> list:
        """
        检查报警历史

        Returns:
            list: 报警历史列表
        """
        # 这里需要根据实际的电缸实现来读取报警历史
        # 示例实现
        history = []
        for i in range(10):  # 假设最多保存10条历史
            alarm_code = self.controller.client.read_tag(f"Controller.AlarmHistory{i}")
            if alarm_code:
                history.append({
                    'index': i,
                    'code': alarm_code,
                    'description': self._get_alarm_description(alarm_code),
                    'timestamp': self.controller.client.read_tag(f"Controller.AlarmTime{i}")
                })
        return history

    def get_diagnostic_info(self) -> Dict[str, Any]:
        """
        获取诊断信息

        Returns:
            Dict[str, Any]: 诊断信息
        """
        return {
            'motor_temperature': self._read_diagnostic('motor_temperature'),
            'controller_temperature': self._read_diagnostic('controller_temperature'),
            'bus_voltage': self._read_diagnostic('bus_voltage'),
            'motor_current': self._read_diagnostic('motor_current'),
            'encoder_status': self._read_diagnostic('encoder_status'),
            'firmware_version': self._read_diagnostic('firmware_version'),
        }

    def export_status_log(self, filename: str = "status_log.csv"):
        """
        导出状态日志

        Args:
            filename: 导出文件名
        """
        import csv

        status = self.get_full_status()

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入标题
            writer.writerow(['Timestamp', 'Parameter', 'Value'])

            # 递归写入所有状态
            def write_dict(d, prefix=''):
                for key, value in d.items():
                    if isinstance(value, dict):
                        write_dict(value, f"{prefix}{key}.")
                    else:
                        writer.writerow([status['timestamp'], f"{prefix}{key}", value])

            write_dict(status)

        logger.info(f"状态日志已导出到 {filename}")

    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.monitoring:
            try:
                status = self.get_full_status()

                # 检查报警
                if status['alarm']['active']:
                    logger.warning(f"检测到报警: {status['alarm']['description']}")

                # 调用回调
                if self.status_callback:
                    self.status_callback(status)

            except Exception as e:
                logger.error(f"监控出错: {e}")

            time.sleep(interval)

    def _read_signal(self, signal_name: str) -> bool:
        """读取信号状态"""
        if signal_name in self.controller.SIGNALS:
            value = self.controller.client.read_tag(self.controller.SIGNALS[signal_name])
            return bool(value) if value is not None else False
        return False

    def _read_parameter(self, param_name: str) -> Optional[Any]:
        """读取参数值"""
        if param_name in self.controller.PARAMETERS:
            return self.controller.client.read_tag(self.controller.PARAMETERS[param_name])
        return None

    def _read_maintenance_counter(self, counter_name: str) -> Optional[int]:
        """读取维护计数器"""
        tag_map = {
            'total_moves': 'Controller.TotalMoves',
            'travel_distance': 'Controller.TravelDistance',
            'overload_level': 'Controller.OverloadLevel',
        }
        if counter_name in tag_map:
            return self.controller.client.read_tag(tag_map[counter_name])
        return None

    def _read_diagnostic(self, diag_name: str) -> Optional[Any]:
        """读取诊断信息"""
        tag_map = {
            'motor_temperature': 'Controller.MotorTemp',
            'controller_temperature': 'Controller.ControllerTemp',
            'bus_voltage': 'Controller.BusVoltage',
            'motor_current': 'Controller.MotorCurrent',
            'encoder_status': 'Controller.EncoderStatus',
            'firmware_version': 'Controller.FirmwareVersion',
        }
        if diag_name in tag_map:
            return self.controller.client.read_tag(tag_map[diag_name])
        return None

    def _get_alarm_code(self) -> Optional[str]:
        """获取当前报警代码"""
        return self.controller.client.read_tag('Controller.AlarmCode')

    def _get_alarm_description(self, code: Optional[str] = None) -> str:
        """获取报警描述"""
        if code is None:
            code = self._get_alarm_code()

        if not code:
            return "无报警"

        # 报警代码映射（根据说明书）
        alarm_map = {
            'A': '过载报警',
            'B': '马达异常报警',
            'C': '控制器异常报警',
            'D': '控制器~编码器间异常报警',
            'E': '供电电压、电源容量异常报警',
        }

        return alarm_map.get(code[0], f"未知报警: {code}")