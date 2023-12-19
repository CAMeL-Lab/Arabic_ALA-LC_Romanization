from pathlib import Path
import os
import re
import pandas as pd
import logging
from funcy import log_durations
import argparse
import repackage
repackage.up()
from data.make_dataset import recompose, tokenize_skiphyph
# from madamira import analyse

project_dir = Path(__file__).resolve().parents[2]



class rulesLogger():
    def __init__(self):
        self.translit_rules = {}
        self.morph_rules = {}
        self.exceptional_rules = {}

    def count_translit_rules(self,transliteration_tuples):
        for rule in transliteration_tuples:
            if rule in self.translit_rules:
                self.translit_rules[rule] += 1
            else:
                self.translit_rules[rule] = 1

    def count_morph_rules(self,rule_tuple):
            if rule_tuple in self.morph_rules:
                self.morph_rules[rule_tuple] += 1
            else:
                self.morph_rules[rule_tuple] = 1

    def count_exceptional_rules(self,exceptional_tuple):
        if exceptional_tuple in self.exceptional_rules:
            self.exceptional_rules[exceptional_tuple] += 1
        else:
            self.exceptional_rules[exceptional_tuple] = 1

rules_logger = rulesLogger()

def get_translit_dict(mode,map_tsv=f'{project_dir}/src/predict/ar2phon/ar2phon_map.tsv'):
    mapping = pd.read_csv(map_tsv,delimiter='\t').fillna('')
    mapping.index = mapping['Arabic']
    return mapping[mode].to_dict()

def load_loc_mappings():
    return get_translit_dict(mode='LOC')

# def load_caphi_mappings():
#     return get_translit_dict(mode='CAPHI')

def load_exceptional_spellings(exceptional_tsv=f'{project_dir}/src/predict/ar2phon/loc_exceptional_spellings.tsv'):
    with open(exceptional_tsv,'r') as f:
        next(f) #skip header
        exceptional = dict([(line.strip().split('\t')) for line in f if not line.startswith('#')])
    return exceptional

def translit(string,mapdict,logger=rules_logger):
    """
    base greedy transliterator used by other functions, consumes incrementally from start of string, and returns chunks of chars not found in mapdict as is in the place they occured
    returns list of tuples of original character chunks and what they map to
    """

    # recompose string with start and end symbols, which are currently hardcoded into the map_tsv
    startchar = '<<<<<'
    endchar = '>>>>>'
    string = startchar+string+endchar

    # stores tuples of each chunk of chars and their transliteration
    transliteration = []

    # sort toks from smallest to biggest in length
    chars_by_len = sorted(list(mapdict.keys()),key=len,reverse=True)

    # index that changes with each match
    cursor_index = 0
    
    # while exit condition incase string is not in dict
    previous_chars = ''

    # collect char chunks not in dictionary
    nomap_collector = ''
    # while string has characters
    while string[cursor_index:]:
        
        # loops through size sorted toks
        for chars in chars_by_len:
            
            # a regex match, matching from start of string only
            match = re.match(chars,string[cursor_index:])
            # put a value in previous tok, if there is a match it will reset to '', otherwise it will allow loop to exit
            previous_chars = string[cursor_index:]
            # if regex match
            if match:
                # noan_collector contains chars, append it to analyses and reset collector
                if nomap_collector:
                    transliteration.append(('NOMAP',nomap_collector))
                    nomap_collector = ''
                # update string cursor location
                cursor_index += match.span()[1]
                # map
                mapvalue = mapdict[chars]
                if mapvalue == '~':
                    mapvalue = transliteration[-1][1]
                #append mapvalue to transliteration
                transliteration.append((chars,mapvalue))
                # reset previous_chars so while loop does not exit
                previous_chars = ''
                # break on first match in order to loop through chars from the start
                break
        
        # exit condition: if remaining chars are not exhausted and equal previous_chars it means there is no mapping in the dict for remaining chunk, 
        # so increment by one char and check again (i.e the loop will restart and check again), capturing all nomap chars in that chunk until a mapping is found or chars are exhausted
        
        if cursor_index < len(string) and string[cursor_index:] == previous_chars:
            
            nomap_collector += string[cursor_index]
            cursor_index += 1
            # if chars are exhausted and noan_collector contains something, append it to analysis
            if cursor_index == len(string) and nomap_collector:
                transliteration.append(('NOMAP',nomap_collector))

    if logger:
        logger.count_translit_rules(transliteration) # list of mapping tupples
    
   
    transliteration = [chunk[1] for chunk in transliteration]
    transliteration = ''.join(transliteration)

    return transliteration

# def translit_caphi_token(token,mapdict):
#     transliteration = translit(token=token,mapdict=mapdict)
#     return ' '.join([chars[1] for chars in transliteration]).strip()

# def translit_token(token,mapdict,exceptional_spelling_dict): #NOTE: go directly from translit to translit_sentence, this will only break exceptional spellings and is just not necessary
#     capitalize_symbol = '±'
#     token = exceptional_spelling_dict.get(token,token)
#     if token[-1] == capitalize_symbol:
#         token = token[:-1]
#         transliteration = translit(token,mapdict=mapdict)
#         recomposed = ''.join([chars[1] for chars in transliteration]).strip()
#         recomposed = capitalize_loc(recomposed)
#     else:
#         transliteration = translit(token,mapdict=mapdict)
#         recomposed = ''.join([chars[1] for chars in transliteration]).strip()
#     return recomposed


def capitalize_loc(word): # for capitalizing hyphen '-' separated words and words beginning with hamza or 3ayn
    #when hyphen "-" is present, split into hyphen separated tokens and capitalize last token
    capitalize_symbol = '±'
    
    # remove capitalize symbol
    if word.endswith(capitalize_symbol):
        word = word[:-1]

    # in case of hyphens
    if '-' in word and not word.endswith('-') and not word.startswith('-'):
        split_tokens = word.split('-')
        main_token = split_tokens[-1]
        first_letter = main_token[0]
        #in case of hamza or 3ayn, next letter is capitalized
        if first_letter in {'ʼ','ʻ'}:  
            chars = [x for x in main_token]
            chars[1] = chars[1].capitalize()
            main_token = ''.join(chars)
        else:
            main_token = main_token.capitalize()
        capitalized = '-'.join(split_tokens)

    #for strings with no hyphen
    else:
        #in case of hamza or 3ayn, next letter is capitalized
        if len(word)>1 and word[0] in {'ʼ','ʻ'}: 
            chars = [x for x in word]
            chars[1] = chars[1].capitalize()
            capitalized =  ''.join(chars)
        # in normal case without hamza, 3ayn, or hyphen
        else:
            capitalized =  word.capitalize()
    return capitalized


def translit_simple(sentence,mapdict,exceptional_spelling_dict,logger=rules_logger):
    '''translit() + handles exceptional spellings and capitalizes first token of sentence'''
    # capitalize_symbol = '±' # no longer needed as capitalization is done directly
    transliterated = []
    sentence = str(sentence)
    for tok_index,token in enumerate(sentence.split()):
        # exceptional replacement
        if token in exceptional_spelling_dict:
            logger.count_exceptional_rules((token,exceptional_spelling_dict[token]))
            token = exceptional_spelling_dict[token]

        transliterated.append(translit(token,mapdict))
        if tok_index == 0: # first token
            logger.count_morph_rules(('index-0 capitalize','capitalized'))
            transliterated[-1] = capitalize_loc(transliterated[-1])
    return ' '.join(transliterated)

# def translit_morph(mada_sentnece_object,loc_mapdict,exceptional_spellings):

def get_diac(analysis):
    diacritized = []
    for sent in anlaysis:
        for word in sent.words:
            diac_word = sent.analysis[word]['diac']
            diacritized.append(diac_word)
    return recompose(' '.join(diacritized))

# def translit_diac(diac):
#     diacritized =


def translit_morph(mada_sentnece_object,loc_mapdict,exceptional_spellings,logger=rules_logger): #TODO: 1) break up into smaller functions. 2) turn transliterator into class with constructor
    '''takes a madaSentenceObject from parse_analyser_output()'''
    capschar = '±'
    words = mada_sentnece_object.words # list of words
    toks = mada_sentnece_object.toks # list of words which are diacritized and affix tokenized
    sentence_analysis = mada_sentnece_object.analysis # dictionary with word keys and analysis values
    
    modified_words = []
    # loop through words in mada_sentence_object (made of lists of words/tokenized_words and dictionary of analyeses for each word
    
    for tidx in range(len(toks)): #or len(words)
        
        # access word and tok (i.e tokenized word) by index
        word = words[tidx]
        tok = toks[tidx]
        # access analysis by dictionary lookup of word in sentence_analysis
        analysis = sentence_analysis[word]

        # handle exceptional spelling, skipping rest of loop
        if word in exceptional_spellings:
            logger.count_exceptional_rules((word,exceptional_spellings[word]))
            tok = exceptional_spellings[word]
            # capitalization                            NOTE: has to be done here for exceptional spellings as well as after modifications
            #capitalize sentence initial token          TODO: check all places where capschar may duplicate
            if tidx == 0 and not tok.endswith(capschar):
                logger.count_morph_rules(('index-0 capitalize','capitalized'))
                tok = tok+capschar

            modified_words.append(tok)
            continue

        ## beginning of morph rules

        # look ahead
        if tidx < len(toks)-1:
            nextword = words[tidx+1]
            nexttok = toks[tidx+1]
            nextanalysis = sentence_analysis[nextword]
        else:
            nextword = None
            nexttok = None
            nextanalysis = None
        

        bw = analysis['bw']
        bwsplit = bw.split('+')
        bwending = bwsplit[-1]
        bwbeginning = bwsplit[0]
        
        # rule 1 'lil'
        ## keep lil instead of li-al
        if analysis['prc0'] == 'Al_det' and analysis['prc1'] == 'li_prep':
            logger.count_morph_rules(('li+al','lil'))
            find = re.escape('لِ+ال')
            tok = re.sub(find,r'لِل',tok)
        
        #TODO: fix MADAMIRA bug for la prep thats supposed to be li, e.g: 'لنباتات': {'bw': 'la/PREP+nabAt/NOUN+At/NSUFF_FEM_PL+i/CASE_DEF_GEN',
                                                                                    #   'gloss': 'plants;vegetation',
                                                                                    #   'diac': 'لَنَباتاتِ',
                                                                                    #   'lemma': 'نَبات_1',


        ## remove case endings
        # if word ends with direct object or possessive pronoun do nothing
        if ('DO' in bwending) or ('POSS_PRON' in bwending): 
            logger.count_morph_rules(('case-ending','kept'))
            pass
        # elif word ends with case ending, nominall suffix, or a verb (imperfective, perfective, and command)
        elif ('CASE' in bwending) or ('IV' in bwending) or ('PV' in bwending) or ('CV' in bwending) or ('NSUFF' in bwending):
            logger.count_morph_rules(('case-ending','removed'))
            # remove final diacritic, including alif for tanween
            tok = re.sub(r'اً(±)?$',r'\1',tok) #alif tanween must be first
            tok = re.sub(r'[ًٌٍَُِ](±)?$',r'\1',tok)


        ## ta marbuta handling
        # spell ta-marbuta if its in construct state
        if 'ة' in tok:
            logger.count_morph_rules(('ta-marbuta','total'))
            if analysis['stt'] == 'c':
                # caveat: cannot be construct if followed by prep (additional rule for handling odd madamira analysis)
                if nextanalysis and 'PREP' in nextanalysis['bw'].split('+')[0]:
                    logger.count_morph_rules(('ta-marbuta','not-construct (followed by prep)'))
                    pass
                else:
                    logger.count_morph_rules(('ta-marbuta','construct'))
                    # put a sukun on the ta-marbuta for transliterator to spell it
                    tok = re.sub(r'ة',r'ةْ',tok)

        ## split single letter proclitic
        # splitprepositions .. currently handling ب and ل only
        if 'PREP' in bwbeginning and len(bwsplit)>1:  # length condition to make sure letters are actual proclitics
            an = analysis['lemma'].split('_')[0]
            if an in {'لِ-','بِ'}:
                logger.count_morph_rules(('single-letter clitic','split'))
                tok = re.sub(r'([لب][َُِ]?)',r'\1-',tok)
  
        # capitalization
        #capitalize sentence initial token          TODO: check all places where capschar may duplicate
        if tidx == 0 and not tok.endswith(capschar):
            logger.count_morph_rules(('index-0 capitalize','capitalized'))
            tok = tok+capschar

        ##conditions for capitalizing non-initial tokens
        elif tidx > 0:
            # look back variable
            before = toks[tidx-1]

            # capitalize after period, (a simple sentence segmenter) TODO: what happens when periods are not sentence markers such as acronyms etc
            if before == '.':
                logger.count_morph_rules(('after . capitalize','capitalized'))
                tok = tok+capschar
            
            # capitalize if gloss is capitalized and pos is proper noun or adjective (and word is not arabic punctuation and not capitalized for other reasons)
            if analysis['pos'] in {'noun_prop','adj'} and analysis['gloss'] and analysis['gloss'][0].isupper() and word not in {'،','؛'} and not tok.endswith(capschar):
                # print(tok)
                logger.count_morph_rules(('adj/nounprop capitalized gloss','capitalized'))
                tok = tok+capschar

            #elif pos in nounprop NOTE: this is to make sure proper nouns are capitalized regardless of gloss and other conditions but maybe better to collapse with previous condition
            elif analysis['pos'] in {'noun_prop'} and not tok.endswith(capschar):
                logger.count_morph_rules(('nounprop','capitalized'))
                tok = tok+capschar
   
        
        ## append modified spellings to token holder
        # tokenization marker replacement.
        if '+' in tok:
            tmp = tok.replace('+','- ').split(' ') 
            modified_words += tmp
        else:
            modified_words.append(tok)
            
    

    # converting everything
    transliterated_words = [] 
    for tok in modified_words:
        if tok:
            # capitalize  NOTE: THEN tranlisterate so as to remove final capschar for proper transliteration
            if tok.endswith(capschar):
                tok = tok[:-1]
                transliterated_tok = translit(tok,loc_mapdict)
                transliterated_tok = capitalize_loc(transliterated_tok)
            else:
                transliterated_tok = translit(tok,loc_mapdict)
            # capitalize if capschar at the end
            transliterated_words.append(transliterated_tok)      
        else:
            if tok == '':
                pass
            else:
                print(f'whats this tok?: <{tok}>') #TODO: remove this since it doesn't seem to be doing anything

    transliterated_sentence = ' '.join(transliterated_words)
    
    return recompose(transliterated_sentence,mode='rom') 





@log_durations(logging.info)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', default='data/processed/dev.tsv', help='path to file containing Arabic lines, must specify -i txt or -i tsv with optional headername, default: -i tsv ar ')
    parser.add_argument('output', help= 'specify output location for predictions')
    parser.add_argument('-i','--input_type', required=True, nargs='+', default=['tsv','ar'], help='options: 1)txt: if file is single column txt file (no header); 2)tsv <optional:input-header>: input is multicolumn tsv.  unless specified, header defaults to "ar"') #TODO: add csv option?
    parser.add_argument('-m','--mode', required=True, help= 'options: 1)translit_simple: apply rules to raw text without diacritics or morphological information; 2)translit_morph: apply rules to morphologically analyzed text')
    parser.add_argument('-da','--dont_reanalyse', action='store_true',help= "don't reanalyse sentences as analysis is already saved")
    parser.add_argument('-l','--log_rules', action='store_true',help= "create a rule freq tsv in reports directory") #TODO: make logger counts optional
    args = parser.parse_args()
    
    setname = args.input.split('/')[-1].replace('.tsv','')
    name = args.mode.split('_')[-1]
    print(f'predicting {args.input}')
    logging.info(f'predicting {args.input}')    


    # input
    input_type = {idx:value for idx,value in enumerate(args.input_type)}
    if input_type[0]=='tsv':
        lines = pd.read_csv(args.input,delimiter='\t')
        if input_type.get(1,'ar') not in lines.columns:
            raise Exception('specified input column is not in input file')
        ar_lines = lines[input_type.get(1,'ar')] # defaults to 'ar' column if no column is specified
    elif input_type[0] == 'txt':
        ar_lines = pd.read_csv(args.input,delimiter='\t',header=None)[0]
    else:
        raise Exception('no -i --input_type selected, please choose -i txt for single column input or -i tsv <optional column name; default: ar > for tsv')

    # load loc mappings and exceptional spellings
    locmap = load_loc_mappings()
    locexceptional = load_exceptional_spellings()

    # predict
    if args.mode == 'simple':
        predictions = ar_lines.apply(lambda x: translit_simple(x,locmap,locexceptional))

    elif args.mode == 'morph':
        Path(f'{project_dir}/data/processed_for_madamira/analyser_input').mkdir(parents=True,exist_ok=True)
        Path(f'{project_dir}/data/processed_for_madamira/analyser_output').mkdir(parents=True,exist_ok=True)
        
        analyse_input_path = f'{project_dir}/data/processed_for_madamira/analyser_input/{setname}.xml'
        analyse_output_path = f'{project_dir}/data/processed_for_madamira/analyser_output/{setname}.xml'
        

        if not args.dont_reanalyse:  #TODO: change this to see if analyse_output_path exists and ask if reanalysis is necessary
            # tokenize to make ready for config file
            tokenized_ar_lines = list(ar_lines.apply(tokenize_skiphyph).values)

            # generate config file
            analyser_input = analyse.generate_analyser_input(tokenized_ar_lines)
            
            # write config file
            analyse.write_xml(analyser_input,analyse_input_path)

            # anlyse
            analyse.analyse_standalone(analyse_input_path,analyse_output_path)

        # load analysis
        analysis = analyse.load_analysis(analyse_output_path)

        # parse analysis
        mada_sent_objects = analyse.parse_analyser_output(analysis)
        
        predictions = [] # TODO: this is done through a loop, whereas simple translit is done through a pandas.apply.  should prob make them the same but storing mada_sent_obj in dataframe requires more work
        for sent in mada_sent_objects:
            predictions.append(translit_morph(sent,locmap,locexceptional))

        predictions = pd.DataFrame(predictions)
        
    else:
        raise Exception('Invalid -m --mode')

    

    # write predictions
    predictions.to_csv(args.output,sep='\t',index=False,header=False)

    # write rules freq logger to tsv
    if args.log_rules:
        translit_rules_freq = pd.DataFrame([{'from':x[0],'to':x[1],'freq':y} for x,y in rules_logger.translit_rules.items()]).sort_values('freq',ascending=False)
        translit_rules_freq.to_csv(f'{project_dir}/reports/translit_rules_freq-{setname}_{name}.tsv',sep='\t',index=False)
        
        morph_rules_freq  = pd.DataFrame([{'from':x[0],'to':x[1],'freq':y} for x,y in rules_logger.morph_rules.items()]).sort_values('freq',ascending=False)
        morph_rules_freq.to_csv(f'{project_dir}/reports/morph_rules_freq-{setname}_{name}.tsv',sep='\t',index=False)

        exceptional_rules_freq = pd.DataFrame([{'from':x[0],'to':x[1],'freq':y} for x,y in rules_logger.exceptional_rules.items()]).sort_values('freq',ascending=False)
        exceptional_rules_freq.to_csv(f'{project_dir}/reports/exceptional_rules_freq-{setname}_{name}.tsv',sep='\t',index=False)

if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt,filename='reports/translit_rules.log',filemode='a')

    main()

    