import pandas as pd
import repackage
import re
from camel_tools.utils.charsets import UNICODE_PUNCT_CHARSET
import logging
from funcy import log_durations
import argparse
from pathlib import Path
repackage.up()
from data.make_dataset import recompose, puncs


project_dir = Path(__file__).resolve().parents[2]



def load_traindf(path=f'{project_dir}/data/processed/train.tsv'):
    return pd.read_csv(path,delimiter='\t')


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

@log_durations(logging.info)
def train_mle(traindf,size_ratio=1, return_dict=False): # levdis 
    '''trains on aligned sentences only (same len), #could also add a levenstein threshold alignment based on simple_translit to avoid first/last name switcharoos
     returns dataframe, unless return_dict is set to true'''
    
    traindf = traindf[:int(len(traindf)*size_ratio)]
    parallel_tokens = []
    skipped = [0]
    def get_aligned_tokens(dfrow,parallel_tokens=parallel_tokens,skipped=skipped):
        target = dfrow['rom']
        source = dfrow['ar']
        target = tokenize_skiphyph(target)
        source = tokenize_skiphyph(source)
        
        # create a df of the tokenizes sentence
        target = pd.Series(target.split(),dtype=str)
        source = pd.Series(source.split(),dtype=str)
        
        if len(target)==len(source):
            parallel_tokens.append(pd.DataFrame(data={'source':source,'target':target}))
        else:
            skipped[0] += 1

    traindf.apply(get_aligned_tokens,axis=1)

    parallel_tokens = pd.concat(parallel_tokens)
    mledf = parallel_tokens.groupby(['source','target']).size().reset_index(name='freq').sort_values('freq',ascending=False) #make and sort by most freq to least
    
    mledf =  mledf.drop_duplicates('source') # drops duplicate source, keeping first which is most freq
    
    
    print(f'# of misaligned sentences skipped: {skipped[0]}')
    logging.info(f'# of misaligned sentences skipped: {skipped[0]}')
    #### tweaks

    # skip non-punc mapping to punc
    alltokens = len(mledf)
    mledf = mledf[mledf.apply(lambda x: (x['source'] in UNICODE_PUNCT_CHARSET ) == (x['target'] in UNICODE_PUNCT_CHARSET),axis=1)]

    skippedtokens = alltokens - len(mledf)    
    
    print(f'# of tokens skipped becauses nonpunc maps to punc: {skippedtokens}')
    logging.info(f'# of tokens skipped becauses nonpunc maps to punc: {skippedtokens}')

    #TODO: make sure mappings for low freq occurences are above a certain levenshtein threshold
    
    if return_dict:
        return mledf.set_index('source')['target'].to_dict()
    else:
        return mledf



@log_durations(logging.info)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='path to source/target file containing columns "rom" and "ar" ')
    parser.add_argument('output' , help= 'specify output location to store mle model')
    parser.add_argument('-s', '--size_ratio', nargs="+", default=1, type=float, help= 'training size ratios, e.g: 0.5') # 1 0.5 0.25 0.125 0.0625 0.03125 0.015625
    args = parser.parse_args()
    
    print(f'training mle with: {args.input}')
    logging.info(f'training mle with: {args.input}')

    for size in args.size_ratio:
        print(f'train size_ratio: {size}')
        logging.info(f'train size_ratio: {size}')

  
        outpath = f'{args.output}size{size}.tsv'

        Path(args.output).mkdir(parents=True,exist_ok=True)

        traindf = load_traindf(path=args.input)

        print(f'train size # of sentences: {len(traindf)*size}')
        logging.info(f'train size # of sentences: {len(traindf)*size}')  # this includes non-aligned sentences which are skipped in mle_model creation

        mle_model = train_mle(traindf,size)
        
        tokencount = mle_model['freq'].sum()
        
        print(f'train size # of tokens {tokencount}')
        logging.info(f'train size # of tokens {tokencount}')

        mle_model.to_csv(outpath,sep='\t',index=False) #,header=False)


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt,filename='reports/train_mle.log',filemode='a')

    main()
