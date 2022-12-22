import stanza 
import udon2
import pymorphy2
import json

from typing import List

from process.module import ParaphraseModule
from process.preprocessing_utils import PreprocessingUtils

class ImperfFutureToPerfModule(ParaphraseModule):
    def __init__(self, name="imperf_to_perf") -> None:
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

    # детектирование имперфективного будущего 
    def detect_imperfective_future(self, sentence, preproc_utils):
        doc = preproc_utils.stanza_model(sentence)
        parsed_sentence = doc.sentences[0]
        roots = udon2.Importer.from_stanza(doc.to_dict())
        for i, root in enumerate(roots): 
            sentence_tree = root
            # находим все глаголы
            verbs = sentence_tree.select_by("upos", "VERB")
            if len(verbs) > 0:
                for verb_node in verbs:
                    # предложение с аналитическим будущем
                    if verb_node.has_all("feats", "Aspect=Imp|VerbForm=Inf|Voice=Act"): 
                        verb_node_children = verb_node.children
                        for child in verb_node_children:
                            if child.deprel == 'aux' and child.lemma == 'быть':
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

    # функция для нахождения нужного варианта преобразования
    def get_verb(self, verb_form): 
        # сначала находим нужный глагол
        verb = None
        possible_varians = self.morph.parse(verb_form)
        for i, variant in enumerate(possible_varians): 
            if 'INFN' in variant.tag and 'perf' in variant.tag:
                verb = variant
        return verb
    
    # преобразование инфинитива СВ глагола в нужную форму на основе мор. признаков "быть"
    def insert_perf_verb(self, aux_feats, perf_inf): 
        perf_verb = ''
        perf_inf_parsed = self.get_verb(perf_inf)
        if aux_feats['Number'] == 'Sing' and aux_feats['Person'] == '1': 
            perf_verb = perf_inf_parsed.inflect({'VERB', 'perf', 'sing', '1per', 'futr', 'indc'}).word
        elif aux_feats['Number'] == 'Sing' and aux_feats['Person'] == '2': 
            perf_verb = perf_inf_parsed.inflect({'VERB', 'perf', 'sing', '2per', 'futr', 'indc'}).word
        elif aux_feats['Number'] == 'Sing' and aux_feats['Person'] == '3': 
            perf_verb = perf_inf_parsed.inflect({'VERB', 'perf', 'sing', '3per', 'futr', 'indc'}).word
        elif aux_feats['Number'] == 'Plur' and aux_feats['Person'] == '1': 
            perf_verb = perf_inf_parsed.inflect({'VERB', 'perf', 'plur', '1per', 'futr', 'indc'}).word
        elif aux_feats['Number'] == 'Plur' and aux_feats['Person'] == '2': 
            perf_verb = perf_inf_parsed.inflect({'VERB', 'perf', 'plur', '2per', 'futr', 'indc'}).word
        elif aux_feats['Number'] == 'Plur' and aux_feats['Person'] == '3': 
            perf_verb = perf_inf_parsed.inflect({'VERB', 'perf', 'plur', '3per', 'futr', 'indc'}).word
        return perf_verb
        
    # функция для нахождения аналитического будущего
    def find_impf_verb(self, sentence, preproc_utils):
        impf_verb_nodes = []
        aux_verb_nodes = []
        doc = preproc_utils.stanza_model(sentence)
        parsed_sentence = doc.sentences[0]
        roots = udon2.Importer.from_stanza(doc.to_dict())
        sentence_tree = roots[0]
        verbs = sentence_tree.select_by("upos", "VERB")
        for verb_node in verbs:
            impf_verb_node = {}
            aux_verb_node = {}
            # нашли нужный глагол
            if verb_node.has_all("feats", "Aspect=Imp|VerbForm=Inf|Voice=Act"): 
                verb_node_children = verb_node.children
                # нашли глагол-связку
                for child in verb_node_children:
                    if child.upos == 'AUX' and child.lemma == 'быть':
                        # родительский узел
                        impf_verb_node['id'] = int(verb_node.id)
                        impf_verb_node['form'] = verb_node.form
                        impf_verb_node['lemma'] = verb_node.lemma
                        impf_verb_node['feats'] = str(verb_node.feats)
                        impf_verb_node['upos'] = verb_node.upos
                        # дочерний узел
                        aux_verb_node['id'] = int(child.id)
                        aux_verb_node['form'] = child.form
                        aux_verb_node['lemma'] = child.lemma
                        aux_verb_node['feats'] = str(child.feats)
                        aux_verb_node['upos'] = child.upos
                        aux_verb_node['parent'] = int(child.parent.id)
            for word in parsed_sentence.words: 
                if 'id' in aux_verb_node.keys():
                    if word.id == aux_verb_node['id']: 
                        aux_verb_node['start_char'] = word.start_char
                        aux_verb_node['end_char'] = word.end_char
                if 'id' in impf_verb_node.keys():
                    if word.id == impf_verb_node['id']: 
                        impf_verb_node['start_char'] = word.start_char
                        impf_verb_node['end_char'] = word.end_char
            if len(impf_verb_node.keys()) != 0:
                impf_verb_nodes.append(impf_verb_node)
            if len(aux_verb_node.keys()) != 0:
                aux_verb_nodes.append(aux_verb_node)
        return impf_verb_nodes, aux_verb_nodes

    # преобразование
    def process(self, input_text: str, verbs_dict: dict, preproc_utils: PreprocessingUtils) -> str:
        changed_sentence = '' 
        doc = self.stanza_model(input_text)
        parsed_sentence = doc.sentences[0]
        impf_verb_nodes, aux_verb_nodes = self.find_impf_verb(input_text)
        if len(impf_verb_nodes) > 0 and len(aux_verb_nodes) > 0:
            for impf_verb_node, aux_verb_node in zip(impf_verb_nodes, aux_verb_nodes):         
                idx = impf_verb_nodes.index(impf_verb_node)
                impf_verb_lemma = impf_verb_node['lemma']
                if impf_verb_lemma in verbs_dict.keys(): 
                    # изменяем имперфективный глагол на перфективный, ставим в нужную форму
                    # опираемся на мор. признаки глагола-связки, т.к. главный у нас в инфинитиве
                    aux_verb_feats = self.get_feats_dict(aux_verb_node['feats'])
                    perf_inf = verbs_dict[impf_verb_lemma]
                    perf_verb = self.insert_perf_verb(aux_verb_feats, perf_inf)
                    aux_start = aux_verb_node['start_char']
                    aux_end = aux_verb_node['end_char']
                    if idx == 0: 
                        changed_sentence = input_text[:aux_start] + '' + input_text[aux_end+1:]
                        changed_sentence = re.sub(impf_verb_node['form'], perf_verb, changed_sentence)
                        changed_sentence = re.sub('  ', ' ', changed_sentence)
                    elif idx >= 1 and changed_sentence == '':
                        changed_sentence = input_text[:aux_start] + '' + input_text[aux_end+1:]
                        changed_sentence = re.sub(impf_verb_node['form'], perf_verb, changed_sentence)
                        changed_sentence = re.sub('  ', ' ', changed_sentence)
                    elif idx >= 1 and changed_sentence != '':
                        upd_sentence_parsed = self.preproc_utils.stanza_model(changed_sentence).sentences[0] 
                        for word in upd_sentence_parsed.words: 
                            if word.text == aux_verb_node['form'] and word.feats == aux_verb_node['feats']: 
                                aux_parent = word.head
                                for word_2 in upd_sentence_parsed.words: 
                                    if word_2.id == aux_parent and word_2.text == impf_verb_node['form'] and word_2.feats == impf_verb_node['feats']: 
                                        aux_start_new = word.start_char
                                        aux_end_new = word.end_char
                                        changed_sentence = changed_sentence[:aux_start_new] + '' + changed_sentence[aux_end_new+1:]
                                        changed_sentence = re.sub(impf_verb_node['form'], perf_verb, changed_sentence)
                                        changed_sentence = re.sub('  ', ' ', changed_sentence)
                else:
                    if idx == 0 and len(impf_verb_nodes) > 1: 
                        continue
                    elif idx == 0 and len(impf_verb_nodes) == 1:
                        changed_sentence = input_text
                    elif idx == impf_verb_nodes.index(impf_verb_nodes[-1]) and changed_sentence == '':
                        changed_sentence = input_text
                    elif idx == impf_verb_nodes.index(impf_verb_nodes[-1]) and changed_sentence != '':
                        changed_sentence = changed_sentence
                    elif idx != 0 and idx != impf_verb_nodes.index(impf_verb_nodes[-1]): 
                        continue
        else: 
            changed_sentence = input_text
        return changed_sentence

    def process_batch(self, inputs: List[str], preproc_utils: PreprocessingUtils) -> List[str]:
        verbs_dict = self.get_verbs_dict(self.verbs_dict_path)
        outputs = []
        for input_text in inputs:
            if self.detect_imperfective_future(input_text, preproc_utils): 
                paraphrased = self.process(input_text, verbs_dict, preproc_utils)
                outputs.append(paraphrased)
            else: 
                outputs.append(input_text)
        return outputs

if __name__ == "__main__":
    print("This module is not callable")
    exit()
