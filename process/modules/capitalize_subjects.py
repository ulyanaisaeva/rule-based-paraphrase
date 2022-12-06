from typing import Any

from process.module import ParaphraseModule
from process.preprocessing_utils import PreprocessingUtils


class CapitalizeSubjectsModule(ParaphraseModule):
    def __init__(self, name="capitalize_nouns") -> None:
        super().__init__(name=name)
    
    def load(self, preproc_utils: PreprocessingUtils) -> None:
        # load any tools as `preproc_utils` attributes
        self.loaded = True
    
    def process(self, input_text: str, preproc_utils: PreprocessingUtils) -> str:
        output_text = ""
        last_char = 0
        parsed_sent = preproc_utils.stanza_parse(input_text)
        for word in parsed_sent.words:
            if word.deprel == "nsubj":
                word.text = word.text.upper()
            if word.start_char > last_char:
                output_text += " "
            output_text += word.text
            last_char = word.end_char
        return output_text

    def process_batch(self, inputs: list[str], preproc_utils: PreprocessingUtils) -> list[str]:
        outputs = []
        for input_text in inputs:
            outputs.append(self.process(input_text, preproc_utils))
        return outputs


if __name__ == "__main__":
    print("This module is not callable")
    exit()
