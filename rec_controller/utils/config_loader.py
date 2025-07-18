"""配置文件加载器"""
import yaml
import os


def load_config(config_file: str) -> dict:
    """加载YAML配置文件"""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config