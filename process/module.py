from abc import ABC, abstractmethod
from typing import Any


class ParaphraseModule(ABC):
    def __init__(self, name: str = None) -> None:
        self.name = name
        self.loaded = False
        self.preproc_utils = None
    
    @abstractmethod
    def load(self, preproc_utils: dict[str, Any]) -> None:
        raise NotImplementedError(
                f"load() method is not implemented at module {self.name} ({self.__class__.__name__}).")

    @abstractmethod
    def process_batch(self, inputs: list[str], preproc_utils: dict[str, Any]) -> list[str]:
        raise NotImplementedError(
                f"process_multiple() method is not implemented at module {self.name} ({self.__class__.__name__}).")


if __name__ == "__main__":
    print("This module is not callable")
    exit()
