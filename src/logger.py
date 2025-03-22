import logging
import sys
from logging.handlers import RotatingFileHandler
from config import Config
from singleton_meta import SingletonMeta


class Logger(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.logger = logging.getLogger("now_playing_logger")

        # Overall logging level
        self.logger.setLevel(logging.DEBUG)

        # Stream handler for console logging
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
        self.logger.addHandler(stdout_handler)

        # File handler with rotation
        log_file_path = Config().get_config()['log']['log_file_path']
        file_handler = RotatingFileHandler(log_file_path, maxBytes=2000, backupCount=3)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
        self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger
