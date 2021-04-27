import pandas as pd
import repackage
import os
repackage.up()
import translit_rules 

'''This program validates the ar2phon_map.tsv file produces the expected transliterations by comparing to
a list of words in validate_mappings.tsv. Words are taken from LOC Arabic Transliteration Rules document 
(source: https://www.loc.gov/catdir/cpso/romanization/arabic.pdf), as well as some additional words'''




# pd.set_option('display.max_rows', None)

caphimap = translit_rules.get_caphi_mappings()
locmap = translit_rules.get_loc_mappings()

# copy safebw to map file for easy readability of rules
# mapping = pd.read_csv(Path(os.getcwd()).parent.joinpath('src','predict','ar2phon','ar2phon_map.tsv'),delimiter='\t').fillna('')
# mapping['Arabic'].apply(ar2safebw).to_clipboard(index=False,header=False)


validation = pd.read_csv(f'{os.getcwd()}/src/predict/ar2phon/validate_mappings.tsv',delimiter='\t').fillna('')
validation['predict_caphi'] = validation['arabic'].apply(lambda x: translit_rules.translit_caphi_token(x,caphimap))
validation['predict_loc'] = validation['arabic'].apply(lambda x: translit_rules.translit_loc_token(x,locmap))
validation['match_caphi'] = validation.apply(lambda x: x['caphi']==x['predict_caphi'],axis=1)
validation['match_loc'] = validation.apply(lambda x: x['loc']==x['predict_loc'],axis=1)

print(validation.to_string())

print('NOTE: 3 validations (صمد), (فعلوا) and (أُولائِكَ) will return False by design because they were listed in the LOC document but are odd spellings or require additional morphological information')