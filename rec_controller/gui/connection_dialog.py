"""连接选择对话框"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from core.serial_comm import SerialClient
from core.rec_controller import RECController


class ConnectionDialog(QDialog):
    """连接选择对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("通信端口选择")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # 提示标签
        label = QLabel("请选择通信端口。")
        layout.addWidget(label)

        # 创建分割窗口
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：端口列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("通信端口一览"))

        self.port_list = QListWidget()
        left_layout.addWidget(self.port_list)

        # 右侧：状态显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        right_layout.addWidget(QLabel("状态"))

        self.status_list = QListWidget()
        right_layout.addWidget(self.status_list)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter)

        # 按钮
        button_layout = QHBoxLayout()

        self.back_btn = QPushButton("← 返回")
        self.back_btn.clicked.connect(self.reject)

        self.refresh_btn = QPushButton("🔍 重新搜索")
        self.refresh_btn.clicked.connect(self.refresh_ports)

        self.connect_btn = QPushButton("✏️ 通信开始")
        self.connect_btn.clicked.connect(self.start_connection)

        button_layout.addWidget(self.back_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.connect_btn)

        layout.addLayout(button_layout)

        # 提示
        tip_label = QLabel("💡 请点击处...")
        tip_label.setStyleSheet("QLabel { color: blue; }")
        layout.addWidget(tip_label)

        # 连接信号
        self.port_list.itemClicked.connect(self.on_port_selected)
        
        # 初始化端口列表
        self.refresh_ports()

    def refresh_ports(self):
        """刷新端口列表"""
        self.port_list.clear()
        self.status_list.clear()

        # 获取串口列表
        ports = SerialClient.list_ports()

        for port, desc in ports:
            item = QListWidgetItem(f"{port}")
            self.port_list.addItem(item)

        # 添加网络选项
        network_item = QListWidgetItem("EtherNet/IP (192.168.0.1)")
        network_item.setData(Qt.UserRole, "network")
        self.port_list.addItem(network_item)

    def on_port_selected(self, item):
        """选择端口时的处理"""
        self.status_list.clear()

        if item.data(Qt.UserRole) == "network":
            # 网络连接
            self.status_list.addItem("EtherNet/IP")
            self.status_list.addItem("IP: 192.168.0.1")
        else:
            # 串口连接
            port = item.text()
            self.status_list.addItem(f"{port}")

            # 尝试识别设备
            controller = RECController(
                comm_type=RECController.COMM_SERIAL,
                port=port
            )

            if controller.connect():
                self.status_list.addItem("GW No.0 REC-GW")
                self.status_list.addItem("轴No.0 EC")
                controller.disconnect()
            else:
                self.status_list.addItem("连接失败")

    def start_connection(self):
        """开始连接"""
        current_item = self.port_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择通信端口")
            return

        if current_item.data(Qt.UserRole) == "network":
            # 网络连接
            self.controller = RECController(
                comm_type=RECController.COMM_ETHERNET_IP,
                ip_address='192.168.0.1'
            )
        else:
            # 串口连接
            port = current_item.text()
            self.controller = RECController(
                comm_type=RECController.COMM_SERIAL,
                port=port
            )

        if self.controller.connect():
            self.accept()
        else:
            QMessageBox.critical(self, "错误", "连接失败")