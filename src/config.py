import os
import yaml

from singleton_meta import SingletonMeta


class Config(metaclass=SingletonMeta):
    def __init__(self) -> None:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        with open(config_path, 'r') as config_file:
            self._config = yaml.safe_load(config_file)

    def get_config(self) -> dict:
        return self._config
