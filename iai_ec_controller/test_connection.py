"""
简单的连接测试
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'iai_ec_controller'))

import yaml
from core.eip_client import EIPClient

# 测试连接
client = EIPClient('192.168.1.100')
print(f"尝试连接到 {client.ip_address}...")

if client.connect():
    print("连接成功！")
    client.disconnect()
else:
    print("连接失败")