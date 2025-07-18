"""网络扫描模块"""
import socket
import threading
import ipaddress
from typing import List, Dict, Callable
import time


class NetworkScanner:
    """网络扫描器"""

    def __init__(self, subnet: str = None):
        """
        Args:
            subnet: 子网，例如 '192.168.0.0/24'
        """
        self.subnet = subnet or self._get_local_subnet()
        self.results = []
        self.scan_progress = 0
        self.is_scanning = False

    def _get_local_subnet(self) -> str:
        """获取本地子网"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            # 假设是/24子网
            ip_parts = local_ip.split('.')
            subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
            return subnet
        except:
            return "192.168.0.0/24"

    def scan_network(self, port: int = 44818, timeout: float = 0.5,
                     progress_callback: Callable = None) -> List[Dict]:
        """扫描网络中的设备

        Args:
            port: 要扫描的端口
            timeout: 连接超时时间
            progress_callback: 进度回调函数

        Returns:
            找到的设备列表
        """
        self.results = []
        self.scan_progress = 0
        self.is_scanning = True

        try:
            network = ipaddress.ip_network(self.subnet, strict=False)
            total_hosts = network.num_addresses - 2  # 排除网络地址和广播地址

            threads = []
            checked = 0

            for ip in network.hosts():
                if not self.is_scanning:
                    break

                thread = threading.Thread(
                    target=self._scan_host,
                    args=(str(ip), port, timeout)
                )
                thread.start()
                threads.append(thread)

                # 限制并发线程数
                if len(threads) >= 50:
                    for t in threads:
                        t.join()
                    threads = []

                checked += 1
                self.scan_progress = int(checked / total_hosts * 100)

                if progress_callback:
                    progress_callback(self.scan_progress)

            # 等待剩余线程
            for t in threads:
                t.join()

        finally:
            self.is_scanning = False

        return self.results

    def _scan_host(self, ip: str, port: int, timeout: float):
        """扫描单个主机"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            result = sock.connect_ex((ip, port))
            if result == 0:
                # 端口开放，尝试获取更多信息
                device_info = {
                    'ip': ip,
                    'port': port,
                    'status': 'open',
                    'timestamp': time.time()
                }

                # 尝试获取设备信息
                try:
                    from pycomm3 import CIPDriver
                    with CIPDriver(ip) as driver:
                        info = driver.get_module_info()
                        if info:
                            device_info['device_type'] = 'REC Controller'
                            device_info['vendor'] = info.vendor
                            device_info['product_name'] = info.product_name
                except:
                    device_info['device_type'] = 'Unknown EtherNet/IP Device'

                self.results.append(device_info)

        except Exception as e:
            pass
        finally:
            sock.close()

    def stop_scan(self):
        """停止扫描"""
        self.is_scanning = False