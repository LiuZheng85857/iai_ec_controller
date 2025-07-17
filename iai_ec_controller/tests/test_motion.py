"""
运动控制测试模块
"""
import pytest
import time
from unittest.mock import Mock, patch, call
from core.ec_controller import ECController
from commands.motion import MotionCommands


class TestMotion:
    """运动控制测试类"""

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
            },
            'motion': {
                'default_speed': 100,
                'default_acceleration': 0.3,
                'default_deceleration': 0.3
            }
        }

    @pytest.fixture
    def mock_controller(self, mock_config):
        """模拟控制器"""
        controller = ECController(mock_config)
        controller.client = Mock()
        controller.client.connected = True
        controller.is_homing_complete = True
        return controller

    def test_home_operation(self, mock_controller):
        """测试原点复位"""
        # 设置模拟返回值
        mock_controller.client.write_tag.return_value = True
        mock_controller.client.read_tag.side_effect = [
            False,  # home_complete (第1次)
            False,  # home_complete (第2次)
            True,  # home_complete (第3次)
        ]

        # 执行原点复位
        result = mock_controller.home()

        # 验证结果
        assert result is True
        assert mock_controller.is_homing_complete is True

        # 验证调用
        calls = mock_controller.client.write_tag.call_args_list
        assert calls[0] == call(mock_controller.SIGNALS['ST0'], True)
        assert calls[-1] == call(mock_controller.SIGNALS['ST0'], False)

    def test_move_to_position(self, mock_controller):
        """测试位置移动"""
        # 设置当前位置
        mock_controller.client.read_tag.side_effect = [
            50.0,  # current_position
            False,  # LS1 (第1次)
            False,  # ALM check
            True,  # LS1 (第2次)
        ]
        mock_controller.client.write_tag.return_value = True

        # 移动到100度
        result = mock_controller.move_to_position(100, speed=200)

        # 验证结果
        assert result is True

        # 验证参数设置
        calls = mock_controller.client.write_tag.call_args_list
        assert call(mock_controller.PARAMETERS['speed'], 200) in calls
        assert call(mock_controller.PARAMETERS['target_position'], 100) in calls
        assert call(mock_controller.SIGNALS['ST1'], True) in calls
        assert call(mock_controller.SIGNALS['ST1'], False) in calls

    def test_jog_operation(self, mock_controller):
        """测试点动操作"""
        motion = MotionCommands(mock_controller)

        # 正向点动
        result = motion.jog_forward(speed=50)
        assert result is True
        mock_controller.client.write_tag.assert_any_call(
            mock_controller.PARAMETERS['speed'], 50
        )
        mock_controller.client.write_tag.assert_any_call(
            mock_controller.SIGNALS['ST1'], True
        )

        # 停止点动
        motion.stop_jog()
        mock_controller.client.write_tag.assert_any_call(
            mock_controller.SIGNALS['ST0'], False
        )
        mock_controller.client.write_tag.assert_any_call(
            mock_controller.SIGNALS['ST1'], False
        )

    def test_move_sequence(self, mock_controller):
        """测试序列移动"""
        motion = MotionCommands(mock_controller)

        # 模拟成功的移动
        mock_controller.move_to_position = Mock(return_value=True)

        # 执行序列移动
        positions = [90, 180, 270, 0]
        result = motion.move_sequence(positions, speed=150, dwell_time=0.1)

        # 验证结果
        assert result is True
        assert mock_controller.move_to_position.call_count == 4

        # 验证调用参数
        for i, pos in enumerate(positions):
            assert mock_controller.move_to_position.call_args_list[i] == call(pos, 150)

    def test_push_operation(self, mock_controller):
        """测试推压操作"""
        motion = MotionCommands(mock_controller)
        mock_controller.client.write_tag.return_value = True
        mock_controller.move_to_position = Mock(return_value=True)

        # 执行推压
        result = motion.push_operation(push_position=45, push_force=50)

        # 验证结果
        assert result is True

        # 验证推压参数设置
        calls = mock_controller.client.write_tag.call_args_list
        assert call('Controller.PushForce', 50) in calls
        assert call('Controller.PushPosition', 45) in calls
        assert call('Controller.PushMode', True) in calls
        assert call('Controller.PushMode', False) in calls

    def test_invalid_position(self, mock_controller):
        """测试无效位置"""
        # 超出范围的位置
        result = mock_controller.move_to_position(400)  # 超过330度
        assert result is False

        # 负数位置
        result = mock_controller.move_to_position(-10)
        assert result is False

    def test_invalid_speed(self, mock_controller):
        """测试无效速度"""
        # 速度过低
        result = mock_controller.move_to_position(100, speed=10)  # 低于20度/秒
        assert result is False

        # 速度过高
        result = mock_controller.move_to_position(100, speed=700)  # 超过600度/秒
        assert result is False

    def test_alarm_during_motion(self, mock_controller):
        """测试运动中发生报警"""
        # 设置报警状态
        mock_controller.client.read_tag.side_effect = [
            50.0,  # current_position
            False,  # LS1
            False,  # ALM (正常) - 用于_check_alarm返回True
            False,  # LS1
            False,  # ALM (报警) - 用于_check_alarm返回True
        ]
        mock_controller._check_alarm = Mock(side_effect=[False, True])

        # 尝试移动
        result = mock_controller.move_to_position(100)

        # 验证结果
        assert result is False

        # 验证停止信号
        mock_controller.client.write_tag.assert_any_call(
            mock_controller.SIGNALS['ST1'], False
        )

    def test_timeout_during_motion(self, mock_controller):
        """测试运动超时"""
        # 设置永远不到达
        mock_controller.client.read_tag.return_value = False
        mock_controller._check_alarm = Mock(return_value=False)

        # 使用较短的超时进行测试
        with patch('time.time', side_effect=[0, 0.1, 0.2, 61]):  # 模拟超时
            result = mock_controller.move_to_position(100)

        # 验证结果
        assert result is False