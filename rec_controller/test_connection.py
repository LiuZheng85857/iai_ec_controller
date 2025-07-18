"""连接测试主程序"""
import sys
import argparse
from PyQt5.QtWidgets import QApplication
from diagnostics.diagnostic_gui import DiagnosticDialog
from diagnostics.connection_test import ConnectionDiagnostics
from utils.logger import setup_logger
import logging


def run_cli_test(ip_address: str):
    """运行命令行测试"""
    print(f"开始测试连接到 {ip_address}")
    print("=" * 60)

    diagnostics = ConnectionDiagnostics(ip_address)

    # 运行所有测试
    print("正在执行测试...")
    results = diagnostics.run_all_tests()

    # 打印报告
    report = diagnostics.generate_report()
    print(report)

    # 返回是否所有测试通过
    all_passed = all(r['status'] == 'pass' for r in results.values())
    return 0 if all_passed else 1


def run_gui_test(ip_address: str = None):
    """运行GUI测试"""
    app = QApplication(sys.argv)
    app.setApplicationName("REC连接诊断工具")

    dialog = DiagnosticDialog(ip_address)
    dialog.show()

    sys.exit(app.exec_())


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='REC控制器连接诊断工具')
    parser.add_argument('ip', nargs='?', default='192.168.0.1',
                        help='目标IP地址 (默认: 192.168.0.1)')
    parser.add_argument('--cli', action='store_true',
                        help='使用命令行模式')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细日志')

    args = parser.parse_args()

    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if args.cli:
        # 命令行模式
        return run_cli_test(args.ip)
    else:
        # GUI模式
        run_gui_test(args.ip)


if __name__ == "__main__":
    sys.exit(main())