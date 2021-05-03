# -*- coding: utf-8 -*-
from pathlib import Path
import os
import argparse
import logging
from camel_tools.utils.charsets import UNICODE_PUNCT_CHARSET
import pandas as pd
import re
from funcy import log_durations
from camel_tools.utils.normalize import normalize_unicode

# punctuation set used in tokenize_hyph, which skips hyphens. NOTE: LOC hamza and 3ayn are not! part of UNICODE_PUNCT_CHARSET so no need to worry about them.
puncs = UNICODE_PUNCT_CHARSET-{'-'}#,'ʼ','ʻ'}
puncs = dict(zip(puncs,len(puncs)*['']))

# manual tag selection is documented in documentation/tag_selection(dev).tsv and 01-explore_dev.ipynb
SELECTED_TAGS = [
 '245a',
 '245c',
 '100a',
 '260b',
 '250a',
 '245b',
 '264b',
 '264a',
 '700a',
 '490a',
 '600a',
 '246a',
 '440a',
 '830a',
 '260f',
 '700t',
 '490v',
 '600t',
 '500a',
 '740a',
 '111a',
 '110b',
 '440v',
 '246b',
 '440p',
 '800a',
 '775t',
 '775d',
 '775b',
 '830v'
 ]

punc_remove_dict = dict(zip(UNICODE_PUNCT_CHARSET,['']*len(UNICODE_PUNCT_CHARSET))) #required for depunc(string) but no needed to load for every string
def depunc(string,keep_hyph=False):
    dct = punc_remove_dict.copy()
    if keep_hyph:
        dct.pop('-')
    mapped = map(lambda x: dct.get(x,x),string) # for each char if char is in punc_remove_dict get dict value (i.e, empty string ''), else get char itself
    return ''.join(mapped)


# TODO: make consisten filter names (anyways filters returning false will be excluded, and true included)


def drop_nan(dfrow): 
    '''checks if ar and rom are of type str, and further checks if those lines are not numeric when stripped of punctuation'''
    return not dfrow.isnull().any()

def filter_nonnumeric_str(dfrow): 
    '''checks if ar and rom are of type str, and further checks if those lines are not numeric when stripped of punctuation'''
    ar = dfrow['ar']
    rom = dfrow['rom']
    if type(ar) == str and type(rom) == str: 
        if not depunc(ar).isnumeric() and not depunc(rom).replace(' ','').isnumeric():  
            return True
        else:
            return False
    else:
        return False

def drop_link_errors(dfrow):
    if dfrow['link-error']==False:
        return True
    else:
        return False

def filter_persian(dfrow):
# perfilter
    sent = str(dfrow['rom']).split()
    for tok in sent:
        if tok.endswith('-i') or tok.endswith("-'i"):
            return False
    else:
        return True

def filter_tags(dfrow,selected_tags=SELECTED_TAGS):
    combtag = str(dfrow['comb.tag'])
    if combtag in selected_tags:
        return True
    else:
        return False

def filter_nonalligned(dfrow):
    rom = str(dfrow['rom'])
    ar = str(dfrow['ar'])
    
    rom = recompose(tokenize_skiphyph(rom),mode='rom').split()
    
    ar = recompose(tokenize_skiphyph(ar),mode='ar').split()

    if len(rom)==len(ar):
        return True
    else:
        return False


def filter_data(lines,filter_funcs, print_log = True, log_additional_columns = ['recID','comb.tag']):
    '''applies filter funcs to lines, and logs how many lines were removed, as well as additional logs such as 'comb.tag' or 'id' '''
    
    filtered_lines = lines.copy()
    previous = pd.DataFrame()
    for func in filter_funcs:
        print(func.__name__)
        logging.info(func.__name__)
        condition = filtered_lines.apply(func,axis=1)==True
        previous = filtered_lines
        filtered_lines = filtered_lines[condition]
        
        if print_log:
            print(f'# of removed lines: {len(previous)-len(filtered_lines)}')
            logging.info(f'# of removed lines: {len(previous)-len(filtered_lines)}')
            if log_additional_columns:
                for column in log_additional_columns:
                    print(f'# of removed {column}: {len(set(previous[column]))-len(set(filtered_lines[column]))}')
                    logging.info(f'# of removed {column}: {len(set(previous[column]))-len(set(filtered_lines[column]))}')
        
    # print('# of removed by tag:')
    # print(lines[~condition]['comb.tag'].value_counts()[:50]) # prints most frequent removed tags and their frequency
    return filtered_lines


### recompose sentences

# 1
def recompose_waw(line): # reattach waws
    return line.replace(' و ', ' و')

# 2
def tokenize_skiphyph(sent,puncs=puncs):
    chars = []
    sent = str(sent)
    for char in list(sent):
        if char in puncs:
            chars.append(' '+char+' ')
        else:
            chars.append(char)
    sent = ''.join(chars)
    sent = re.sub(r'\s+',r' ',sent)
    return sent.strip()

# 3
def remove_extra_space(sent):
    return re.sub(r'\s+',r' ',sent)

# 4
def recompose_hyphens(sent,mode): #TODO: there is no longer a separate rom handling, recomposition happens on all equally, so other code should be changed accordingly
    sent = re.sub(r'\s*(-+)\s*',r' \1 ',sent)
    if mode == 'rom':
        # NOTE: Rule 16 b form loc rules: (b) Inseparable prepositions, conjunctions, and other prefixes are connected with what follows 
              # DEFINE prc3 prc3:0 prc3:na prc3:>a_ques
              # DEFINE prc2 prc2:fa_conn prc2:fa_rc prc2:na prc2:0 prc2:wa_part prc2:wa_sub prc2:fa_sub prc2:wa_conj prc2:fa_conj
              # DEFINE prc1 prc1:la_emph prc1:ka_prep prc1:fiy_prep prc1:li_jus prc1:0 prc1:la_rc prc1:li_prep prc1:wA_voc prc1:yA_voc prc1:ta_prep prc1:wa_prep prc1:sa_fut prc1:hA_dem prc1:bi_prep prc1:na prc1:la_prep prc1:bi_part
              # DEFINE prc0 prc0:na prc0:mA_part prc0:0 prc0:Al_det prc0:mA_neg prc0:lA_neg prc0:mA_rel
        # NOTE: from database almor-msa-r13: DEFINE prc1 prc1:la_emph prc1:ka_prep prc1:fiy_prep prc1:li_jus prc1:0 prc1:la_rc prc1:li_prep prc1:wA_voc prc1:yA_voc prc1:ta_prep prc1:wa_prep prc1:sa_fut prc1:hA_dem prc1:bi_prep prc1:na prc1:la_prep prc1:bi_part
        sent = re.sub(r'\b(al|ka|fa|la|bi|lil|wa|lā|mā|li|sa|ta|)\s*-\s+',r'\1-',sent) #check to see if all applicable prefixes are covered
    return sent.strip()

def recompose_lacunas(sent):
    sent = re.sub(r'(\.{2,})',r' \1 ',sent)
    sent = remove_extra_space(sent).strip()
    return sent
# 5
def recompose_right_punc(sent):
    right_attaching_puncs = re.escape(r'.?,)]!،؟')
    sent = re.sub(f'\s*([{right_attaching_puncs}])',r'\1',sent)
    return sent.strip() # must make sure no trailing spaces at the end!!!!
# 6
def recompose_left_punc(sent):
    left_attaching_puncs = re.escape(r'([')
    sent = re.sub(f'\s*([{left_attaching_puncs}])\s*',r' \1',sent)
    return sent.strip()
# 7
def recompose_date_slash(sent):
    return re.sub(r'(\d)\s*(/)\s*(\d)',r'\1\2\3',sent)

# 8
def recompose_quotes(sent):
    chars = list(sent)
    begin_quote = False
    bef = ''
    aft = ''
    for char_index in range(len(chars)):
        
        char = chars[char_index]
        if char_index>0:
            bef = chars[char_index-1]
        if char_index<len(chars)-1:
            aft = chars[char_index+1]

        if char in {'"',"'"}:
            if not begin_quote:
                
                begin_quote = True
                if aft == ' ':
                    chars[char_index+1] = ''
            else:
                begin_quote = False
                if bef == ' ':
                    chars[char_index-1] = ''
    return ''.join(chars)



def recompose(sent,mode): #TODO: this was changed so only difference between ar and rom is waw handling

    #NOTE: order of rules is not trivial!!
    sent = remove_extra_space(sent)
    sent = tokenize_skiphyph(sent)
    sent = recompose_hyphens(sent,mode='rom')
    sent = recompose_right_punc(sent)
    sent = recompose_lacunas(sent)
    sent = recompose_left_punc(sent)
    sent = recompose_date_slash(sent)
    sent = recompose_quotes(sent)
    
    if mode=='ar':
        sent = recompose_waw(sent)
    elif mode=='rom':
        pass
    else:
        raise Exception('make sure you have the right recompose mode 1)ar  2)rom')

    return sent

def create_splits(lines):
    
    def dosplits(record_list_row):
        if record_list_row.name%10 == 0:
            return 'dev'
        elif record_list_row.name%10 in range(1,9):
            return 'train'
        elif record_list_row.name%10 == 9:
            return 'test'

    record_list = lines['recID'].drop_duplicates().reset_index(drop=True)
    record_list = pd.DataFrame(record_list)

    record_list['splits'] = record_list.apply(dosplits,axis=1)

    stats = pd.DataFrame(record_list.splits.value_counts(normalize=True)).merge(record_list.splits.value_counts(),right_index=True,left_index=True).rename(columns={'splits_x':'% of total','splits_y':'# of records'})

    logging.info('\n'+stats.to_string())

    return lines.merge(record_list,on='recID')

# countnormalized = 0
# countbadcharremoval = 0
# countbadcharreplacement = 0

def preliminary_cleaners(line):
    line = str(line)
    normalized = normalize_unicode(line)
    badchars = {'’':'ʼ','‘':'ʻ',"'":"ʼ","ʾ":"ʼ",chr(8221):'"',chr(8220):'"'} # replacements # 'ک':'ك' letters such as گ should be handled in translit map. see rules for "Letters Representing Non-Arabic Consonants"
    cleanedsent = ''
    for char in normalized:
        if ord(char) in {10, 8204, 8205, 8206, 8207, 8234, 8236, 8238, 65533}: #removals
            pass
        else:
            if char in badchars:
                cleanedsent += badchars[char]
            else:
                cleanedsent += char
    return cleanedsent

#TODO: this is too messy
def count_tokens(df,rom_col='rom',ar_col='ar'):
    rom_tokens = 0
    ar_tokens = 0

    for line in df[[rom_col,ar_col]].iterrows():
        rom_tokens += len(recompose(tokenize_skiphyph(line[1][rom_col]),mode='rom').split())
        ar_tokens += len(recompose(tokenize_skiphyph(line[1][ar_col]),mode='ar').split())

    return rom_tokens,ar_tokens


@log_durations(logging.info)
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('input_tsvs', default='data/extracted_lines/extracted_lines.tsv', nargs='*', help='path to tsv(s) containing extracted parallel lines with unique record ids')
    parser.add_argument('-o','--out', default='data/processed', help= 'output directory for cleaned and processed dat')
    parser.add_argument('-ds','--dont_split', action='store_true', help= 'output directory for cleaned and processed dat')
    args = parser.parse_args()

    total_lines = []
    total_filtered_lines = []
    for tsv in args.input_tsvs:
        
        lines = pd.read_csv(tsv,delimiter='\t')
        
        # NOTE: cleaning has to happen before filtering
        lines['rom'] = lines['rom_raw'].apply(lambda x: recompose(preliminary_cleaners(x),mode='rom'))
        lines['ar'] = lines['ar_raw'].apply(lambda x: recompose(preliminary_cleaners(x),mode='ar'))
        
        lines['comb.tag'] = lines.apply(lambda x: str(x['tag'])+str(x['subtag']),axis=1)
        total_lines.append(lines)
        filtered_lines = filter_data(lines=lines,filter_funcs=[drop_nan,drop_link_errors,filter_tags,filter_nonalligned,filter_nonnumeric_str,filter_persian])
        

        # drop link-error column
        filtered_lines = filtered_lines.drop('link-error',axis=1)

        
        if args.dont_split:
            for tsv in args.input_tsvs:
                tsv = tsv.split('/')[-1].replace('extracted_','')
                filtered_lines = filtered_lines.reset_index().rename(columns={'index':'sentID'})
                
                # count lines
                linecount = len(filtered_lines)
                print(f'# of lines: {linecount}')
                logging.info(f'# of lines: {linecount}')
                
                # tok countd
                romtokcount, artokcount = count_tokens(filtered_lines)
                print(f'number of tokens: rom: {romtokcount} ; ar: {artokcount}')
                logging.info(f'number of tokens: rom: {romtokcount} ; ar: {artokcount}')
                
                order = ['sentID','rom','ar','rom_raw','ar_raw','comb.tag','recID','subtag','tag','link','source']
                filtered_lines[order].to_csv(f'{args.out}/{tsv}',sep='\t',index=False)
                total_filtered_lines.append(filtered_lines)
        else:
            
            filtered_lines = create_splits(filtered_lines)
            sets = ['dev','train','test']
            for s in sets:
                print(f'split: {s}')
                logging.info(f'split: {s}')
                splitdata = filtered_lines[filtered_lines['splits']==s]
                splitdata = splitdata.reset_index().rename(columns={'index':'sentID'}) 

                # count lines
                linecount = len(splitdata)
                print(f'# of lines: {linecount}')
                logging.info(f'# of lines: {linecount}')
                
                # tok count
                romtokcount, artokcount = count_tokens(splitdata)
                print(f'number of tokens: rom: {romtokcount} ; ar: {artokcount}')
                logging.info(f'number of tokens: rom: {romtokcount} ; ar: {artokcount}')

                total_filtered_lines.append(splitdata)

                order = ['sentID','rom','ar','rom_raw','ar_raw','comb.tag','recID','subtag','tag','link','source','splits']
                splitdata[order].to_csv(f'{args.out}/{s}.tsv',sep='\t',index=False)


    total_lines = pd.concat(total_lines)
    total_filtered_lines = pd.concat(total_filtered_lines)

    # log splits ratio
    if not args.dont_split:
        splitratios = total_filtered_lines.value_counts('splits',normalize=True).to_string()
        print(f'split ratios:\n{splitratios}')
        logging.info(f'split ratios:\n{splitratios}')


    print('total')
    logging.info('total')
    print('total # of removed lines:',len(total_lines)-len(total_filtered_lines))
    logging.info(f'total # of removed lines: {len(total_lines)-len(total_filtered_lines)}')
            
    for column in ['recID','comb.tag']:
        print(f'total # of removed {column}: {len(set(total_lines[column]))-len(set(total_filtered_lines[column]))}')
        logging.info(f'total # of removed {column}: {len(set(total_lines[column]))-len(set(total_filtered_lines[column]))}')




if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt,filename='reports/clean_dataset_job.log',filemode='a')

    
    
    main()
    
