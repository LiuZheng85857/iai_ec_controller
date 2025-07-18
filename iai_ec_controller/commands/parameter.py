"""
参数设置命令模块
用于读取和设置电缸参数
"""
from typing import Dict, Any, Optional
from loguru import logger
from utils.converter import Converter


class ParameterCommands:
    """参数命令类"""

    # 参数编号定义（根据说明书）
    PARAM_IDS = {
        'motion_range': 1,          # 动作范围调整
        'ls_detection_range': 2,    # LS信号检测范围
        'home_direction': 3,        # 原点复位方向
        'home_offset': 4,           # 原点位置调整
        'smooth_motion': 5,         # 平滑加减速
        'stop_current_mode': 6,     # 停止时电流抑制
        'wireless_function': 7,     # 无线功能
        'power_save': 8,            # 省电设定
    }

    def __init__(self, controller):
        """
        初始化参数命令

        Args:
            controller: EC控制器实例
        """
        self.controller = controller
        self.converter = Converter()

    def read_parameter(self, param_name: str) -> Optional[Any]:
        """
        读取参数

        Args:
            param_name: 参数名称

        Returns:
            参数值，失败返回None
        """
        if param_name not in self.PARAM_IDS:
            logger.error(f"未知参数: {param_name}")
            return None

        param_id = self.PARAM_IDS[param_name]
        tag_name = f"Controller.Parameter{param_id}"

        value = self.controller.client.read_tag(tag_name)
        if value is not None:
            logger.info(f"读取参数 {param_name} = {value}")
        else:
            logger.error(f"读取参数 {param_name} 失败")

        return value

    def write_parameter(self, param_name: str, value: Any) -> bool:
        """
        写入参数

        Args:
            param_name: 参数名称
            value: 参数值

        Returns:
            bool: 成功返回True
        """
        if param_name not in self.PARAM_IDS:
            logger.error(f"未知参数: {param_name}")
            return False

        # 验证参数值
        if not self._validate_parameter(param_name, value):
            return False

        param_id = self.PARAM_IDS[param_name]
        tag_name = f"Controller.Parameter{param_id}"

        if self.controller.client.write_tag(tag_name, value):
            logger.info(f"设置参数 {param_name} = {value}")
            logger.warning("参数更改后需要重启控制器才能生效")
            return True
        else:
            logger.error(f"设置参数 {param_name} 失败")
            return False

    def read_all_parameters(self) -> Dict[str, Any]:
        """
        读取所有参数

        Returns:
            Dict[str, Any]: 参数字典
        """
        params = {}
        for name in self.PARAM_IDS:
            value = self.read_parameter(name)
            if value is not None:
                params[name] = value
        return params

    def backup_parameters(self, filename: str = "parameters_backup.yaml"):
        """
        备份参数到文件

        Args:
            filename: 备份文件名
        """
        import yaml
        from datetime import datetime

        params = self.read_all_parameters()
        params['backup_time'] = datetime.now().isoformat()
        params['controller_model'] = self.controller.config['controller']['model']

        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(params, f, allow_unicode=True)

        logger.info(f"参数已备份到 {filename}")

    def restore_parameters(self, filename: str = "parameters_backup.yaml") -> bool:
        """
        从文件恢复参数

        Args:
            filename: 备份文件名

        Returns:
            bool: 成功返回True
        """
        import yaml

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                params = yaml.safe_load(f)

            # 移除非参数项
            params.pop('backup_time', None)
            params.pop('controller_model', None)

            # 逐个恢复参数
            success_count = 0
            for name, value in params.items():
                if self.write_parameter(name, value):
                    success_count += 1

            logger.info(f"成功恢复 {success_count}/{len(params)} 个参数")
            return success_count == len(params)

        except Exception as e:
            logger.error(f"恢复参数失败: {e}")
            return False

    def set_motion_range(self, max_angle: float) -> bool:
        """
        设置动作范围

        Args:
            max_angle: 最大角度(0-330度)

        Returns:
            bool: 成功返回True
        """
        return self.write_parameter('motion_range', max_angle)

    def set_ls_detection_range(self, range_degree: float) -> bool:
        """
        设置LS信号检测范围

        Args:
            range_degree: 检测范围(度)

        Returns:
            bool: 成功返回True
        """
        return self.write_parameter('ls_detection_range', range_degree)

    def set_smooth_motion(self, enable: bool) -> bool:
        """
        设置平滑加减速

        Args:
            enable: 是否启用

        Returns:
            bool: 成功返回True
        """
        return self.write_parameter('smooth_motion', 1 if enable else 0)

    def set_power_save(self, enable: bool) -> bool:
        """
        设置省电模式

        Args:
            enable: 是否启用

        Returns:
            bool: 成功返回True
        """
        if enable:
            logger.warning("启用省电模式会降低最大速度和扭矩")
        return self.write_parameter('power_save', 1 if enable else 0)

    def _validate_parameter(self, param_name: str, value: Any) -> bool:
        """
        验证参数值

        Args:
            param_name: 参数名称
            value: 参数值

        Returns:
            bool: 有效返回True
        """
        if param_name == 'motion_range':
            if not 0 <= value <= 330:
                logger.error(f"动作范围必须在0-330度之间")
                return False

        elif param_name == 'ls_detection_range':
            min_resolution = 360 / 45 / 800  # 最小分辨率
            if value < min_resolution:
                logger.error(f"检测范围不能小于最小分辨率 {min_resolution:.4f}度")
                return False

        elif param_name == 'home_direction':
            if value not in [0, 1]:  # 0=反向, 1=正向
                logger.error("原点复位方向必须为0(反向)或1(正向)")
                return False

        elif param_name in ['smooth_motion', 'stop_current_mode',
                           'wireless_function', 'power_save']:
            if value not in [0, 1]:
                logger.error(f"{param_name} 必须为0(无效)或1(有效)")
                return False

        return True