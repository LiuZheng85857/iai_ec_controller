"""配置对话框"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ConfigDialog(QDialog):
    """配置对话框"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("系统配置")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # 创建标签页
        tab_widget = QTabWidget()

        # REC控制器配置
        rec_tab = QWidget()
        rec_layout = QFormLayout(rec_tab)

        self.ip_edit = QLineEdit(self.config['rec_controller']['ip_address'])
        self.subnet_edit = QLineEdit(self.config['rec_controller']['subnet_mask'])
        self.gateway_edit = QLineEdit(self.config['rec_controller']['gateway'])

        rec_layout.addRow("IP地址:", self.ip_edit)
        rec_layout.addRow("子网掩码:", self.subnet_edit)
        rec_layout.addRow("网关:", self.gateway_edit)

        tab_widget.addTab(rec_tab, "REC控制器")

        # EC单元配置
        ec_tab = QWidget()
        ec_layout = QFormLayout(ec_tab)

        self.unit_count_spin = QSpinBox()
        self.unit_count_spin.setRange(1, 4)
        self.unit_count_spin.setValue(self.config['ec_units']['count'])

        ec_layout.addRow("EC接续单元数量:", self.unit_count_spin)

        tab_widget.addTab(ec_tab, "EC单元")

        # 通信配置
        comm_tab = QWidget()
        comm_layout = QFormLayout(comm_tab)

        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 10.0)
        self.timeout_spin.setValue(self.config['communication']['timeout'])
        self.timeout_spin.setSingleStep(0.1)
        self.timeout_spin.setSuffix(" 秒")

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(self.config['communication']['retry_count'])

        comm_layout.addRow("超时时间:", self.timeout_spin)
        comm_layout.addRow("重试次数:", self.retry_spin)

        tab_widget.addTab(comm_tab, "通信")

        layout.addWidget(tab_widget)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def get_config(self) -> dict:
        """获取配置"""
        self.config['rec_controller']['ip_address'] = self.ip_edit.text()
        self.config['rec_controller']['subnet_mask'] = self.subnet_edit.text()
        self.config['rec_controller']['gateway'] = self.gateway_edit.text()
        self.config['ec_units']['count'] = self.unit_count_spin.value()
        self.config['communication']['timeout'] = self.timeout_spin.value()
        self.config['communication']['retry_count'] = self.retry_spin.value()

        return self.config