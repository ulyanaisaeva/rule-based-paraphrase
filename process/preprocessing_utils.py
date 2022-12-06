import stanza

class PreprocessingUtils:
    def __init__(self) -> None:
        self.stanza = None
        self.pymorphy = None
        self.udon2 = None
    
    def load(self) -> None:
        if self.stanza is None:
            stanza.download(lang="ru", verbose=True)
            self.stanza = stanza.Pipeline(lang="ru")
    
    def stanza_parse(self, input_sent) -> stanza.models.common.doc.Sentence:
        return self.stanza(input_sent).sentences[0]


if __name__ == "__main__":
    print("This module is not callable")
    exit()
