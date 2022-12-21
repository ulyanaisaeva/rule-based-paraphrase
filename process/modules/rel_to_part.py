from collections import defaultdict
from typing import List

import stanza
import udon2
import pyconll
import pymorphy2

from process.module import ParaphraseModule
from process.preprocessing_utils import PreprocessingUtils

class ReltoPart(ParaphraseModule):
    def __init__(self, name="rel_to_part") -> None:
        super().__init__(name=name)
    
    def load(self, preproc_utils: PreprocessingUtils) -> None:
         if getattr(preproc_utils, 'morph', None) is None:
             preproc_utils.morph = pymorphy2.MorphAnalyzer()
         self.loaded = True
        
    def conjunction_check(self, tree_node, sent, morph):
      head = preproc_utils.morph.parse(str(tree_node.parent.parent).split('|')[-1])[0]
      wordform = str(tree_node).split('|')[-1]
      parsed_rel = preproc_utils.morph.parse(wordform)[0]
      conjuncts = []
      for child in tree_node.parent.children:
        rewritten_sentence = sent
        if child.deprel=='conj':
          conjuncts.append(str(child).split('|')[-1])
      if len(conjuncts) == 0: return False
      for conjunct in conjuncts:
        if parsed_rel.tag.number=='sing':
          rewrite = preproc_utils.morph.parse(conjunct)[0].inflect({'PRTF', parsed_rel.tag.number, head.tag.case, parsed_rel.tag.gender}).word
        else:
          rewrite = preproc_utils.morph.parse(conjunct)[0].inflect({'PRTF', parsed_rel.tag.number, head.tag.case}).word
        rewritten_sentence = rewritten_sentence.replace(conjunct, rewrite)
      return rewritten_sentence

    def adjuncts(self, tree_node, tree_root):
        adj_list = []
        verb = tree_node.parent
        
        def dfs(n):
          for child in n.children:
            if child.id > tree_node.id and child.id < tree_node.parent.id:
              adj_list.append([str(child).split('|')[-1], child.id])
            if len(child.children)>0:
              dfs(child)
        
          return adj_list

        if dfs(verb)==0:
          return False
        else:
          adj_list.sort(key=lambda x: x[1])
          return ' '.join([elem[0] for elem in adj_list]).strip(',').strip(' ')
            
    def process_batch(self, inputs: List[str], preproc_utils: PreprocessingUtils) -> List[str]:
        output = defaultdict()
        for sentence in inputs:
          if ' котор' in sentence:
            try:
              parsed_data = preproc_utils.stanza(sentence)
              roots = udon2.Importer.from_stanza(parsed_data.to_dict())
              root = roots[0]
              selection = root.select_by("lemma", "который")
              for node in selection:
                  if node.deprel=='nsubj' and node.parent.upos=='VERB' and not node.parent.has('feats', 'Tense', 'Fut') and len(node.parent.get_by('deprel', 'aux'))==0:
                      head = preproc_utils.morph.parse(str(node.parent.parent).split('|')[-1])[0]
                      wordform = str(node).split('|')[-1]
                      parsed_rel = preproc_utils.morph.parse(wordform)[0]
                      verb = str(node.parent).split('|')[-1]
                      if parsed_rel.tag.number=='sing':
                        rewrite = preproc_utils.morph.parse(verb)[0].inflect({'PRTF', parsed_rel.tag.number, head.tag.case, parsed_rel.tag.gender}).word
                      else:
                        rewrite = preproc_utils.morph.parse(verb)[0].inflect({'PRTF', parsed_rel.tag.number, head.tag.case}).word
                      if not self.adjuncts(node, root):
                        rewritten_sentence = sentence.split(wordform)[0] + rewrite + ' ' + ' '.join(sentence.split(wordform)[1].split(' ')[2:])
                      else:
                        rewritten_sentence = sentence.split(wordform)[0] + self.adjuncts(node, root) + ' ' + rewrite + ' '+ sentence.split(str(node.parent).split('|')[-1])[1]
                      ans = self.conjunction_check(node, rewritten_sentence, preproc_utils.morph)
                      if ans:
                        output[sentence] = ' '.join(ans.split())
                      
                      else:
                        output[sentence] = ' '.join(rewritten_sentence.split())


                  elif node.deprel!='nsubj' and node.deprel!='nsubj:pass':
                    wh_word, ch = '', ''
                    head = node.parent.parent
                    for child in node.children:
                      if child.lemma=='в' and node.has('feats', 'Case', 'Acc') and not head.has('feats', 'Animacy', 'Anim'):
                        wh_word = 'куда'
                        ch = child
                      if child.lemma=='в' and node.has('feats', 'Case', 'Loc') and not head.has('feats', 'Animacy', 'Anim'):
                        wh_word = 'где'
                        ch = child
                    if len(wh_word)>0:
                      wordform = str(node).split('|')[-1]
                      prep = str(ch).split('|')[-1]
                      rewritten_sentence = sentence.split(prep + ' ' + wordform)[0] + wh_word + sentence.split(prep + ' ' + wordform)[1]
                      output[sentence] = ' '.join(rewritten_sentence.split())
                  
                  elif node.deprel=='nsubj:pass' and not node.parent.has('feats', 'Tense', 'Fut'):
                    aux = node.parent.get_by('deprel', 'aux:pass')
                    head = preproc_utils.morph.parse(str(node.parent.parent).split('|')[-1])[0]
                    verb = str(node.parent).split('|')[-1]
                    if len(aux)!=0 and aux[0].has('feats', 'Tense', 'Pres'):
                      break
                    wordform = str(node).split('|')[-1]
                    parsed_rel = preproc_utils.morph.parse(wordform)[0]
                    if parsed_rel.tag.number=='sing':
                        rewrite = preproc_utils.morph.parse(str(node.parent).split('|')[-1])[0].inflect({'PRTF', parsed_rel.tag.number, head.tag.case, parsed_rel.tag.gender}).word
                    elif parsed_rel.tag.number!='sing':
                        rewrite = preproc_utils.morph.parse(str(node.parent).split('|')[-1])[0].inflect({'PRTF', parsed_rel.tag.number, head.tag.case}).word
                    if not self.adjuncts(node, root):
                      rewritten_sentence = sentence.split(wordform)[0] + rewrite + ' ' + ' '.join(sentence.split(wordform)[1].split(' ')[2:])
                    else:
                      rewritten_sentence = sentence.split(wordform)[0] + ' ' + self.adjuncts(node, root) + ' ' + rewrite + ' ' + sentence.split(verb)[-1]
                    if len(aux)>0:
                      rewritten_sentence = rewritten_sentence.replace(str(aux).split('|')[-1], '')
                    ans = self.conjunction_check(node, rewritten_sentence, preproc_utils.morph)
                    if ans:
                        output[sentence] = ' '.join(ans.split())
                      
                    else:
                        output[sentence] = ' '.join(rewritten_sentence.split())

            except (ValueError, AttributeError):
                pass
          if sentence not in output.keys():
            output[sentence] = sentence
          
        return list(output.values())


if __name__ == "__main__":
    print("This module is not callable")
    exit()

