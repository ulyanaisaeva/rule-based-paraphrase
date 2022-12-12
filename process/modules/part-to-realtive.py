from process.module import ParaphraseModule
from process.preprocessing_utils import PreprocessingUtils

!pip install pymorphy2
import pymorphy2 
morph = pymorphy2.MorphAnalyzer()

%pip install pyconll
import pyconll
%pip install udon2
import udon2


class PartToRelativeModule(ParaphraseModule):
    def __init__(self, name="part_to_relative") -> None:
        super().__init__(name=name)

    def load(self, preproc_utils: PreprocessingUtils) -> None:
    # load any tools as `preproc_utils` attributes
        self.loaded = True    
    
    def participle_parser(self, sentence, preproc_utils: PreprocessingUtils):
        parsed_data = preproc_utils.stanza_parse(sentence)
        output_file_name = "participle.conllu"
        preproc_utils.stanza.utils.conll.CoNLL.write_doc2conll(parsed_data, output_file_name)
        participle_data = pyconll.load_from_file("participle.conllu")
        roots = udon2.Importer.from_stanza(parsed_data.to_dict()) 
        root = roots[0]  
        selection = root.select_having("feats", "VerbForm=Part")
        if len(selection) != 0:
            data = {}
            for node in selection:
                if node.deprel != 'acl':
                    pass
                else:
                    subtree = node.get_subtree_text().replace(node.form, '')
                    if subtree != '' and not node.has("feats", "Variant", "Short"): # избавляемся от одиночных причастий и кратких причастий
                        data['participle'] = node.form
                        data['dep'] = subtree
                        data['head'] = node.parent.form
                        data['agent_full'] = ''

                        for feat in node.feats: # если причастие страдательное, мы пытаемся найти агенс, если он выражен
                            if feat[0] == 'Voice':
                                if feat[1] == 'Pass':
                                    if len(node.select_by("deprel", "obl")) > 0:
                                        obl = node.select_by("deprel", "obl")[0]
                                        for feat in obl.feats:
                                            if feat[0] == 'Case' and feat[1] == 'Ins':
                                                data['agent'] = obl.form
                                                data['agent_full'] = obl.get_subtree_text()
            return data
        else:
            return {}
    
    def participle(self, token):
        part_list = morph.parse(token)
        part = morph.parse(token)[0]
        for elem in part_list:
            if elem.tag.POS == 'PRTF':
                part = elem
        return part
    
    def normal_form(self, token):
        part = self.participle(token)
        part_norm_list = morph.parse(part.normal_form)
        part_norm = part_norm_list[0]
        for elem in part_norm_list:
            if elem.tag.POS == 'INFN':
                part_norm = elem
        return part_norm
    
    def participle_rewrite(self,sentence):
        data = self.participle_parser(sentence)
        tokens = sentence.split()
        rewritten_sentence = ''
        dep = []
        ag_data = data['agent_full'].split()
        for t in tokens:
            token = t.strip(',.')
            if token == data['participle']: # выбираем причастие 
                t_pos = tokens.index(t) # index of participle
                dep = data['dep'].strip(',').split()
                d_pos = tokens.index(dep[0])
                part = self.participle(token)
                part_norm = self.normal_form(token)
                if part.tag.voice == 'actv': # проверяем залог
                    head = morph.parse(data['head'])[0]
                    if part.tag.tense == 'pres':
                        verb = part_norm.inflect({'VERB', part.tag.tense, head.tag.number, '3per'}).word
                    elif part.tag.tense == 'past':
                        verb = part_norm.inflect({'VERB', part.tag.tense, head.tag.number, head.tag.gender}).word
                    if head.tag.number == 'sing':
                        which = morph.parse('который')[0].inflect({head.tag.number, head.tag.gender, 'nomn'}).word
                    elif head.tag.number == 'plur':
                        which = morph.parse('который')[0].inflect({head.tag.number, 'nomn'}).word
                    change = f'{which} {verb}'
                    rewritten_sentence += f' {change}'
                elif part.tag.voice == 'pssv':
                    agent_list = []  # преобразуем агенс со всеми зависимыми в номинатив
                    if len(data['agent_full']) != 0:
                        for word in ag_data:
                            if word != ',':
                                ag_el = morph.parse(word.strip(',."«»'))[0]
                                ag_el_ = ag_el.inflect({'nomn'}).word
                                agent_list.append(ag_el_)
                            else:
                                agent_list.append(word)
                        head = morph.parse(data['head'])[0]
                        agent = morph.parse(data['agent'])[0]
                        if part.tag.tense == 'past':
                            verb = part_norm.inflect({'VERB', part.tag.tense, agent.tag.number, agent.tag.gender}).word
                        if part.tag.tense == 'pres':
                            verb = part_norm.inflect({'VERB', part.tag.tense, agent.tag.number, '3per'}).word
                        if head.tag.number == 'sing':
                            which = morph.parse('который')[0].inflect({head.tag.number, head.tag.gender, head.tag.animacy, 'accs'}).word
                        elif head.tag.number == 'plur':
                            which = morph.parse('который')[0].inflect({head.tag.number, head.tag.animacy, 'accs'}).word
                        rewritten_sentence += f' {which}'
                        rewritten_sentence += f' {verb}'
                        rewritten_sentence += f' {" ".join(agent_list)}'
                    else:
                        head = morph.parse(data['head'])[0]
                        if part.tag.tense == 'past':
                            verb = part_norm.inflect({'VERB', part.tag.tense, 'plur'}).word
                        if part.tag.tense == 'pres':
                            verb = part_norm.inflect({'VERB', part.tag.tense, 'plur', '3per'}).word
                        if head.tag.number == 'sing':
                            which = morph.parse('который')[0].inflect({head.tag.number, head.tag.gender, head.tag.animacy, 'accs'}).word
                        elif head.tag.number == 'plur':
                            which = morph.parse('который')[0].inflect({head.tag.number, head.tag.animacy, 'accs'}).word
                        rewritten_sentence += f' {which}'
                        rewritten_sentence += f' {verb}'            
            else:
                if token in ag_data:
                    pass
                else:
                    rewritten_sentence += f' {t}'
        rewritten_sentence += '.'
        return rewritten_sentence

    def process_batch(self, inputs: List[str], preproc_utils: PreprocessingUtils) -> List[str]:
        outputs = []
        for sentence in inputs:
            data = self.participle_parser(sentence, preproc_utils)
            if data != {}:
                tokens = sentence.split()
                pure_tokens = []
                head = morph.parse(data['head'])[0]
                for t in tokens:
                    pure_tokens.append(t.strip('.,'))
                rewritten_sentence = ''
                dep = []
                ag_data = data['agent_full'].split()
                if pure_tokens.index(data['head']) < pure_tokens.index(data['participle']):
                    paraphrased = self.participle_rewrite(sentence)
                    outputs.append(paraphrased)
                else:
                    outputs.append(sentence)
            else:
                outputs.append(sentence)
        return outputs

if __name__ == "__main__":
    print("This module is not callable")
    exit()
