import logging
import sys
from logging.handlers import RotatingFileHandler
from config import Config
from singleton_meta import SingletonMeta


class Logger(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger('now_playing_logger')
        self._config: dict = Config().get_config()

        # Overall logging level
        self._logger.setLevel(logging.DEBUG)

        # Stream handler for console logging
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
        self._logger.addHandler(stdout_handler)

        # File handler with rotation
        log_file_path = self._config['log']['log_file_path']
        file_handler = RotatingFileHandler(log_file_path, maxBytes=1_000_000, backupCount=5)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
        self._logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self._logger
