"""主窗口"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from .control_panel import ControlPanel
from .status_panel import StatusPanel
from .config_dialog import ConfigDialog
from core.rec_controller import RECController
from utils.config_loader import load_config
import logging


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.controller = None
        self.config = load_config('config.yaml')
        self.logger = logging.getLogger(__name__)
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("REC控制器 - EC电缸控制系统")
        self.setGeometry(100, 100, 1200, 800)

        # 设置窗口图标
        self.setWindowIcon(QIcon('icon.png'))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建工具栏
        self.create_toolbar()

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 创建控制面板
        self.control_panel = ControlPanel()
        splitter.addWidget(self.control_panel)

        # 创建状态面板
        self.status_panel = StatusPanel()
        splitter.addWidget(self.status_panel)

        # 设置分割比例
        splitter.setSizes([600, 600])

        main_layout.addWidget(splitter)

        # 创建状态栏
        self.create_statusbar()

        # 连接信号
        self.control_panel.command_signal.connect(self.handle_command)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        #   诊断按钮
        diagnostic_action = QAction(QIcon('icons/diagnostic.png'), '诊断', self)
        diagnostic_action.triggered.connect(self.show_diagnostic_dialog)
        toolbar.addAction(diagnostic_action)

        # 连接动作
        connect_action = QAction(QIcon('icons/connect.png'), '连接', self)
        connect_action.triggered.connect(self.connect_controller)
        toolbar.addAction(connect_action)

        # 断开动作
        disconnect_action = QAction(QIcon('icons/disconnect.png'), '断开', self)
        disconnect_action.triggered.connect(self.disconnect_controller)
        toolbar.addAction(disconnect_action)

        toolbar.addSeparator()

        # 配置动作
        config_action = QAction(QIcon('icons/config.png'), '配置', self)
        config_action.triggered.connect(self.show_config_dialog)
        toolbar.addAction(config_action)

        toolbar.addSeparator()

        # 紧急停止
        estop_action = QAction(QIcon('icons/estop.png'), '紧急停止', self)
        estop_action.triggered.connect(self.emergency_stop)
        toolbar.addAction(estop_action)

    def show_diagnostic_dialog(self):
        """显示诊断对话框"""
        from diagnostics.diagnostic_gui import DiagnosticDialog

        ip = self.config['rec_controller']['ip_address']
        dialog = DiagnosticDialog(ip, self)
        dialog.exec_()

    def create_statusbar(self):
        """创建状态栏"""
        self.statusbar = self.statusBar()

        # 连接状态标签
        self.connection_label = QLabel("未连接")
        self.connection_label.setStyleSheet("QLabel { color: red; }")
        self.statusbar.addPermanentWidget(self.connection_label)

        # 模式标签
        self.mode_label = QLabel("模式: --")
        self.statusbar.addPermanentWidget(self.mode_label)

    def connect_controller(self):
        """连接控制器"""
        from gui.connection_dialog import ConnectionDialog
        
        # 显示连接选择对话框
        dialog = ConnectionDialog(self)
        if dialog.exec_():
            self.controller = dialog.controller
            if self.controller:
                self.connection_label.setText("已连接")
                self.connection_label.setStyleSheet("QLabel { color: green; }")
                self.control_panel.set_controller(self.controller)
                self.status_panel.set_controller(self.controller)
                self.status_panel.start_update()
                
                # 读取设备信息
                status = self.controller.read_gateway_status()
                if status:
                    mode = "MANU" if status['mod'] else "AUTO"
                    self.mode_label.setText(f"模式: {mode}")
                else:
                    self.mode_label.setText("模式: --")
            else:
                QMessageBox.critical(self, "错误", "连接失败")

    def disconnect_controller(self):
        """断开控制器"""
        if self.controller:
            self.status_panel.stop_update()
            self.controller.disconnect()
            self.controller = None
            self.connection_label.setText("未连接")
            self.connection_label.setStyleSheet("QLabel { color: red; }")
            self.mode_label.setText("模式: --")

    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = ConfigDialog(self.config, self)
        if dialog.exec_():
            self.config = dialog.get_config()
            # 保存配置
            import yaml
            with open('config.yaml', 'w') as f:
                yaml.dump(self.config, f)

    def emergency_stop(self):
        """紧急停止"""
        if self.controller:
            self.control_panel.emergency_stop_all()

    def handle_command(self, command: dict):
        """处理命令"""
        self.logger.info(f"执行命令: {command}")

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(self, '确认', '确定要退出吗？',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.controller:
                self.disconnect_controller()
            event.accept()
        else:
            event.ignore()