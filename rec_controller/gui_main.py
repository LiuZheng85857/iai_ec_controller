"""GUI主程序入口"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from gui.main_window import MainWindow
from utils.logger import setup_logger
from utils.config_loader import load_config


def main():
    """GUI主程序"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("REC Controller")
    app.setOrganizationName("IAI")

    # 设置应用样式
    app.setStyle('Fusion')

    # 显示启动画面
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.white)
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage("正在加载...", Qt.AlignBottom | Qt.AlignCenter, Qt.black)
    app.processEvents()

    # 加载配置
    config = load_config('config.yaml')
    setup_logger(config['logging'])

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 关闭启动画面
    splash.finish(window)

    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()