"""状态显示面板"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from core.rec_controller import RECController
from commands.status_commands import StatusCommands


class StatusPanel(QWidget):
    """状态显示面板"""

    def __init__(self):
        super().__init__()
        self.controller = None
        self.status_commands = None
        self.init_ui()

        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("状态监控")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; }")
        layout.addWidget(title)

        # 网关状态
        gateway_group = QGroupBox("网关状态")
        gateway_layout = QFormLayout()

        self.gateway_status_led = StatusLED()
        self.mode_label = QLabel("--")
        self.alarm_code_label = QLabel("--")

        gateway_layout.addRow("状态:", self.gateway_status_led)
        gateway_layout.addRow("模式:", self.mode_label)
        gateway_layout.addRow("报警代码:", self.alarm_code_label)

        gateway_group.setLayout(gateway_layout)
        layout.addWidget(gateway_group)

        # 轴状态表格
        axes_group = QGroupBox("轴状态")
        axes_layout = QVBoxLayout()

        # 创建表格
        self.axes_table = QTableWidget()
        self.axes_table.setColumnCount(6)
        self.axes_table.setHorizontalHeaderLabels([
            "单元/轴", "准备就绪", "后退端", "前进端", "报警", "状态"
        ])
        self.axes_table.horizontalHeader().setStretchLastSection(True)

        axes_layout.addWidget(self.axes_table)
        axes_group.setLayout(axes_layout)
        layout.addWidget(axes_group)

        # 初始化表格行
        self.init_axes_table()

    def init_axes_table(self):
        """初始化轴状态表格"""
        rows = []
        for unit in range(4):
            for axis in range(4):
                rows.append(f"单元{unit}/轴{axis}")

        self.axes_table.setRowCount(len(rows))

        for i, row_name in enumerate(rows):
            # 名称
            self.axes_table.setItem(i, 0, QTableWidgetItem(row_name))

            # LED指示器
            for col in range(1, 5):
                led = StatusLED()
                self.axes_table.setCellWidget(i, col, led)

            # 状态文本
            self.axes_table.setItem(i, 5, QTableWidgetItem("--"))

    def set_controller(self, controller: RECController):
        """设置控制器"""
        self.controller = controller
        self.status_commands = StatusCommands(controller)

    def start_update(self):
        """开始更新"""
        self.update_timer.start(200)  # 200ms更新一次

    def stop_update(self):
        """停止更新"""
        self.update_timer.stop()

    @pyqtSlot()
    def update_status(self):
        """更新状态"""
        if not self.controller or not self.status_commands:
            return

        try:
            # 更新网关状态
            gateway_status = self.status_commands.get_gateway_status()
            if gateway_status:
                self.gateway_status_led.set_status(not gateway_status['almh'])
                self.mode_label.setText("MANU" if gateway_status['mod'] else "AUTO")
                self.alarm_code_label.setText(str(gateway_status['alarm_code']))

            # 更新轴状态
            for unit in range(4):
                for axis in range(4):
                    row = unit * 4 + axis
                    try:
                        status = self.status_commands.get_axis_status(unit, axis)

                        if status:
                            # 准备就绪
                            led = self.axes_table.cellWidget(row, 1)
                            if led:
                                led.set_status(status.get('ready', False))

                            # 后退端（使用busy状态作为替代）
                            led = self.axes_table.cellWidget(row, 2)
                            if led:
                                led.set_status(status.get('busy', False))

                            # 前进端（使用done状态作为替代）
                            led = self.axes_table.cellWidget(row, 3)
                            if led:
                                led.set_status(status.get('done', False))

                            # 报警
                            led = self.axes_table.cellWidget(row, 4)
                            if led:
                                led.set_status(status.get('alarm', False), alarm=True)

                            # 状态文本
                            status_text = self.get_status_text(status)
                            item = self.axes_table.item(row, 5)
                            if item:
                                item.setText(status_text)
                    except Exception as e:
                        # 静默处理单个轴的错误，避免影响其他轴
                        pass
        except Exception as e:
            # 静默处理更新错误，避免频繁的错误日志
            pass

    def get_status_text(self, status: dict) -> str:
        """获取状态文本"""
        if status.get('alarm', False):
            return "报警"
        elif not status.get('ready', False):
            return "未就绪"
        elif status.get('busy', False):
            return "忙碌"
        elif status.get('done', False):
            return "完成"
        elif status.get('error', False):
            return "错误"
        else:
            return "运行中"


class StatusLED(QWidget):
    """状态LED指示器"""

    def __init__(self, size=20):
        super().__init__()
        self.size = size
        self.status = False
        self.alarm = False
        self.setFixedSize(size, size)

    def set_status(self, status: bool, alarm: bool = False):
        """设置状态"""
        self.status = status
        self.alarm = alarm
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 选择颜色
        if self.alarm and self.status:
            color = QColor(255, 0, 0)  # 红色 - 报警
        elif self.status:
            color = QColor(0, 255, 0)  # 绿色 - 正常
        else:
            color = QColor(128, 128, 128)  # 灰色 - 关闭

        # 绘制LED
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(2, 2, self.size - 4, self.size - 4)