"""REC控制器主程序"""
import sys
import time
import logging
from core.rec_controller import RECController
from core.ec_actuator import ECActuator
from utils.config_loader import load_config
from utils.logger import setup_logger


def main():
    # 加载配置
    config = load_config('config.yaml')

    # 设置日志
    setup_logger(config['logging'])
    logger = logging.getLogger(__name__)

    # 创建REC控制器实例
    controller = RECController(
        ip_address=config['rec_controller']['ip_address'],
        unit_count=config['ec_units']['count']
    )

    try:
        # 连接到控制器
        if not controller.connect():
            logger.error("无法连接到REC控制器")
            return

        # 读取网关状态
        gateway_status = controller.read_gateway_status()
        if gateway_status:
            logger.info(f"网关状态: {gateway_status}")

            # 检查是否在MANU模式
            if not gateway_status['mod']:
                logger.warning("控制器在AUTO模式，某些操作可能受限")

        # 创建第一个轴的控制实例
        axis1 = ECActuator(controller, unit_index=0, axis_index=0)

        # 执行原点复归
        logger.info("执行原点复归...")
        if axis1.home():
            logger.info("原点复归完成")
        else:
            logger.error("原点复归失败")
            return

        # 执行基本运动测试
        logger.info("开始运动测试...")

        # 前进
        logger.info("前进到前进端...")
        axis1.move_forward()
        if axis1.wait_for_position('forward'):
            logger.info("到达前进端")
        axis1.stop()

        time.sleep(1)

        # 后退
        logger.info("后退到后退端...")
        axis1.move_backward()
        if axis1.wait_for_position('backward'):
            logger.info("到达后退端")
        axis1.stop()

    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        # 断开连接
        controller.disconnect()
        logger.info("程序结束")


if __name__ == "__main__":
    main()