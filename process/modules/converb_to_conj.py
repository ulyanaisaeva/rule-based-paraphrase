from process.module import ParaphraseModule
from process.preprocessing_utils import PreprocessingUtils
from stanza.utils.conll import CoNLL

import stanza
import pymorphy2 
morph = pymorphy2.MorphAnalyzer()
import pyconll
import udon2

class ConverbToConjuctionModule(ParaphraseModule):
    def __init__(self, name="capitalize_nouns") -> None:
        super().__init__(name=name)
    
    def load(self, preproc_utils: PreprocessingUtils) -> None:
        # load any tools as `preproc_utils` attributes
        preproc_utils.stanza_model = stanza.Pipeline('ru', processors='tokenize,pos,lemma,depparse')
        self.loaded = True

    def converb_parser(self, sentence, preproc_utils: PreprocessingUtils):
        data = {}
        parsed_data = preproc_utils.stanza_model(sentence)
        output_file_name = "participle.conllu"
        CoNLL.write_doc2conll(parsed_data, output_file_name)
        participle_data = pyconll.load_from_file("participle.conllu")
        roots = udon2.Importer.from_stanza(parsed_data.to_dict()) 
        root = roots[0]  
        selection = root.select_having("feats", "VerbForm=Conv") # выбираем все узлы, содержащие деепричастие
        for node in selection:
            subtree = node.get_subtree_text().replace(node.form, '', 1).strip(',.')
            data['converb'] = node.form
            inf = False
            for feat in node.parent.feats:
                if feat[0] == 'VerbForm' and feat[1] == 'Inf':
                    inf = True
            if inf:
                data['head'] = node.parent.parent.form
            else:
                data['head'] = node.parent.form
            data['dep'] = subtree
            head_sub = node.parent.get_subtree_text().split()
            data['agent'] = ''
            ag_word = ''
            if len(node.parent.get_by('deprel', 'nsubj')) != 0:
                agent = node.parent.get_by('deprel', 'nsubj')[0]
                ag_word = agent.form
                data['agent'] = agent.get_subtree_text()
            elif len(node.parent.parent.get_by('deprel', 'nsubj')) != 0:
                agent = node.parent.parent.get_by('deprel', 'nsubj')[0]
                ag_word = agent.form
                data['agent'] = agent.get_subtree_text()
            data['ag_word'] = ag_word
        return data

    def chose_converb(self, token):
        conv_list = morph.parse(token)
        conv = morph.parse(token)[0]
        for elem in conv_list:
            if elem.tag.POS == 'GRND':
                conv = elem
        return conv
    
    def normal_form(self, token):
        conv = self.chose_converb(token)
        conv_norm_list = morph.parse(conv.normal_form)
        conv_norm = conv_norm_list[0]
        for elem in conv_norm_list:
            if elem.tag.POS == 'INFN':
                conv_norm = elem
        return conv_norm
    
    def converb_rewrite(self, sentence, preproc_utils: PreprocessingUtils):
        rewritten_sentence = ''
        data = self.converb_parser(sentence, preproc_utils)
        converb = data['converb']
        head_string = data['head']
        dep = data['dep'].split()
        sentence_list = []
        agent = data['agent'].split()
        agent_str = ''
        and_ = 'и'

        for elem in sentence.split():
            sentence_list.append(elem.strip(',.:?!«»"'))

        if sentence_list.index(converb) > sentence_list.index(head_string): #порядок слов, в котором главная клауза предшествует зависимой
            for t in sentence.split():
                token = t.strip(',.!?«»"')
                if token == 'не' and sentence_list[sentence_list.index(token)+1] == converb:
                    pass
                elif token == converb:
                    head = morph.parse(head_string)[0]
                    conv = self.chose_converb(token)
                    norm = self.normal_form(token)
                    ag_word = morph.parse(data['ag_word'])[0]
                    if head.tag.tense == 'pres':
                        if conv.tag.aspect != 'perf':
                            verb = norm.inflect({'VERB', head.tag.tense, head.tag.number, head.tag.person}).word
                        else:
                            verb = norm.inflect({'VERB', conv.tag.tense, head.tag.number, ag_word.tag.gender}).word
                    elif head.tag.tense == 'past':
                        if head.tag.number == 'plur':
                            verb = norm.inflect({'VERB', head.tag.tense, head.tag.number}).word
                        else:
                            verb = norm.inflect({'VERB', head.tag.tense, head.tag.number, head.tag.gender}).word
                    rewritten_sentence += f' {and_}'
                    if dep[0] == 'не':
                        rewritten_sentence += ' не'
                    rewritten_sentence += f' {verb}'
                elif token == head_string:
                    rewritten_sentence += f' {token}'
                else:
                    rewritten_sentence += f' {t}'
        elif sentence_list.index(converb) < sentence_list.index(head_string):
            first_part = ''
            second_part = ''
            for t in sentence.split():
                token = t.strip(',.!?«»""')
                if sentence_list.index(token) <= sentence_list.index(dep[-1]):
                    if token == converb:
                        head = morph.parse(head_string)[0]
                        conv = self.chose_converb(token)
                        norm = self.normal_form(token)
                        ag_word = morph.parse(data['ag_word'])[0]
                        if head.tag.tense == 'pres':
                            if conv.tag.aspect != 'perf':
                                verb = norm.inflect({'VERB', head.tag.tense, head.tag.number, head.tag.person}).word
                            else:
                                verb = norm.inflect({'VERB', conv.tag.tense, head.tag.number, ag_word.tag.gender}).word
                        elif head.tag.tense == 'past':
                            if head.tag.number == 'plur':
                                verb = norm.inflect({'VERB', head.tag.tense, head.tag.number}).word
                            else:
                                verb = norm.inflect({'VERB', head.tag.tense, head.tag.number, head.tag.gender}).word
                        first_part += f' {verb}'
                    else:
                        first_part += f' {t}'
                else:
                    if token in agent: 
                        agent_str += f' {t}'
                    else:
                        second_part += f' {t}'
            first_part = agent_str + first_part
            rewritten_sentence = first_part.strip(',.') + ' и' + second_part
        rewritten_sentence = rewritten_sentence.strip(' ')
        rewritten_sentence = rewritten_sentence.replace(rewritten_sentence[0], rewritten_sentence[0].upper(), 1)
        rewrite_list = rewritten_sentence.split()
        new_elem = None
        change = None
        for i in range(1, len(rewrite_list) - 1):
            elem = rewrite_list[i]
            el = elem.replace(',', '')
            if elem[0].isupper() and sentence_list.index(el) == 0:
                new_elem = el.lower()
                change = i
        if new_elem != None and change != None:
            rewrite_list[change] = new_elem
        rewritten_sentence = ' '.join(rewrite_list)
        rewrite = rewritten_sentence
        for i in range(len(rewritten_sentence)):
            if rewritten_sentence[i] == ',' and rewritten_sentence[i+2] == 'и':
                rewrite = rewritten_sentence[:i] +  rewritten_sentence[i+1:]
                return rewrite
                break
        return rewrite

    def process_batch(self, inputs, preproc_utils: PreprocessingUtils):
        outputs = []
        for sentence in inputs:
            data = self.converb_parser(sentence, preproc_utils)
            if data != {}:
                paraphrased = self.converb_rewrite(sentence, preproc_utils)
                outputs.append(paraphrased)
        return outputs

if __name__ == "__main__":
    print("This module is not callable")
    exit()
