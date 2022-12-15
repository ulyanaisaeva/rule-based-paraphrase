from collections import defaultdict
from typing import List
import stanza
import udon2
from stanza.utils.conll import CoNLL
import pyconll
import pymorphy2
from process.pipeline import ParaphrasePipeline
from process.module import ParaphraseModule
import re
from process.preprocessing_utils import PreprocessingUtils

class FintoConv(ParaphraseModule):
    def __init__(self, name="fin_to_conv") -> None:
        super().__init__(name=name)
        
    def load(self, preproc_utils: PreprocessingUtils) -> None:
        # load any tools as `preproc_utils` attributes
        self.loaded = True

    def get_key(self, val, my_dict):
      for key, value in my_dict.items():
        if val == value:
          return key
        
    def search_subjects(self, tree_node):
      nsubj_list = {}
      def dfs(n):
        for child in n.children:
          if child.deprel == 'nsubj':
            nsubj_list[child] = child.id
          if len(child.children)>0:
            dfs(child)
      dfs(tree_node)
      return nsubj_list
        
    def process_batch(self, inputs: List[str], preproc_utils: PreprocessingUtils) -> List[str]:
        output = defaultdict()
        morph = pymorphy2.MorphyAnalyzer()
        for sentence in inputs:
          sentence = re.sub('[«»]', '', sentence)
          parsed_data = preproc_utils.stanza(sentence)
          rewritten_sentence = re.sub('[«»]', '', sentence)
          roots = udon2.Importer.from_stanza(parsed_data.to_dict())
          root = roots[0]
          if len(root.select_by('deprel', 'conj'))!=0:
            try:
              selection = root.select_by('upos', 'VERB')
              subjects = root.select_by('deprel', 'nsubj')
              delete_space_before = r'\s+(?=(?:[,.?!):;…]))'
              delete_space_after = r'(?<=([/(/:]))\s+'
              for node in selection:
                  if node.deprel=='root' and node.has('feats', 'VerbForm', 'Fin'):
                    subjs = self.search_subjects(root)
                    clause_dict = {subj: [subj.parent] for subj in subjs.keys()}
                    conjuncts = [[node, node.id]]
                    for n in node.children:
                      if n.deprel=='conj' and n.upos=='VERB' and n.has('feats', 'VerbForm', 'Fin') and len(n.get_by('deprel', 'nsubj'))==0:
                          conjuncts.append([n, n.id])
                    vals = sorted([val for val in subjs.values()])
                    for c in conjuncts:
                      if len(vals)==1:
                          clause_dict[self.get_key(vals[0], subjs)].append(c[0])
                      else:
                        for i in range(len(vals)-1):
                          if int(c[1]) > int(vals[i]) and int(c[1])<int(vals[i+1]) and str(c[0]) not in [str(elem) for sublist in clause_dict.values() for elem in clause_dict.values()]:
                            clause_dict[self.get_key(vals[i], subjs)].append(c[0])
                    if len(conjuncts)>1:
                      can_transform, delete_conj = [], []
                      for val in list(clause_dict.values()):
                        if len(val)>1:
                          for con in val:
                            conj = con.get_by('deprel', 'cc')
                            exception = con.get_by('lemma', 'или')
                            if len(conj)==0 and len(exception)==0:
                              can_transform.append(con)
                            elif len(conj)!=0 and len(exception)==0:
                              delete_conj.append(con)
                        if len(delete_conj)==0:
                          can_transform.remove(val[-1])
                            
                      
                      for con in can_transform:
                        verb = str(con).split('|')[-1]
                        rewrite =  morph.parse(verb)[0].inflect({'GRND'}).word
                        rewritten_sentence = rewritten_sentence.replace(verb, rewrite)
                      if len(delete_conj)>0:
                        for elem in delete_conj:
                          old_subsentence = ' '.join([str(token).split('|')[-1] for token in elem.linear()])
                          old_subsentence = re.sub(delete_space_before, r'', old_subsentence)
                          old_subsentence = re.sub(delete_space_after, r'', old_subsentence)
                          c = elem.get_by('deprel', 'cc')
                          elem.remove_child(c[0])
                          subsentence = str(elem.get_subtree_text())
                          subsentence = re.sub(delete_space_before, r'', subsentence)
                          subsentence = re.sub(delete_space_after, r'', subsentence)
                          v = str(elem).split('|')[-1]
                          rewritten_sentence = rewritten_sentence.replace(old_subsentence, subsentence)
                      
                      
                      if rewritten_sentence!=sentence:
                        output[sentence] = rewritten_sentence
                      else:
                        output[sentence] = sentence

            except(ValueError, AttributeError):
              pass
            
          if sentence not in output.keys():
              output[sentence] = sentence
            
        return list(output.values())
        
 if __name__ == "__main__":
     print("This module is not callable")
     exit()


