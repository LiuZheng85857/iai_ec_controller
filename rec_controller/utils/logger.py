"""日志配置"""
import logging
import sys


def setup_logger(config: dict):
    """设置日志记录器"""
    level = getattr(logging, config.get('level', 'INFO'))

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 添加文件处理器
    if 'file' in config:
        file_handler = logging.FileHandler(config['file'], encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)