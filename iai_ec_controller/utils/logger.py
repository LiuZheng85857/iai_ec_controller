"""
日志记录工具
提供统一的日志记录接口
"""
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Optional


class LogManager:
    """日志管理器"""

    def __init__(self, log_file: Optional[str] = None, level: str = "INFO"):
        """
        初始化日志管理器

        Args:
            log_file: 日志文件路径
            level: 日志级别
        """
        self.log_file = log_file or f"logs/ec_control_{datetime.now():%Y%m%d}.log"
        self.level = level
        self._setup()

    def _setup(self):
        """设置日志配置"""
        # 移除默认处理器
        logger.remove()

        # 添加控制台输出
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            level=self.level,
            colorize=True
        )

        # 确保日志目录存在
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        # 添加文件输出
        logger.add(
            self.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=self.level,
            rotation="10 MB",  # 文件大小达到10MB时轮转
            retention="7 days",  # 保留7天
            compression="zip",  # 压缩旧日志
            encoding="utf-8"
        )

    def get_logger(self):
        """获取logger实例"""
        return logger


# 创建全局日志实例
log_manager = LogManager()
get_logger = log_manager.get_logger