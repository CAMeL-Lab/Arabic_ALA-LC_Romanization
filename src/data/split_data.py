import pandas as pd
import logging
import argparse


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_tsv', default='data/extracted_lines/extracted_lines.tsv', nargs='?', help='path to tsv containing extracted parallel lines with unique record ids')
    parser.add_argument('-o','--out', default='data/extracted_lines', help= 'output directory for split data sets')
    args = parser.parse_args()

    lines = pd.read_csv(args.input_tsv,delimiter='\t')

    lines = create_splits(lines)


    sets = ['dev','train','test']
    for s in sets:
        splitdata = lines[lines['splits']==s]
        splitdata.to_csv(f'{args.out}/extracted_{s}.tsv',sep='\t',index=False)

if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt,filename='reports/split_data.log',filemode='a')

    main()