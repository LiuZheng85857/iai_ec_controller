"""控制面板"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from core.rec_controller import RECController
from core.ec_actuator import ECActuator
from commands.basic_commands import BasicCommands


class ControlPanel(QWidget):
    """控制面板类"""

    command_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.controller = None
        self.actuators = {}
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("控制面板")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; }")
        layout.addWidget(title)

        # 轴选择
        axis_group = QGroupBox("轴选择")
        axis_layout = QGridLayout()

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["单元0", "单元1", "单元2", "单元3"])
        axis_layout.addWidget(QLabel("单元:"), 0, 0)
        axis_layout.addWidget(self.unit_combo, 0, 1)

        self.axis_combo = QComboBox()
        self.axis_combo.addItems(["轴0", "轴1", "轴2", "轴3"])
        axis_layout.addWidget(QLabel("轴号:"), 1, 0)
        axis_layout.addWidget(self.axis_combo, 1, 1)

        axis_group.setLayout(axis_layout)
        layout.addWidget(axis_group)

        # 基本控制
        basic_group = QGroupBox("基本控制")
        basic_layout = QGridLayout()

        # 初始化按钮
        self.init_btn = QPushButton("初始化(原点复归)")
        self.init_btn.clicked.connect(self.initialize_axis)
        basic_layout.addWidget(self.init_btn, 0, 0, 1, 2)

        # 点动控制
        self.jog_backward_btn = QPushButton("← 点动后退")
        self.jog_forward_btn = QPushButton("点动前进 →")
        self.jog_backward_btn.pressed.connect(self.jog_backward_start)
        self.jog_backward_btn.released.connect(self.jog_stop)
        self.jog_forward_btn.pressed.connect(self.jog_forward_start)
        self.jog_forward_btn.released.connect(self.jog_stop)

        basic_layout.addWidget(self.jog_backward_btn, 1, 0)
        basic_layout.addWidget(self.jog_forward_btn, 1, 1)

        # 位置移动
        self.move_backward_btn = QPushButton("移动到后退端")
        self.move_forward_btn = QPushButton("移动到前进端")
        self.move_backward_btn.clicked.connect(self.move_to_backward)
        self.move_forward_btn.clicked.connect(self.move_to_forward)

        basic_layout.addWidget(self.move_backward_btn, 2, 0)
        basic_layout.addWidget(self.move_forward_btn, 2, 1)

        # 停止按钮
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #ff6666; }")
        self.stop_btn.clicked.connect(self.stop_axis)
        basic_layout.addWidget(self.stop_btn, 3, 0, 1, 2)

        # 复位按钮
        self.reset_btn = QPushButton("报警复位")
        self.reset_btn.clicked.connect(self.reset_alarm)
        basic_layout.addWidget(self.reset_btn, 4, 0, 1, 2)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 循环运动
        cycle_group = QGroupBox("循环运动")
        cycle_layout = QGridLayout()

        self.cycle_count_spin = QSpinBox()
        self.cycle_count_spin.setRange(1, 9999)
        self.cycle_count_spin.setValue(1)
        cycle_layout.addWidget(QLabel("循环次数:"), 0, 0)
        cycle_layout.addWidget(self.cycle_count_spin, 0, 1)

        self.dwell_time_spin = QDoubleSpinBox()
        self.dwell_time_spin.setRange(0.0, 10.0)
        self.dwell_time_spin.setValue(0.5)
        self.dwell_time_spin.setSingleStep(0.1)
        self.dwell_time_spin.setSuffix(" 秒")
        cycle_layout.addWidget(QLabel("停留时间:"), 1, 0)
        cycle_layout.addWidget(self.dwell_time_spin, 1, 1)

        self.cycle_start_btn = QPushButton("开始循环")
        self.cycle_stop_btn = QPushButton("停止循环")
        self.cycle_start_btn.clicked.connect(self.start_cycle)
        self.cycle_stop_btn.clicked.connect(self.stop_cycle)

        cycle_layout.addWidget(self.cycle_start_btn, 2, 0)
        cycle_layout.addWidget(self.cycle_stop_btn, 2, 1)

        cycle_group.setLayout(cycle_layout)
        layout.addWidget(cycle_group)

        # 添加弹簧
        layout.addStretch()

        # 初始状态
        self.set_enabled(False)

    def set_controller(self, controller: RECController):
        """设置控制器"""
        self.controller = controller
        self.set_enabled(True)

    def set_enabled(self, enabled: bool):
        """设置控件启用状态"""
        for widget in self.findChildren(QPushButton):
            widget.setEnabled(enabled)
        for widget in self.findChildren(QComboBox):
            widget.setEnabled(enabled)
        for widget in self.findChildren(QSpinBox):
            widget.setEnabled(enabled)
        for widget in self.findChildren(QDoubleSpinBox):
            widget.setEnabled(enabled)

    def get_current_axis(self) -> tuple:
        """获取当前选择的轴"""
        unit_index = self.unit_combo.currentIndex()
        axis_index = self.axis_combo.currentIndex()
        return unit_index, axis_index

    def get_actuator(self) -> ECActuator:
        """获取当前轴的执行器"""
        unit_index, axis_index = self.get_current_axis()
        key = f"{unit_index}_{axis_index}"

        if key not in self.actuators:
            self.actuators[key] = ECActuator(self.controller, unit_index, axis_index)

        return self.actuators[key]

    @pyqtSlot()
    def initialize_axis(self):
        """初始化轴"""
        actuator = self.get_actuator()
        commands = BasicCommands(actuator)

        # 在线程中执行
        self.worker = Worker(commands.initialize)
        self.worker.finished.connect(lambda success:
                                     QMessageBox.information(self, "完成", "初始化完成" if success else "初始化失败"))
        self.worker.start()

    @pyqtSlot()
    def jog_forward_start(self):
        """开始点动前进"""
        actuator = self.get_actuator()
        actuator.move_forward()

    @pyqtSlot()
    def jog_backward_start(self):
        """开始点动后退"""
        actuator = self.get_actuator()
        actuator.move_backward()

    @pyqtSlot()
    def jog_stop(self):
        """停止点动"""
        actuator = self.get_actuator()
        actuator.stop()

    @pyqtSlot()
    def move_to_forward(self):
        """移动到前进端"""
        actuator = self.get_actuator()
        commands = BasicCommands(actuator)

        self.worker = Worker(commands.move_to_forward_end)
        self.worker.start()

    @pyqtSlot()
    def move_to_backward(self):
        """移动到后退端"""
        actuator = self.get_actuator()
        commands = BasicCommands(actuator)

        self.worker = Worker(commands.move_to_backward_end)
        self.worker.start()

    @pyqtSlot()
    def stop_axis(self):
        """停止轴"""
        actuator = self.get_actuator()
        actuator.stop()

    @pyqtSlot()
    def reset_alarm(self):
        """复位报警"""
        actuator = self.get_actuator()
        actuator.reset_alarm()

    @pyqtSlot()
    def start_cycle(self):
        """开始循环"""
        from commands.position_commands import PositionCommands
        actuator = self.get_actuator()
        commands = PositionCommands(actuator)

        cycles = self.cycle_count_spin.value()
        dwell = self.dwell_time_spin.value()

        self.cycle_worker = Worker(lambda: commands.cycle_motion(cycles, dwell))
        self.cycle_worker.start()

    @pyqtSlot()
    def stop_cycle(self):
        """停止循环"""
        if hasattr(self, 'cycle_worker'):
            self.cycle_worker.terminate()
        self.stop_axis()

    def emergency_stop_all(self):
        """紧急停止所有轴"""
        if self.controller:
            for unit in range(4):
                for axis in range(4):
                    self.controller.send_axis_command(unit, axis, 'ST0', False)
                    self.controller.send_axis_command(unit, axis, 'ST1', False)


class Worker(QThread):
    """工作线程"""
    finished = pyqtSignal(bool)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            result = self.func()
            self.finished.emit(result if result is not None else True)
        except Exception as e:
            print(f"Worker error: {e}")
            self.finished.emit(False)