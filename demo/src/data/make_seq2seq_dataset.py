import pandas
import argparse
from pathlib import Path
import pandas as pd
import os

project_dir = Path(__file__).resolve().parents[2]

def prep_data_for_seq2seq(processed_path,splits_ldc_path,size_ratio=[1]):
    
    allsets = []
    splits = ['dev','train','test']
    for s in splits:
        df = pd.read_csv(f'{processed_path}/{s}.tsv',delimiter='\t')
        allsets.append(df)

    allsets = pd.concat(allsets)
    
    seqhome = splits_ldc_path
    for s in splits:
        if s == 'dev':
            arpath = 'dev/dev-ar-recomposed-lines'
            rompath = 'dev/dev-rom-clean-lines'
            allsets[allsets['splits']==s]['ar'].to_csv(f'{seqhome}/{arpath}',sep='\t',header=False,index=False) #NOTE: if sep delimiter is in the line, to_csv will create quotes around the line, so make sure its \t
            
            allsets[allsets['splits']==s]['rom'].to_csv(f'{seqhome}/{rompath}',sep='\t',header=False,index=False)
        elif s == 'test':
            arpath = 'test/test-ar-recomposed-lines'
            rompath = 'test/test-rom-clean-lines'
            allsets[allsets['splits']==s]['ar'].to_csv(f'{seqhome}/{arpath}',sep='\t',header=False,index=False)
            allsets[allsets['splits']==s]['rom'].to_csv(f'{seqhome}/{rompath}',sep='\t',header=False,index=False)
        elif s == 'train':
            rompathsource = 'source/train-rom-clean-lines'
            rompath = 'train/train-rom-clean-lines'
            arpath = 'train/train-ar-recomposed-lines'
            for ratio in size_ratio:
                size = int(len(allsets[allsets['splits']==s])*ratio)
                Path(f'{project_dir}/seq2seq/temp_size{ratio}').mkdir(parents=True, exist_ok=True)
                allsets[allsets['splits']==s]['ar'][:size].to_csv(f'{seqhome}/{arpath}_size{ratio}',sep='\t',header=False,index=False)
                allsets[allsets['splits']==s]['rom'][:size].to_csv(f'{seqhome}/{rompath}_size{ratio}',sep='\t',header=False,index=False)
                allsets[allsets['splits']==s]['rom'][:size].to_csv(f'{seqhome}/{rompathsource}_size{ratio}',sep='\t',header=False,index=False)




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('processed_dir', default='data/processed', help='path to directory containing processed splits')
    parser.add_argument('seq2seq_dir', default='seq2seq/splits_ldc', help='path to directory for storing seq2seq ready splits')
    parser.add_argument('-s','--size',nargs='+',default=[1,0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625],type=float, help='specify training data size ratios to be created')
    args = parser.parse_args()

    
    prep_data_for_seq2seq(args.processed_dir,args.seq2seq_dir, size_ratio=args.size)
    



if __name__ == "__main__":

    main()