import pandas as pd
import logging
import re
from pathlib import Path
from funcy import log_durations
import argparse
import repackage
repackage.up()
from predict import translit_rules
from data.make_dataset import recompose, tokenize_skiphyph

project_dir = Path(__file__).resolve().parents[2]



def load_mle_model(size=None,mle_model_tsv=None,as_df=False): #TODO: change model to dict
    if mle_model_tsv:
        mledf = pd.read_csv(mle_model_tsv,delimiter='\t')
    elif size:
        mledf = pd.read_csv(f'{project_dir}/models/mle/size{float(size)}.tsv',delimiter='\t')
    
    if as_df:
        return mledf
    else:
        return mledf.set_index('source')['target'].to_dict()



def apply_mle(sentence,mledict):
    predict_mle = []
    for tok in tokenize_skiphyph(sentence).split():
        mle_tok = mledict.get(tok,'OOV')
        predict_mle.append(mle_tok)
    return recompose(' '.join(predict_mle),mode='rom')



def apply_mle_translit_simple_backoff(sentence,mledict,locmap,locexceptional):
    predict_mle = []
    for tok_index, tok in enumerate(tokenize_skiphyph(sentence).split()):
        mle_tok = mledict.get(tok, translit_rules.translit_simple(tok,locmap,locexceptional))
        if tok_index == 0:
            mle_tok = translit_rules.capitalize_loc(mle_tok)
        predict_mle.append(mle_tok)
    return recompose(' '.join(predict_mle),mode='rom')

def apply_mle_translit_morph_backoff(sentence,mledict,backoff_sentences,sent_index):
    predict_mle = []
    for tok_idx, tok in enumerate(tokenize_skiphyph(sentence).split()):
        if tok in mledict:
            mle_tok = mledict[tok]
        else:
            bckf_sent = backoff_sentences[sent_index]
            bckf_tokens = tokenize_skiphyph(bckf_sent).split()
            mle_tok = bckf_tokens[tok_idx]
        predict_mle.append(mle_tok)
    return recompose(' '.join(predict_mle),mode='rom')




@log_durations(logging.info)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', default='data/processed/dev.tsv', help='path to file containing Arabic lines, must specify -i txt or -i tsv with optional headername, default: -i tsv ar ')
    parser.add_argument('output', help= 'output file for predictions')
    parser.add_argument('-i','--input_type', required=True, nargs='+', default=['tsv','ar'], help='options: 1)txt: if file is single column txt file (no header); 2)tsv <optional:input-header>: input is multicolumn tsv.  unless specified, header defaults to "ar"') #TODO: add csv option?
    parser.add_argument('-m','--mle_model', required=True, help='path to mle_model tsv')
    parser.add_argument('-b','--backoff',required=True, 
                        help= """backoff options:\n\
                        OOV                  no backoff - returns OOV\n\
                        translit_simple      Simple transliteration\n\
                        <prediction_file>    Specify prediction file from another model as backoff\
                        """)

    args = parser.parse_args()
    input_name = args.input.split('/')[-1].replace('.tsv','')

    logging.info(f'predicting {args.input}')

    # load mle model
    
    mle_model = args.mle_model
    model_name = args.mle_model.split('/')[-1].replace('.tsv','')
    mledict = load_mle_model(mle_model_tsv=mle_model)


    # input
    input_type = {idx:value for idx,value in enumerate(args.input_type)}
    if input_type[0]=='tsv':
        lines = pd.read_csv(args.input,delimiter='\t')
        if input_type.get(1,'ar') not in lines.columns:
            raise Exception('specified input column is not in input file')
        ar_lines = lines[input_type.get(1,'ar')] # defaults to 'ar' column if no column is specified
    elif input_type[0] == 'txt':
        ar_lines = pd.read_csv(args.input,delimiter='\t',header=None)[0]

    
    # backoff and apply
    logging.info(f'backoff: {args.backoff}\t model: {model_name}')
    if args.backoff == 'OOV':
        predictions = ar_lines.apply(lambda x: apply_mle(x,mledict=mledict))
    elif args.backoff == 'translit_simple':
        locmap = translit_rules.load_loc_mappings()
        locexceptional = translit_rules.load_exceptional_spellings()
        predictions = ar_lines.apply(lambda row: apply_mle_translit_simple_backoff(row,mledict=mledict,locmap=locmap,locexceptional=locexceptional))
    else:
        try:
            backoff_predictions = pd.read_csv(args.backoff,delimiter='\t',header=None)
        except Exception as e:        
            print('Invalid path to backoff predictions')

        backoff_predictions = list(backoff_predictions[0].values)
        predictions = []
        for sent_idx, sent in enumerate(ar_lines):
            try:
                sent_prediction = apply_mle_translit_morph_backoff(sent,mledict=mledict,backoff_sentences=backoff_predictions,sent_index=sent_idx)
            except Exception as e:
                print(e)
                print(sent)
                print()
                print(translit_morph_predictions[sent_idx])
                exit()
            predictions.append(sent_prediction)

        predictions = pd.DataFrame(predictions)
   
    

    predictions.to_csv(args.output,sep='\t',index=False,header=False)


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt,filename='reports/mle_predict.log',filemode='a')

    main()
