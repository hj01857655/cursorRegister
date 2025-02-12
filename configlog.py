import sys
import time
from pathlib import Path
from loguru import logger


class LogSetup:
    DEFAULT_CONFIG = {
        "level": "DEBUG",
        "colorize": True,
        "rotation": "5 MB",
        "retention": "7 days",
        "compression": "zip",
        "log_path": "./log",
        "console_mode": 1,
        "only_level": None,
        "record_logs": False
    }

    CHINESE_TO_ENGLISH_KEYS = {
        '日志路径': 'log_path',
        '日志级别': 'level',
        '颜色化': 'colorize',
        '日志轮转': 'rotation',
        '日志保留时间': 'retention',
        '压缩方式': 'compression',
        '控制台模式': 'console_mode',
        '仅限级别': 'only_level',
        '记录日志': 'record_logs'
    }

    def __init__(self, config=None, **kwargs):
        config = config or {}
        translated_config = {self.CHINESE_TO_ENGLISH_KEYS.get(k, k): v for k, v in config.items()}
        # 添加数据类型转换逻辑
        for key in ['console_mode']:
            if key in translated_config:
                if translated_config[key] == '开启':
                    translated_config[key] = 1
                elif translated_config[key] == '红字':
                    translated_config[key] = 2
                elif translated_config[key] == '关闭':
                    translated_config[key] = 0

        for key in ['colorize', 'record_logs']:
            if key in translated_config:
                if translated_config[key] == '开启':
                    translated_config[key] = True
                elif translated_config[key] == '关闭':
                    translated_config[key] = False
        self.config = {**self.DEFAULT_CONFIG, **translated_config, **kwargs}
        self.log_path = self.config['log_path']
        self.set_attributes_from_config()
        logger.remove()
        self._add_handlers()

    def set_attributes_from_config(self):
        self.__dict__.update(self.config)

    def _add_handler(self, sink, params):
        if self.only_level:
            params['filter'] = lambda record: record["level"].name == self.only_level
        logger.add(sink=sink, **params)

    def _add_handlers(self):
        file_params = {
            "format": "{time:YYYY-MM-DD HH:mm:ss} |{level:8}| - {message}",
            "rotation": self.rotation,
            "retention": self.retention,
            "compression": self.compression,
            "enqueue": True,
            "colorize": self.colorize,
            "level": self.level
        }

        self._add_handler(Path(self.log_path) / "{time:YYYY-MM-DD_HH}.log", file_params)
        console_sink = {1: sys.stdout, 2: sys.stderr}.get(self.console_mode)
        if console_sink:
            console_params = {
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>|{level:8}| - {message}</level>",
                "colorize": self.colorize,
                "enqueue": True,
                "level": self.level
            }
            self._add_handler(console_sink, console_params)
        elif self.console_mode:
            logger.warning("控制台模式无效，日志不会输出到控制台")
            print("控制台模式无效，日志不会输出到控制台")

    def delete_logs(self, confirm=False, retries=3, delay=2):
        if not confirm:
            logger.warning("删除日志文件需要确认，请传递 confirm=True 参数以继续")
            return

        log_path = Path(self.log_path)
        if not log_path.exists():
            logger.warning(f"日志路径不存在: {log_path}")
            return

        logger.remove()
        logger.complete()
        log_files = list(log_path.glob("*.log"))
        if not log_files:
            logger.info("没有找到日志文件")
            return

        for file_path in log_files:
            for attempt in range(retries):
                try:
                    file_path.unlink()
                    logger.info(f"已删除日志文件: {file_path}")
                    break
                except Exception as e:
                    if attempt < retries - 1:
                        logger.warning(f"删除日志文件失败: {file_path}, 错误: {e}, 尝试重试...")
                        time.sleep(delay)
                    else:
                        logger.error(f"删除日志文件失败: {file_path}, 错误: {e}")


if __name__ == "__main__":
    path = Path.cwd().parent
    print(path)
    config_dict = {
        '日志路径': './cursorRegister_log',
        '日志级别': 'DEBUG',
        '颜色化': '开启',
        '日志轮转': '10 MB',
        '日志保留时间': '14 days',
        '压缩方式': 'gz',
        '控制台模式': '关闭',
        '仅限级别': 'DEBUG',
        '记录日志': '开启'
    }
    log_config = LogSetup(config=config_dict)
    logger.debug("这是一个调试消息")
    logger.info("这是一个信息消息")
    logger.warning("这是一个警告消息")
    logger.error("这是一个错误消息")
    logger.critical("这是一个严重错误消息")

    # 再次记录日志
    logger.debug("这是加载配置后的调试消息")
    logger.info("这是加载配置后的信息消息")
    logger.warning("这是加载配置后的警告消息")
    logger.error("这是加载配置后的错误消息")
    logger.critical("这是加载配置后的严重错误消息")

    # 调用删除日志的方法
    # log_config.delete_logs(confirm=True)
