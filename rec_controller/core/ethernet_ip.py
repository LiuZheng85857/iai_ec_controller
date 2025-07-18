"""EtherNet/IP通信协议实现"""
from pycomm3 import CIPDriver, Services, ClassCode, INT, DINT, REAL
import struct
import logging


class EtherNetIPClient:
    """EtherNet/IP客户端类"""

    def __init__(self, ip_address, timeout=3.0):
        self.ip_address = ip_address
        self.timeout = timeout
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """建立连接"""
        try:
            self.driver = CIPDriver(self.ip_address, timeout=self.timeout)
            self.driver.open()
            self.logger.info(f"成功连接到REC控制器: {self.ip_address}")
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.driver:
            self.driver.close()
            self.logger.info("断开连接")

    def read_data(self, start_address, length):
        """读取数据"""
        try:
            # 使用pycomm3的read方法读取数据
            # 根据REC文档，使用字节地址
            tag = f"B{start_address}:{length}"
            result = self.driver.read(tag)
            if result and hasattr(result, 'value'):
                return result.value
            elif result and hasattr(result, 'data'):
                return result.data
            else:
                return None
        except Exception as e:
            self.logger.error(f"读取数据失败: {e}")
            return None

    def write_data(self, start_address, data):
        """写入数据"""
        try:
            tag = f"B{start_address}"
            result = self.driver.write(tag, data)
            if hasattr(result, 'error'):
                return result.error is None
            else:
                return True
        except Exception as e:
            self.logger.error(f"写入数据失败: {e}")
            return False