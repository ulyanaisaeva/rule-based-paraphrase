import stanza 
import udon2
import pymorphy2
import json

from typing import List

from process.module import ParaphraseModule
from process.preprocessing_utils import PreprocessingUtils

class PerfFutToImperfModule(ParaphraseModule):
    def __init__(self, name="perf_to_imperf") -> None:
        super().__init__(name=name)
        self.morph = pymorphy2.MorphAnalyzer()
        self.verbs_dict_path = "process/russian_verbs_aspect_pairs.json"
    
    def load(self, preproc_utils: PreprocessingUtils) -> None:
        # load any tools as `preproc_utils` attributes
        preproc_utils.stanza_model = stanza.Pipeline('ru', processors='tokenize,pos,lemma,depparse')
        self.loaded = True

    def get_verbs_dict(self, file_path): 
        verbs_dictionary = None
        with open(file_path, 'r') as fin:
            verbs_data = json.load(fin)
            verbs_dictionary = verbs_data['russian verbs']
        return verbs_dictionary

    # детектирование перфективного будущего 
    def detect_perfective_future(self, sentence):
        doc = self.preproc_utils.stanza_model(sentence)
        parsed_sentence = doc.sentences[0]
        roots = udon2.Importer.from_stanza(doc.to_dict())
        for i, root in enumerate(roots): 
            sentence_tree = root
            # находим все глаголы
            verbs = sentence_tree.select_by("upos", "VERB")
            if len(verbs) > 0:
                for verb_node in verbs:
                    # предложение с синтетическим будущем
                    if verb_node.has_all("feats", "Aspect=Perf|Tense=Fut|VerbForm=Fin|Voice=Act"): 
                        return True
        return False
    
    # обработка feats --> преобразование в словарь
    def get_feats_dict(self, word_feats):
        feats_dict = dict()
        feats_lst = word_feats.split('|')
        for pair in feats_lst: 
            key, value = pair.split('=')
            feats_dict[key] = value
        return feats_dict
    
    # функция для добавления узла "быть" в предложение в нужной форме
    def add_be_node(self, root_feats):
        be_node = ''
        if root_feats['Number'] == 'Sing' and root_feats['Person'] == '1': 
            be_node = 'буду'
        elif root_feats['Number'] == 'Sing' and root_feats['Person'] == '2': 
            be_node = 'будешь'
        elif root_feats['Number'] == 'Sing' and root_feats['Person'] == '3': 
            be_node = 'будет'
        elif root_feats['Number'] == 'Plur' and root_feats['Person'] == '1': 
            be_node = 'будем'
        elif root_feats['Number'] == 'Plur' and root_feats['Person'] == '2': 
            be_node = 'будете'
        elif root_feats['Number'] == 'Plur' and root_feats['Person'] == '3': 
            be_node = 'будут'
        return be_node

    # функция нахождения перфективного будущего 
    def find_perf_verb(self, sentence): 
        perf_fut_verbs = []
        doc = self.preproc_utils.stanza_model(sentence)
        parsed_sentence = doc.sentences[0]
        roots = udon2.Importer.from_stanza(doc.to_dict())
        sentence_tree = roots[0]
        verbs = sentence_tree.select_by("upos", "VERB")
        for verb_node in verbs:
            perf_fut_verb = {}
            # находим глагол в перфективном будущем
            if verb_node.has_all("feats", "Aspect=Perf|Tense=Fut|VerbForm=Fin|Voice=Act"): 
                perf_fut_verb['id'] = int(verb_node.id)
                perf_fut_verb['form'] = verb_node.form
                perf_fut_verb['lemma'] = verb_node.lemma
                perf_fut_verb['feats'] = str(verb_node.feats)
                perf_fut_verb['upos'] = verb_node.upos
            for word in parsed_sentence.words: 
                if 'id' in perf_fut_verb.keys():
                    if word.id == perf_fut_verb['id']: 
                        perf_fut_verb['start_char'] = word.start_char
                        perf_fut_verb['end_char'] = word.end_char
            if len(perf_fut_verb.keys()) != 0:
                perf_fut_verbs.append(perf_fut_verb)  
        return perf_fut_verbs
    
    def process(self, input_text: str, verbs_dict: dict, preproc_utils: PreprocessingUtils) -> str:
        changed_sentence = '' 
        parsed_sentence = self.preproc_utils.stanza_model(input_text).sentences[0]
        perf_verbs = self.find_perf_verb(input_text)
        if len(perf_verbs) > 0:
            for perf_verb_node in perf_verbs: 
                idx = perf_verbs.index(perf_verb_node)
                perf_verb_lemma = perf_verb_node['lemma']
                if perf_verb_lemma in verbs_dict.keys(): 
                    perf_verb_form = perf_verb_node['form']
                    perf_verb_feats = self.get_feats_dict(perf_verb_node['feats'])
                    be_node = self.add_be_node(perf_verb_feats)
                    # добавляем "быть" в нужной форме перед глаголом
                    # теперь изменяем исходный вариант на НСВ глагол в инфинитиве 
                    impf_verb = verbs_dict[perf_verb_lemma]
                    analytic_future = ' '.join([be_node, impf_verb])
                    if idx == 0:
                        changed_sentence = re.sub(perf_verb_form, analytic_future, input_text)
                    elif idx >= 1 and changed_sentence == '':
                        changed_sentence = re.sub(perf_verb_form, analytic_future, input_text)
                    elif idx >= 1 and changed_sentence != '':
                        changed_sentence = re.sub(perf_verb_form, analytic_future, changed_sentence)
                else: 
                    if changed_sentence == '':
                        changed_sentence = input_text
                    elif changed_sentence != '':
                        continue
        else:
            changed_sentence = input_text
        return changed_sentence

    def process_batch(self, inputs: List[str], preproc_utils: PreprocessingUtils) -> List[str]:
        verbs_dictionary = self.get_verbs_dict(self.verbs_dict_path)
        outputs = []
        for input_text in inputs:
            if self.detect_perfective_future(input_text): 
                paraphrased = self.process(input_text, verbs_dictionary, preproc_utils)
                outputs.append(paraphrased)
            else: 
                outputs.append(input_text)
        return outputs

if __name__ == "__main__":
    print("This module is not callable")
    exit()
