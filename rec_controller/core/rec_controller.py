"""REC控制器类 - 支持串口和网络通信"""
import struct
import time
from typing import List, Dict, Optional, Union
from .ethernet_ip import EtherNetIPClient
from .serial_comm import SerialClient

class RECController:
    """REC控制器主类"""

    # 通信类型
    COMM_SERIAL = 'serial'
    COMM_ETHERNET_IP = 'ethernet_ip'

    # 根据文档定义的地址偏移
    GATEWAY_STATUS_OFFSET = 0
    UNIT_BASE_OFFSET = 2
    BYTES_PER_UNIT = 2

    def __init__(self, comm_type: str = COMM_SERIAL, **kwargs):
        """
        Args:
            comm_type: 通信类型 ('serial' 或 'ethernet_ip')
            **kwargs:
                串口模式: port, baudrate
                网络模式: ip_address, unit_count
        """
        import logging
        self.logger = logging.getLogger(__name__)
        self.comm_type = comm_type
        self.connected = False

        if comm_type == self.COMM_SERIAL:
            self.port = kwargs.get('port', 'COM6')
            self.baudrate = kwargs.get('baudrate', 115200)
            self.client = SerialClient(self.port, self.baudrate)
        else:
            self.ip_address = kwargs.get('ip_address', '192.168.0.1')
            self.unit_count = kwargs.get('unit_count', 1)
            self.client = EtherNetIPClient(self.ip_address)

    def connect(self) -> bool:
        """连接到REC控制器"""
        self.connected = self.client.connect()

        if self.connected and self.comm_type == self.COMM_SERIAL:
            # 串口连接后，尝试识别设备
            if not self._identify_device():
                self.logger.warning("无法识别设备")

        return self.connected

    def disconnect(self):
        """断开连接"""
        self.client.disconnect()
        self.connected = False

    def _identify_device(self) -> bool:
        """识别设备（串口模式）"""
        if self.comm_type != self.COMM_SERIAL:
            return True

        # 发送识别命令（根据实际协议调整）
        identify_cmd = b'\x01\x03\x00\x00\x00\x01\x84\x0A'  # 示例Modbus命令
        response = self.client.query(identify_cmd, 7)

        if response and len(response) >= 5:
            # 解析响应（根据实际协议调整）
            device_id = response[3:5]
            self.logger.info(f"设备识别: {device_id.hex()}")
            return True
        return False

    def read_data(self, address: int, length: int) -> Optional[bytes]:
        """读取数据（统一接口）"""
        if self.comm_type == self.COMM_SERIAL:
            return self._read_serial(address, length)
        else:
            return self._read_ethernet(address, length)

    def write_data(self, address: int, data: bytes) -> bool:
        """写入数据（统一接口）"""
        if self.comm_type == self.COMM_SERIAL:
            return self._write_serial(address, data)
        else:
            return self._write_ethernet(address, data)

    def _read_serial(self, address: int, length: int) -> Optional[bytes]:
        """串口读取（Modbus RTU协议示例）"""
        # 构造Modbus读取命令
        slave_id = 0x01
        function = 0x03  # Read Holding Registers

        cmd = struct.pack('>BBHH', slave_id, function, address, length)
        crc = self._calculate_crc(cmd)
        cmd += struct.pack('<H', crc)

        # 发送并接收
        response = self.client.query(cmd, 5 + length * 2)

        if response and len(response) >= 5:
            # 验证CRC
            if self._verify_crc(response):
                # 提取数据
                data_start = 3
                data_end = 3 + response[2]
                return response[data_start:data_end]

        return None

    def _write_serial(self, address: int, data: bytes) -> bool:
        """串口写入（Modbus RTU协议示例）"""
        slave_id = 0x01
        function = 0x10  # Write Multiple Registers

        num_registers = len(data) // 2
        byte_count = len(data)

        cmd = struct.pack('>BBHHB', slave_id, function, address,
                         num_registers, byte_count)
        cmd += data
        crc = self._calculate_crc(cmd)
        cmd += struct.pack('<H', crc)

        response = self.client.query(cmd, 8)

        return response is not None and len(response) >= 8

    def _read_ethernet(self, address: int, length: int) -> Optional[bytes]:
        """以太网读取"""
        data = self.client.read_data(address, length)
        return bytes(data) if data else None

    def _write_ethernet(self, address: int, data: bytes) -> bool:
        """以太网写入"""
        return self.client.write_data(address, list(data))

    def _calculate_crc(self, data: bytes) -> int:
        """计算Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def _verify_crc(self, data: bytes) -> bool:
        """验证CRC"""
        if len(data) < 3:
            return False

        received_crc = struct.unpack('<H', data[-2:])[0]
        calculated_crc = self._calculate_crc(data[:-2])

        return received_crc == calculated_crc

    # 保留原有的高级接口
    def read_gateway_status(self) -> Dict:
        """读取网关状态"""
        data = self.read_data(self.GATEWAY_STATUS_OFFSET, 2)
        if data:
            status_word = struct.unpack('<H', data)[0]
            return {
                'almh': not bool(status_word & 0x8000),
                'mod': bool(status_word & 0x2000),
                'estp': bool(status_word & 0x1000),
                'alarm_code': status_word & 0xFF
            }
        return None

    def send_axis_command(self, unit_index: int, axis_index: int,
                         command: str, value: bool = True):
        """发送轴控制命令"""
        # 计算地址偏移
        address = self.UNIT_BASE_OFFSET + (unit_index * self.BYTES_PER_UNIT)

        # 读取当前控制字
        current_data = self.read_data(address, 2)
        if current_data:
            control_word = struct.unpack('<H', current_data)[0]
        else:
            control_word = 0

        # 根据命令修改对应位
        bit_offset = axis_index * 4
        if command == 'ST0':
            bit_position = bit_offset + 0
        elif command == 'ST1':
            bit_position = bit_offset + 1
        elif command == 'RES':
            bit_position = bit_offset + 2
        else:
            raise ValueError(f"未知命令: {command}")

        # 设置或清除位
        if value:
            control_word |= (1 << bit_position)
        else:
            control_word &= ~(1 << bit_position)

        # 写回控制字
        data = struct.pack('<H', control_word)
        return self.write_data(address, data)

    def read_axis_status(self, unit_index: int, axis_index: int) -> Optional[Dict]:
        """读取轴状态"""
        # 计算轴状态地址偏移
        # 根据REC文档，轴状态从地址4开始，每个轴占用2字节
        axis_status_offset = 4 + (unit_index * 8) + (axis_index * 2)
        
        data = self.read_data(axis_status_offset, 2)
        if data:
            status_word = struct.unpack('<H', data)[0]
            return {
                'ready': bool(status_word & 0x0001),      # 准备就绪
                'busy': bool(status_word & 0x0002),       # 忙碌
                'done': bool(status_word & 0x0004),       # 完成
                'alarm': bool(status_word & 0x0008),      # 报警
                'error': bool(status_word & 0x0010),      # 错误
                'position': status_word & 0xFF00 >> 8,    # 位置信息（高8位）
                'status_code': status_word & 0x00FF       # 状态码（低8位）
            }
        return None