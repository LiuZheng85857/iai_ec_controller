"""
EtherNet/IP通信客户端
用于与IAI EC电缸建立通信连接
"""
import time
from typing import Optional, Dict, Any
from pycomm3 import CIPDriver, Services
from loguru import logger


class EIPClient:
    """EtherNet/IP客户端类"""

    def __init__(self, ip_address: str, port: int = 44818):
        """
        初始化EIP客户端

        Args:
            ip_address: 电缸IP地址
            port: 通信端口，默认44818
        """
        self.ip_address = ip_address
        self.port = port
        self.driver: Optional[CIPDriver] = None
        self.connected = False

    def connect(self) -> bool:
        """
        建立与电缸的连接

        Returns:
            bool: 连接成功返回True，失败返回False
        """
        try:
            self.driver = CIPDriver(self.ip_address)
            self.driver.open()
            self.connected = True
            logger.info(f"成功连接到电缸 {self.ip_address}")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """断开连接"""
        if self.driver and self.connected:
            self.driver.close()
            self.connected = False
            logger.info("已断开与电缸的连接")

    def read_tag(self, tag_name: str) -> Optional[Any]:
        """
        读取标签值

        Args:
            tag_name: 标签名称

        Returns:
            标签值，失败返回None
        """
        if not self.connected:
            logger.error("未连接到电缸")
            return None

        try:
            result = self.driver.read(tag_name)
            if result:
                return result.value
            return None
        except Exception as e:
            logger.error(f"读取标签 {tag_name} 失败: {e}")
            return None

    def write_tag(self, tag_name: str, value: Any) -> bool:
        """
        写入标签值

        Args:
            tag_name: 标签名称
            value: 要写入的值

        Returns:
            bool: 写入成功返回True，失败返回False
        """
        if not self.connected:
            logger.error("未连接到电缸")
            return False

        try:
            result = self.driver.write(tag_name, value)
            return result is not None
        except Exception as e:
            logger.error(f"写入标签 {tag_name} 失败: {e}")
            return False