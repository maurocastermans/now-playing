import logging
import sys
import yaml
from logging.handlers import RotatingFileHandler
import os


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
            with open(config_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
            log_file_path = config['log']['log_file_path']
            cls._instance = object.__new__(cls)
            cls._instance.logger = logging.getLogger("now_playing_logger")
            if not cls._instance.logger.hasHandlers():
                # Set the overall logging level
                cls._instance.logger.setLevel(logging.DEBUG)

                # Stream handler for console logging
                stdout_handler = logging.StreamHandler(sys.stdout)
                stdout_handler.setLevel(logging.DEBUG)
                stdout_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
                cls._instance.logger.addHandler(stdout_handler)

                # File handler with rotation
                file_handler = RotatingFileHandler(log_file_path, maxBytes=2000, backupCount=3)
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s'))
                cls._instance.logger.addHandler(file_handler)
        return cls._instance

    def get_logger(self) -> logging.Logger:
        return self.logger
