"""连接测试模块"""
import socket
import subprocess
import platform
import time
import struct
from typing import Dict, List, Tuple, Optional
from pycomm3 import CIPDriver
import logging

class ConnectionDiagnostics:
    """连接诊断类"""

    def __init__(self, ip_address: str, timeout: float = 3.0):
        self.ip_address = ip_address
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.test_results = {}

    def run_all_tests(self) -> Dict[str, Dict]:
        """运行所有测试"""
        self.test_results = {
            'network_adapter': self.test_network_adapter(),
            'ping': self.test_ping(),
            'tcp_port': self.test_tcp_ports(),
            'ethernet_ip': self.test_ethernet_ip_connection(),
            'device_info': self.get_device_info(),
            'communication': self.test_communication()
        }
        return self.test_results

    def test_network_adapter(self) -> Dict:
        """测试网络适配器"""
        result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }

        try:
            import psutil

            # 获取所有网络接口
            interfaces = psutil.net_if_addrs()
            active_interfaces = []

            for interface, addrs in interfaces.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        # 检查是否在同一网段
                        if self._is_same_subnet(addr.address, self.ip_address, addr.netmask):
                            active_interfaces.append({
                                'name': interface,
                                'ip': addr.address,
                                'netmask': addr.netmask
                            })

            if active_interfaces:
                result['status'] = 'pass'
                result['message'] = f"找到 {len(active_interfaces)} 个可用网络接口"
                result['details']['interfaces'] = active_interfaces
            else:
                result['status'] = 'fail'
                result['message'] = "没有找到与目标设备同网段的网络接口"
                result['details']['suggestion'] = "请检查网络配置或连接网线"

        except ImportError:
            # 如果没有安装psutil，使用基本方法
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                result['status'] = 'partial'
                result['message'] = f"本机IP: {local_ip}"
                result['details']['local_ip'] = local_ip
            except Exception as e:
                result['status'] = 'fail'
                result['message'] = f"无法获取网络信息: {str(e)}"

        return result

    def test_ping(self) -> Dict:
        """测试ping连通性"""
        result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }

        try:
            # 根据操作系统选择ping命令
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '4', self.ip_address]

            # 执行ping命令
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=self.timeout + 2)

            if process.returncode == 0:
                result['status'] = 'pass'
                result['message'] = f"Ping {self.ip_address} 成功"

                # 解析ping统计信息
                if platform.system().lower() == 'windows':
                    # Windows ping输出解析
                    import re
                    loss_match = re.search(r'(\d+)% loss', stdout)
                    if loss_match:
                        loss = int(loss_match.group(1))
                        result['details']['packet_loss'] = f"{loss}%"

                    time_match = re.search(r'Average = (\d+)ms', stdout)
                    if time_match:
                        avg_time = int(time_match.group(1))
                        result['details']['avg_time'] = f"{avg_time}ms"
                else:
                    # Linux/Mac ping输出解析
                    lines = stdout.strip().split('\n')
                    for line in lines:
                        if 'packet loss' in line:
                            result['details']['statistics'] = line.strip()
                        elif 'avg' in line:
                            result['details']['timing'] = line.strip()
            else:
                result['status'] = 'fail'
                result['message'] = f"Ping {self.ip_address} 失败"
                result['details']['error'] = stderr or "目标主机不可达"
                result['details']['suggestion'] = "检查IP地址是否正确，网线是否连接，设备是否上电"

        except subprocess.TimeoutExpired:
            result['status'] = 'fail'
            result['message'] = "Ping超时"
            result['details']['error'] = "没有收到响应"
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"Ping测试出错: {str(e)}"

        return result

    def test_tcp_ports(self) -> Dict:
        """测试TCP端口"""
        result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }

        # EtherNet/IP常用端口
        ports_to_test = {
            44818: 'EtherNet/IP (TCP)',
            2222: 'EtherNet/IP (UDP)',
            80: 'HTTP',
            502: 'Modbus TCP'
        }

        open_ports = []
        closed_ports = []

        for port, description in ports_to_test.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            try:
                result_code = sock.connect_ex((self.ip_address, port))
                if result_code == 0:
                    open_ports.append(f"{port} ({description})")
                else:
                    closed_ports.append(f"{port} ({description})")
            except Exception as e:
                closed_ports.append(f"{port} ({description}) - 错误: {str(e)}")
            finally:
                sock.close()

        result['details']['open_ports'] = open_ports
        result['details']['closed_ports'] = closed_ports

        if 44818 in [int(p.split()[0]) for p in open_ports]:
            result['status'] = 'pass'
            result['message'] = "EtherNet/IP端口开放"
        else:
            result['status'] = 'fail'
            result['message'] = "EtherNet/IP端口未开放"
            result['details']['suggestion'] = "检查设备是否支持EtherNet/IP或防火墙设置"

        return result

    def test_ethernet_ip_connection(self) -> Dict:
        """测试EtherNet/IP连接"""
        result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }

        try:
            # 尝试建立CIP连接
            with CIPDriver(self.ip_address) as driver:
                # 获取设备信息
                info = driver.get_module_info()
                if info:
                    result['status'] = 'pass'
                    result['message'] = "EtherNet/IP连接成功"
                    result['details']['device_info'] = {
                        'vendor': info.vendor,
                        'product_type': info.product_type,
                        'product_code': info.product_code,
                        'revision': f"{info.revision.major}.{info.revision.minor}",
                        'status': info.status,
                        'serial': info.serial,
                        'product_name': info.product_name
                    }
                else:
                    result['status'] = 'partial'
                    result['message'] = "连接建立但无法获取设备信息"

        except Exception as e:
            result['status'] = 'fail'
            result['message'] = "EtherNet/IP连接失败"
            result['details']['error'] = str(e)

            # 分析错误原因
            error_str = str(e).lower()
            if 'timeout' in error_str:
                result['details']['suggestion'] = "连接超时，检查网络延迟或设备响应"
            elif 'refused' in error_str:
                result['details']['suggestion'] = "连接被拒绝，检查设备配置或IP地址"
            elif 'unreachable' in error_str:
                result['details']['suggestion'] = "设备不可达，检查网络连接"
            else:
                result['details']['suggestion'] = "检查设备是否支持EtherNet/IP协议"

        return result

    def get_device_info(self) -> Dict:
        """获取设备详细信息"""
        result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }

        try:
            with CIPDriver(self.ip_address) as driver:
                # 尝试读取设备标识
                identity = driver.generic_message(
                    class_code=0x01,
                    instance=0x01,
                    service=0x01,
                    connected=False
                )

                if identity:
                    result['status'] = 'pass'
                    result['message'] = "成功获取设备信息"
                    # 解析标识对象数据
                    # 这里需要根据实际返回的数据格式进行解析
                else:
                    result['status'] = 'fail'
                    result['message'] = "无法获取设备标识信息"

        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"获取设备信息失败: {str(e)}"

        return result

    def test_communication(self) -> Dict:
        """测试实际通信"""
        result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }

        try:
            from core.ethernet_ip import EtherNetIPClient

            client = EtherNetIPClient(self.ip_address, self.timeout)

            # 测试连接
            if client.connect():
                result['details']['connection'] = "连接成功"

                # 测试读取数据
                test_data = client.read_data(0, 2)
                if test_data is not None:
                    result['status'] = 'pass'
                    result['message'] = "通信测试成功"
                    result['details']['read_test'] = f"成功读取{len(test_data)}字节数据"
                else:
                    result['status'] = 'partial'
                    result['message'] = "连接成功但无法读取数据"
                    result['details']['suggestion'] = "检查读取地址是否正确"

                client.disconnect()
            else:
                result['status'] = 'fail'
                result['message'] = "无法建立通信连接"

        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"通信测试失败: {str(e)}"

        return result

    def _is_same_subnet(self, ip1: str, ip2: str, netmask: str) -> bool:
        """检查两个IP是否在同一子网"""
        try:
            # 将IP地址和子网掩码转换为整数
            ip1_int = struct.unpack('!I', socket.inet_aton(ip1))[0]
            ip2_int = struct.unpack('!I', socket.inet_aton(ip2))[0]
            netmask_int = struct.unpack('!I', socket.inet_aton(netmask))[0]

            # 计算网络地址
            network1 = ip1_int & netmask_int
            network2 = ip2_int & netmask_int

            return network1 == network2
        except:
            return False

    def generate_report(self) -> str:
        """生成诊断报告"""
        report = []
        report.append("="*60)
        report.append("REC控制器连接诊断报告")
        report.append("="*60)
        report.append(f"目标IP地址: {self.ip_address}")
        report.append(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*60)

        # 测试结果汇总
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'pass')
        failed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'fail')

        report.append(f"\n测试汇总: 总计 {total_tests} 项, 通过 {passed_tests} 项, 失败 {failed_tests} 项")
        report.append("-"*60)

        # 详细结果
        test_names = {
            'network_adapter': '网络适配器检查',
            'ping': 'Ping连通性测试',
            'tcp_port': 'TCP端口扫描',
            'ethernet_ip': 'EtherNet/IP协议测试',
            'device_info': '设备信息获取',
            'communication': '通信功能测试'
        }

        for test_key, test_name in test_names.items():
            if test_key in self.test_results:
                result = self.test_results[test_key]
                status_icon = {
                    'pass': '✓',
                    'fail': '✗',
                    'partial': '△',
                    'unknown': '?',
                    'error': '!'
                }.get(result['status'], '?')

                report.append(f"\n[{status_icon}] {test_name}")
                report.append(f"    状态: {result['message']}")

                if result['details']:
                    for key, value in result['details'].items():
                        if isinstance(value, list):
                            report.append(f"    {key}:")
                            for item in value:
                                report.append(f"        - {item}")
                        elif isinstance(value, dict):
                            report.append(f"    {key}:")
                            for k, v in value.items():
                                report.append(f"        {k}: {v}")
                        else:
                            report.append(f"    {key}: {value}")

        # 建议
        report.append("\n" + "="*60)
        report.append("诊断建议:")
        report.append("-"*60)

        suggestions = []
        for result in self.test_results.values():
            if result['status'] == 'fail' and 'suggestion' in result['details']:
                suggestions.append(result['details']['suggestion'])

        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                report.append(f"{i}. {suggestion}")
        else:
            report.append("所有测试通过，连接正常！")

        report.append("="*60)

        return '\n'.join(report)