import sys
from pathlib import Path
from loguru import logger

class LogSetup:
    def __init__(self, config=None):
        logger.remove()
        logger.add(
            sink=Path("./cursorRegister_log") / "{time:YYYY-MM-DD_HH}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} |{level:8}| - {message}",
            rotation="10 MB",
            retention="14 days",
            compression="gz",
            enqueue=True,
            level="DEBUG"
        )
        logger.add(
            sink=sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>|{level:8}| - {message}</level>",
            colorize=True,
            enqueue=True,
            level="DEBUG"
        )