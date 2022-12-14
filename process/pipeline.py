from typing import List

from process.preprocessing_utils import PreprocessingUtils

from process import modules
from process.module import ParaphraseModule


class ParaphrasePipeline:
    def __init__(self, modules: List[ParaphraseModule] = None) -> None:
        self.modules = modules
        self.loaded = False
        self.preproc_utils = PreprocessingUtils()
    
    def load(self) -> None:

        # === preprocessing modules ===
        self.preproc_utils.load()

        # === paraphrase modules ===
        if self.modules is not None:
            for module in self.modules:
                module.load(self.preproc_utils)
        self.loaded = True
    
    def run(self, inputs: List[str]) -> List[str]:
        if not self.loaded:
            print("Pipeline is not loaded!")
            exit()
        result = inputs
        for module in self.modules:
            result = module.process_batch(result, self.preproc_utils)
        return result


if __name__ == "__main__":
    p = ParaphrasePipeline(modules = [
        modules.CapitalizeSubjectsModule(name="capitalize_subjects"),
    ])
    p.load()
    result = p.run(["Это первое предложение.", "Это второе предложение."])
    print(result)
