"""
连接测试模块
"""
import pytest
import time
from unittest.mock import Mock, patch
from core.eip_client import EIPClient
from core.ec_controller import ECController


class TestConnection:
    """连接测试类"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'connection': {
                'ip_address': '192.168.1.100',
                'port': 44818,
                'timeout': 5
            },
            'controller': {
                'model': 'EC-RTC12',
                'max_rotation': 330,
                'reduction_ratio': 45
            }
        }

    def test_eip_client_connect(self):
        """测试EIP客户端连接"""
        client = EIPClient('192.168.1.100')

        with patch.object(client, 'driver') as mock_driver:
            mock_driver.open.return_value = True

            result = client.connect()
            assert result is True
            assert client.connected is True

    def test_eip_client_disconnect(self):
        """测试EIP客户端断开"""
        client = EIPClient('192.168.1.100')
        client.connected = True

        with patch.object(client, 'driver') as mock_driver:
            client.disconnect()

            assert client.connected is False
            mock_driver.close.assert_called_once()

    def test_eip_client_read_tag(self):
        """测试读取标签"""
        client = EIPClient('192.168.1.100')
        client.connected = True

        mock_result = Mock()
        mock_result.value = 123.45

        with patch.object(client, 'driver') as mock_driver:
            mock_driver.read.return_value = mock_result

            value = client.read_tag('TestTag')
            assert value == 123.45
            mock_driver.read.assert_called_with('TestTag')

    def test_eip_client_write_tag(self):
        """测试写入标签"""
        client = EIPClient('192.168.1.100')
        client.connected = True

        with patch.object(client, 'driver') as mock_driver:
            mock_driver.write.return_value = True

            result = client.write_tag('TestTag', 100)
            assert result is True
            mock_driver.write.assert_called_with('TestTag', 100)

    def test_controller_connect(self, mock_config):
        """测试控制器连接"""
        controller = ECController(mock_config)

        with patch.object(controller.client, 'connect') as mock_connect:
            mock_connect.return_value = True

            result = controller.connect()
            assert result is True
            mock_connect.assert_called_once()

    def test_controller_disconnect(self, mock_config):
        """测试控制器断开"""
        controller = ECController(mock_config)

        with patch.object(controller.client, 'disconnect') as mock_disconnect:
            controller.disconnect()
            mock_disconnect.assert_called_once()

    def test_connection_timeout(self):
        """测试连接超时"""
        client = EIPClient('192.168.1.100')

        with patch.object(client, 'driver') as mock_driver:
            mock_driver.open.side_effect = TimeoutError("Connection timeout")

            result = client.connect()
            assert result is False
            assert client.connected is False

    def test_reconnect(self, mock_config):
        """测试重连"""
        controller = ECController(mock_config)

        with patch.object(controller.client, 'connect') as mock_connect:
            # 第一次连接失败
            mock_connect.return_value = False
            result1 = controller.connect()
            assert result1 is False

            # 第二次连接成功
            mock_connect.return_value = True
            result2 = controller.connect()
            assert result2 is True

            assert mock_connect.call_count == 2