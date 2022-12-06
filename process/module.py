from abc import ABC, abstractmethod
from typing import List

from process.preprocessing_utils import PreprocessingUtils


class ParaphraseModule(ABC):
    def __init__(self, name: str = None) -> None:
        self.name = name
        self.loaded = False
        self.preproc_utils = None
    
    @abstractmethod
    def load(self, preproc_utils: PreprocessingUtils) -> None:
        raise NotImplementedError(
                f"load() method is not implemented at module {self.name} ({self.__class__.__name__}).")

    @abstractmethod
    def process_batch(self, inputs: List[str], preproc_utils: PreprocessingUtils) -> List[str]:
        raise NotImplementedError(
                f"process_multiple() method is not implemented at module {self.name} ({self.__class__.__name__}).")


if __name__ == "__main__":
    print("This module is not callable")
    exit()
