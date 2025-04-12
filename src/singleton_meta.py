from typing import Type


class SingletonMeta(type):
    _instances: dict[Type['SingletonMeta'], object] = {}  # Dictionary to store class instances

    def __call__(cls: Type['SingletonMeta'], *args: tuple, **kwargs: dict) -> object:
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
