import logging
import sys
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, log_file_path: str) -> None:
        self.log_file_path = log_file_path
        self.logger = logging.getLogger('now_playing_logger')

        # Set the overall logging level
        self.logger.setLevel(logging.DEBUG)

        # Stream handler for console logging
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
        self.logger.addHandler(stdout_handler)

        # File handler with rotation
        file_handler = RotatingFileHandler(self.log_file_path, maxBytes=2000, backupCount=3)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
        self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger
