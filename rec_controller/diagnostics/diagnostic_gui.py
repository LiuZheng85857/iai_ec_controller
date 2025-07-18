"""诊断GUI界面"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from .connection_test import ConnectionDiagnostics
from .network_scanner import NetworkScanner
import logging


class DiagnosticDialog(QDialog):
    """诊断对话框"""

    def __init__(self, ip_address: str = None, parent=None):
        super().__init__(parent)
        self.ip_address = ip_address or "192.168.0.1"
        self.diagnostics = None
        self.scanner = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("连接诊断工具")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 连接测试标签页
        self.test_tab = self.create_test_tab()
        self.tab_widget.addTab(self.test_tab, "连接测试")

        # 网络扫描标签页
        self.scan_tab = self.create_scan_tab()
        self.tab_widget.addTab(self.scan_tab, "网络扫描")

        layout.addWidget(self.tab_widget)

        # 按钮
        button_layout = QHBoxLayout()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)

        self.save_report_btn = QPushButton("保存报告")
        self.save_report_btn.clicked.connect(self.save_report)
        self.save_report_btn.setEnabled(False)

        button_layout.addStretch()
        button_layout.addWidget(self.save_report_btn)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def create_test_tab(self) -> QWidget:
        """创建连接测试标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # IP地址输入
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("目标IP地址:"))

        self.ip_edit = QLineEdit(self.ip_address)
        ip_layout.addWidget(self.ip_edit)

        self.test_btn = QPushButton("开始测试")
        self.test_btn.clicked.connect(self.start_test)
        ip_layout.addWidget(self.test_btn)

        layout.addLayout(ip_layout)

        # 测试进度
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        layout.addWidget(self.test_progress)

        # 测试结果树
        self.test_tree = QTreeWidget()
        self.test_tree.setHeaderLabels(["测试项", "状态", "详情"])
        self.test_tree.setColumnWidth(0, 200)
        self.test_tree.setColumnWidth(1, 100)
        layout.addWidget(self.test_tree)

        # 详细日志
        self.test_log = QTextEdit()
        self.test_log.setReadOnly(True)
        self.test_log.setMaximumHeight(150)
        layout.addWidget(self.test_log)

        return widget

    def create_scan_tab(self) -> QWidget:
        """创建网络扫描标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 扫描设置
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("子网:"))

        self.subnet_edit = QLineEdit("192.168.0.0/24")
        scan_layout.addWidget(self.subnet_edit)

        self.scan_btn = QPushButton("开始扫描")
        self.scan_btn.clicked.connect(self.start_scan)
        scan_layout.addWidget(self.scan_btn)

        self.stop_scan_btn = QPushButton("停止扫描")
        self.stop_scan_btn.clicked.connect(self.stop_scan)
        self.stop_scan_btn.setEnabled(False)
        scan_layout.addWidget(self.stop_scan_btn)

        layout.addLayout(scan_layout)

        # 扫描进度
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        layout.addWidget(self.scan_progress)

        # 扫描结果表格
        self.scan_table = QTableWidget()
        self.scan_table.setColumnCount(4)
        self.scan_table.setHorizontalHeaderLabels(["IP地址", "端口", "设备类型", "产品名称"])
        self.scan_table.horizontalHeader().setStretchLastSection(True)
        self.scan_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.scan_table.doubleClicked.connect(self.on_device_selected)
        layout.addWidget(self.scan_table)

        return widget

    @pyqtSlot()
    def start_test(self):
        """开始连接测试"""
        ip = self.ip_edit.text().strip()
        if not self._validate_ip(ip):
            QMessageBox.warning(self, "警告", "请输入有效的IP地址")
            return

        self.test_btn.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_tree.clear()
        self.test_log.clear()

        # 在线程中运行测试
        self.test_thread = TestThread(ip)
        self.test_thread.progress.connect(self.update_test_progress)
        self.test_thread.log.connect(self.append_test_log)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.start()

    @pyqtSlot(int, str, str)
    def update_test_progress(self, progress: int, test_name: str, status: str):
        """更新测试进度"""
        self.test_progress.setValue(progress)

        # 查找或创建测试项
        items = self.test_tree.findItems(test_name, Qt.MatchExactly, 0)
        if items:
            item = items[0]
        else:
            item = QTreeWidgetItem(self.test_tree)
            item.setText(0, test_name)

        # 设置状态
        item.setText(1, status)

        # 设置状态图标和颜色
        if status == "测试中...":
            item.setIcon(1, self.style().standardIcon(QStyle.SP_DialogResetButton))
        elif status == "通过":
            item.setIcon(1, self.style().standardIcon(QStyle.SP_DialogYesButton))
            item.setForeground(1, QBrush(Qt.green))
        elif status == "失败":
            item.setIcon(1, self.style().standardIcon(QStyle.SP_DialogNoButton))
            item.setForeground(1, QBrush(Qt.red))
        elif status == "部分通过":
            item.setIcon(1, self.style().standardIcon(QStyle.SP_MessageBoxWarning))
            item.setForeground(1, QBrush(QColor(255, 165, 0)))

    @pyqtSlot(str)
    def append_test_log(self, message: str):
        """添加测试日志"""
        self.test_log.append(message)

    @pyqtSlot(dict)
    def on_test_finished(self, results: dict):
        """测试完成"""
        self.test_btn.setEnabled(True)
        self.test_progress.setVisible(False)
        self.save_report_btn.setEnabled(True)

        # 显示详细结果
        for test_name, result in results.items():
            items = self.test_tree.findItems(self._get_test_display_name(test_name),
                                             Qt.MatchExactly, 0)
            if items:
                parent = items[0]
                parent.setText(2, result['message'])

                # 添加详细信息
                for key, value in result['details'].items():
                    if key == 'suggestion':
                        continue
                    child = QTreeWidgetItem(parent)
                    child.setText(0, key)
                    child.setText(2, str(value))

        self.test_tree.expandAll()

        # 生成报告
        diagnostics = ConnectionDiagnostics(self.ip_edit.text())
        diagnostics.test_results = results
        report = diagnostics.generate_report()
        self.test_log.append("\n" + "=" * 60)
        self.test_log.append(report)

    @pyqtSlot()
    def start_scan(self):
        """开始网络扫描"""
        subnet = self.subnet_edit.text().strip()

        self.scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        self.scan_progress.setVisible(True)
        self.scan_table.setRowCount(0)

        # 在线程中运行扫描
        self.scan_thread = ScanThread(subnet)
        self.scan_thread.progress.connect(self.scan_progress.setValue)
        self.scan_thread.device_found.connect(self.add_scan_result)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.start()

    @pyqtSlot()
    def stop_scan(self):
        """停止扫描"""
        if hasattr(self, 'scan_thread') and self.scan_thread.isRunning():
            self.scan_thread.stop()

    @pyqtSlot(dict)
    def add_scan_result(self, device: dict):
        """添加扫描结果"""
        row = self.scan_table.rowCount()
        self.scan_table.insertRow(row)

        self.scan_table.setItem(row, 0, QTableWidgetItem(device['ip']))
        self.scan_table.setItem(row, 1, QTableWidgetItem(str(device['port'])))
        self.scan_table.setItem(row, 2, QTableWidgetItem(device.get('device_type', 'Unknown')))
        self.scan_table.setItem(row, 3, QTableWidgetItem(device.get('product_name', '')))

    @pyqtSlot()
    def on_scan_finished(self):
        """扫描完成"""
        self.scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.scan_progress.setVisible(False)

        if self.scan_table.rowCount() == 0:
            QMessageBox.information(self, "扫描完成", "未找到任何设备")
        else:
            QMessageBox.information(self, "扫描完成",
                                    f"找到 {self.scan_table.rowCount()} 个设备")

    @pyqtSlot(QModelIndex)
    def on_device_selected(self, index: QModelIndex):
        """选择扫描到的设备"""
        row = index.row()
        ip = self.scan_table.item(row, 0).text()

        reply = QMessageBox.question(self, "确认",
                                     f"是否对 {ip} 进行连接测试？",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.tab_widget.setCurrentIndex(0)  # 切换到测试标签页
            self.ip_edit.setText(ip)
            self.start_test()

    @pyqtSlot()
    def save_report(self):
        """保存报告"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存诊断报告", "", "文本文件 (*.txt)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.test_log.toPlainText())
                QMessageBox.information(self, "成功", "报告已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def _validate_ip(self, ip: str) -> bool:
        """验证IP地址"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def _get_test_display_name(self, test_key: str) -> str:
        """获取测试显示名称"""
        names = {
            'network_adapter': '网络适配器检查',
            'ping': 'Ping连通性测试',
            'tcp_port': 'TCP端口扫描',
            'ethernet_ip': 'EtherNet/IP协议测试',
            'device_info': '设备信息获取',
            'communication': '通信功能测试'
        }
        return names.get(test_key, test_key)


class TestThread(QThread):
    """测试线程"""
    progress = pyqtSignal(int, str, str)  # 进度, 测试名称, 状态
    log = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, ip_address: str):
        super().__init__()
        self.ip_address = ip_address

    def run(self):
        """运行测试"""
        diagnostics = ConnectionDiagnostics(self.ip_address)

        tests = [
            ('network_adapter', '网络适配器检查'),
            ('ping', 'Ping连通性测试'),
            ('tcp_port', 'TCP端口扫描'),
            ('ethernet_ip', 'EtherNet/IP协议测试'),
            ('device_info', '设备信息获取'),
            ('communication', '通信功能测试')
        ]

        results = {}

        for i, (test_key, test_name) in enumerate(tests):
            # 更新进度
            progress = int((i / len(tests)) * 100)
            self.progress.emit(progress, test_name, "测试中...")
            self.log.emit(f"正在执行: {test_name}")

            # 执行测试
            method = getattr(diagnostics, f"test_{test_key}")
            result = method()
            results[test_key] = result

            # 更新状态
            status_map = {
                'pass': '通过',
                'fail': '失败',
                'partial': '部分通过',
                'error': '错误',
                'unknown': '未知'
            }
            status = status_map.get(result['status'], '未知')
            self.progress.emit(progress, test_name, status)
            self.log.emit(f"{test_name}: {status} - {result['message']}")

        # 完成
        self.progress.emit(100, "测试完成", "")
        self.finished.emit(results)


class ScanThread(QThread):
    """扫描线程"""
    progress = pyqtSignal(int)
    device_found = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, subnet: str):
        super().__init__()
        self.subnet = subnet
        self.scanner = NetworkScanner(subnet)

    def run(self):
        """运行扫描"""

        def progress_callback(value):
            self.progress.emit(value)

        def device_callback(device):
            self.device_found.emit(device)

        # 修改扫描器以支持实时回调
        original_results = self.scanner.results
        self.scanner.results = []

        class ResultsProxy(list):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            def append(self, item):
                super().append(item)
                self.callback(item)

        self.scanner.results = ResultsProxy(device_callback)

        # 执行扫描
        self.scanner.scan_network(progress_callback=progress_callback)

        self.finished.emit()

    def stop(self):
        """停止扫描"""
        if self.scanner:
            self.scanner.stop_scan()