"""
IAI EC电缸控制程序主入口
"""
import sys
import os
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import yaml
import argparse
from loguru import logger

from core.ec_controller import ECController
from commands.motion import MotionCommands


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def setup_logging(config: dict):
    """设置日志"""
    log_level = config['logging']['level']
    log_file = config['logging']['file']

    # 确保日志目录存在
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # 配置日志
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    logger.add(log_file, level=log_level, rotation="10 MB")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='IAI EC电缸控制程序')
    parser.add_argument('-c', '--config', default='config.yaml',
                       help='配置文件路径')
    parser.add_argument('--demo', action='store_true',
                       help='运行演示程序')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    setup_logging(config)

    logger.info("IAI EC电缸控制程序启动")

    # 创建控制器
    controller = ECController(config)
    motion = MotionCommands(controller)

    try:
        # 连接电缸
        if not controller.connect():
            logger.error("无法连接到电缸")
            return

        if args.demo:
            # 运行演示程序
            demo_sequence(controller, motion)
        else:
            # 进入交互模式
            interactive_mode(controller, motion)

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.exception(f"程序异常: {e}")
    finally:
        controller.disconnect()
        logger.info("程序结束")


def demo_sequence(controller: ECController, motion: MotionCommands):
    """演示程序"""
    logger.info("开始演示程序")

    # 1. 原点复位
    if not controller.home():
        logger.error("原点复位失败")
        return

    # 2. 移动到几个位置
    positions = [90, 180, 270, 0]
    motion.move_sequence(positions, speed=200, dwell_time=2)

    # 3. 点动演示
    logger.info("正向点动3秒")
    motion.jog_forward(50)
    import time
    time.sleep(3)
    motion.stop_jog()

    time.sleep(1)

    logger.info("反向点动3秒")
    motion.jog_backward(50)
    time.sleep(3)
    motion.stop_jog()

    # 4. 返回原点
    controller.move_to_position(0, speed=300)

    logger.info("演示程序完成")


def interactive_mode(controller: ECController, motion: MotionCommands):
    """交互模式"""
    from datetime import datetime

    print("\n=== IAI EC电缸控制 - 交互模式 ===")
    print("命令列表:")
    print("  home - 原点复位")
    print("  move <position> [speed] - 移动到指定位置")
    print("  jog+ [speed] - 正向点动")
    print("  jog- [speed] - 反向点动")
    print("  stop - 停止")
    print("  status - 显示状态")
    print("  reset - 复位报警")
    print("  exit - 退出程序")
    print()

    while True:
        try:
            cmd = input("EC> ").strip().split()
            if not cmd:
                continue

            command = cmd[0].lower()

            if command == 'exit':
                break
            elif command == 'home':
                controller.home()
            elif command == 'move' and len(cmd) >= 2:
                position = float(cmd[1])
                speed = float(cmd[2]) if len(cmd) > 2 else None
                controller.move_to_position(position, speed)
            elif command == 'jog+':
                speed = float(cmd[1]) if len(cmd) > 1 else 30
                motion.jog_forward(speed)
            elif command == 'jog-':
                speed = float(cmd[1]) if len(cmd) > 1 else 30
                motion.jog_backward(speed)
            elif command == 'stop':
                controller.stop()
            elif command == 'status':
                status = controller.get_status()
                print(f"状态: {status}")
            elif command == 'reset':
                controller.reset_alarm()
            else:
                print(f"未知命令: {command}")

        except ValueError as e:
            print(f"参数错误: {e}")
        except Exception as e:
            logger.error(f"命令执行错误: {e}")


if __name__ == '__main__':
    main()