"""串口通信模块"""
import serial
import serial.tools.list_ports
import struct
import time
import logging
from typing import List, Optional, Tuple


class SerialClient:
    """串口通信客户端"""

    def __init__(self, port: str = None, baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def list_ports() -> List[Tuple[str, str]]:
        """列出所有可用串口

        Returns:
            [(端口名, 描述), ...]
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, port.description))
        return ports

    def connect(self) -> bool:
        """建立串口连接"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self.logger.info(f"成功连接到串口: {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"串口连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.logger.info("串口断开连接")

    def is_connected(self) -> bool:
        """检查是否连接"""
        return self.serial and self.serial.is_open

    def send_command(self, command: bytes) -> bool:
        """发送命令"""
        try:
            if not self.is_connected():
                return False

            self.serial.write(command)
            self.logger.debug(f"发送: {command.hex()}")
            return True
        except Exception as e:
            self.logger.error(f"发送失败: {e}")
            return False

    def receive_response(self, length: int = None) -> Optional[bytes]:
        """接收响应"""
        try:
            if not self.is_connected():
                return None

            if length:
                response = self.serial.read(length)
            else:
                response = self.serial.read_all()

            if response:
                self.logger.debug(f"接收: {response.hex()}")
            return response
        except Exception as e:
            self.logger.error(f"接收失败: {e}")
            return None

    def query(self, command: bytes, response_length: int = None) -> Optional[bytes]:
        """查询（发送命令并接收响应）"""
        if self.send_command(command):
            time.sleep(0.01)  # 短暂延时
            return self.receive_response(response_length)
        return None