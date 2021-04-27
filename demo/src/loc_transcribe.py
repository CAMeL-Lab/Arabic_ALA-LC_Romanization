'''train predict evaluate'''
import argparse
import logging
from funcy import print_durations
from pathlib import Path
import os
import pandas as pd

project_dir = Path(__file__).resolve().parents[1]


def score_evals(eval_paths):
    scores = {}
    for e in eval_paths:
        evaldf = pd.read_csv(e,delimiter='\t')
        name = e.split('/')[-1].replace('.tsv','')
        setname = e.split('/')[-2]
        matches = {}
        for match in [col for col in evaldf.columns if col.startswith('match')]:
            matches[match] = evaldf[match].value_counts(normalize=True)[True]
        
        scores[(name,setname)] = matches
    return pd.DataFrame(scores).T

def get_eval_paths():
    home = project_dir.joinpath('evaluation')
    evaluations_list = []
    for dirpath, dirnames, filenames in os.walk(home):
        for name in filenames:
            if name.endswith('.tsv'):
                evaluations_list.append(f'{dirpath}/{name}')
    return sorted(evaluations_list,reverse=True)

@print_durations()
def main():

    ##############
    ##############
    ### argparse commands

    # top-level parser
    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
        pass
    
    class CustomParser(argparse.ArgumentParser):
        def __init__(self,**kwargs):
            super().__init__(kwargs)
            self.formatter_class = CustomFormatter
        
    parser = CustomParser(prog='LOC_Transcribe',add_help=True)
    
    subparsers = parser.add_subparsers(help='Options',dest='command')

    ### extract
    parser_extract = subparsers.add_parser('extract',add_help=True,
                            help='Extract parallel lines from marcxml files (linked by marcfield 880 subfield 6)')
    parser_extract.add_argument('input',help='input directory containing marcxml collections',
                                default=f'data/arabic_records/',nargs='?')
    parser_extract.add_argument('output',help='output tsv',
                                default=f'data/extracted_lines/extracted_lines.tsv',nargs='?')
    ##############
    ### preprocess
    parser_clean = subparsers.add_parser('preprocess',add_help=True,help='Clean and optionally split extracted lines')
    parser_clean.add_argument('input',nargs='?',help='input tsv containing extracted parallel lines',
                            default=f'data/extracted_lines/extracted_lines.tsv')
    parser_clean.add_argument('output',nargs='?',help='output directory to store cleaned lines',
                            default=f'data/processed/',)
    parser_clean.add_argument('-s','--split',action='store_true',help='split data into dev train and test')
    
    ##############                        
    ### train
    parser_train = subparsers.add_parser('train',add_help=True,help='train mle or seq2seq model')
    
    train_subparsers = parser_train.add_subparsers(help='Model',dest='train',metavar='model')
    # mle
    parser_train_mle = train_subparsers.add_parser('mle',help='trains mle model')
    parser_train_mle.add_argument('input',nargs='?',help='input tsv containing clean parallel lines with columns "ar" and "rom" for source and gold',
                            default=f'data/processed/train.tsv')
    parser_train_mle.add_argument('output',nargs='?',help='output tsv to store mle model with frequencies',
                            default=f'models/mle/',)
    parser_train_mle.add_argument('-s','--size',nargs='+',default=[1,0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625],type=float,help='specify proportion of training to use, e.g: 0.125')
    # seq2seq
    parser_train_seq2seq = train_subparsers.add_parser('seq2seq',help='trains seq2seq model')
    parser_train_seq2seq.add_argument('input',nargs='?',help='directory containing train dev test',
                            default=f'data/processed')
    parser_train_seq2seq.add_argument('-s','--size',nargs='+',default=[1.0,0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625],type=float,help='specify proportion of training to use, e.g: 0.125')
    parser_train_seq2seq.add_argument('--prep',action='store_true',help='prepare data for seq2seq training with selected train sizes')
    parser_train_seq2seq.add_argument('--train_seq2seq',action='store_true',help='train seq2seq with selected train sizes')
    
    ##############
    ### predict
    parser_predict = subparsers.add_parser('predict',add_help=True,help='Predict romanization',)
    # init predict_subparser
    predict_subparsers = parser_predict.add_subparsers(help='Prediction Model',dest='model',metavar='model')
    # translit_simple
    parser_predict_translit_simple = predict_subparsers.add_parser('simple', add_help=True,help='Apply Simple Rules')
    parser_predict_translit_simple.add_argument('input',default='dev',nargs='?',help='dev, test, or path to tsv containing a column "ar" for source lines')
    parser_predict_translit_simple.add_argument('output',default=f'predictions_out/',nargs='?',help='output directory to store prediction lines')
    # translit_morph
    parser_predict_translit_morph = predict_subparsers.add_parser('morph', add_help=True,help='Apply Morph Rules using MADAMIRA')
    parser_predict_translit_morph.add_argument('input',default='dev',nargs='?',help='input tsv containing "ar" source lines')
    parser_predict_translit_morph.add_argument('output',default=f'predictions_out/',nargs='?',help='output directory to store prediction lines')
    # mle
    parser_predict_mle = predict_subparsers.add_parser('mle', add_help=True,help='Translit using MLE model')
    parser_predict_mle.add_argument('input',default='dev',nargs='?',help='input tsv containing "ar" source lines')
    parser_predict_mle.add_argument('output',default=f'predictions_out/',nargs='?',help='output directory to store prediction lines')
    parser_predict_mle.add_argument('-m','--mle_model', default='models/mle/size1.0.tsv', help='path to mle_model tsv')
    parser_predict_mle.add_argument('-b','--backoff',required=True, 
                        help= """backoff options:\n\
                        OOV                  no backoff - returns OOV\n\
                        translit_simple      Simple transliteration\n\
                        <prediction_file>    provide prediction file from another model as backoff\
                        """)
    # seq2seq
    parser_predict_seq2seq = predict_subparsers.add_parser('seq2seq', add_help=True,help='Predict test set (dev is done with training)')
    parser_predict_seq2seq.add_argument('-t','--predict_test',action="store_true",help='Predict blind test')
    parser_predict_seq2seq.add_argument('-m','--model_size',default=[1.0],nargs='+',type=float,help='Specify model size(s) to apply')
    parser_predict_seq2seq.add_argument('-b','--align_backoff',nargs=2,help='prediction and backoff prediction')
    parser_predict_seq2seq.add_argument('-d','--dont_backoff',action='store_true',help='align without backoff')
    parser_predict_seq2seq.add_argument('-o','--output',default='predictions_out/aligned_seq2seq',help='output directory')
    

    # evaluate
    parser_evaluate = subparsers.add_parser('evaluate', add_help=True,help='Evaluate prediction output.')
    parser_evaluate.add_argument('prediction',help='File containing predicted sentences')
    parser_evaluate.add_argument('gold_tsv',default='data/processed/dev.tsv',nargs='?',help='input tsv containing source, gold, sentID and tag info')
    parser_evaluate.add_argument('output',default=f'evaluation',nargs='?',help='output directory to store prediction lines')

    # score
    parser_score = subparsers.add_parser('score', add_help=True,help='Pretty print evaluation scores.')
    parser_score.add_argument('evaluations',nargs='+',default=['all'],help='Specify which evaluations to score, or all')



    args = parser.parse_args()
    
    ##############
    ##############
    ### system calls

    # extract
    if args.command == 'extract':    
        os.system(f'python3 {project_dir}/src/data/extract_parallel_data.py {args.input} {args.output}')
        
    # preprocess
    if args.command == 'preprocess':
        Path(f'{project_dir}/{args.output}').mkdir(parents=True,exist_ok=True)
        if args.split:    
            os.system(f'python3 {project_dir}/src/data/make_dataset.py {args.input} -o {args.output}')
        else:
            os.system(f'python3 {project_dir}/src/data/make_dataset.py {args.input} -o {args.output} -ds')

    # train
    if args.command == 'train':   
        if args.input in {'dev','test','train'}:
            args.input = f'{project_dir}/data/processed/{args.input}.tsv'
        # mle
        if args.train == 'mle':
            os.system(f'python3 {project_dir}/src/train/mle_train.py {args.input} {args.output} -s {" ".join(map(str,args.size))}')
        # seq2seq
        if args.train == 'seq2seq':
            if args.prep:
                os.system(f'python3 src/data/make_seq2seq_dataset.py {project_dir}/{args.input} seq2seq/splits_ldc -s {" ".join(map(str,args.size))}')
                os.system(f'python3 src/train/seq2seq_create_jobs.py -s {" ".join(map(str,args.size))}')
            if args.train_seq2seq:
                for size in args.size:
                    # Path(f'seq2seq/log/size_{size}').mkdir(parents=True, exist_ok=True) 
                    os.system(f'sbatch src/train/seq2seq_scripts/train_size{size}.sh')
            if args.train_seq2seq==args.prep==False:
                raise Exception('must turn on either prep or train flags in seq2seq train mode')
                
    # predict
    if args.command == 'predict':
        
        # translit_rules
        if args.model in {'simple','morph'}:
            if args.input in {'dev','test','train'}:
                args.input = f'{project_dir}/data/processed/{args.input}.tsv'
            setname = args.input.split('/')[-1].replace('.tsv','')
            name = args.model.split('_')[-1]
            outpath = f'{args.output}/{args.model}/{setname}' 
            Path(f'{project_dir}/{outpath}').mkdir(parents=True, exist_ok=True) 
            os.system(f'python3 {project_dir}/src/predict/translit_rules.py {args.input} {outpath}/{name}.out -i tsv -m {args.model} -l')
        # mle
        if args.model == 'mle':
            if args.input in {'dev','test','train'}:
                args.input = f'{project_dir}/data/processed/{args.input}.tsv'
            setname = args.input.split('/')[-1].replace('.tsv','')
            name = args.model.split('_')[-1]
            if '/' in args.backoff:
                backoff_name = args.backoff.split("/")[-1].replace(".out","")
            else:
                backoff_name = args.backoff

            outpath = f'{args.output}/{args.model}_{backoff_name}/{setname}' 
            Path(f'{project_dir}/{outpath}').mkdir(parents=True, exist_ok=True) 
            
            mle_model_name = args.mle_model.split('/')[-1].replace(".tsv","")
            os.system(f'python3 {project_dir}/src/predict/mle_predict.py {args.input} {outpath}/mle_{backoff_name}_{mle_model_name}.out -i tsv ar -m {args.mle_model} -b {args.backoff}')
        # seq2seq
        if args.model == 'seq2seq':
            if args.predict_test:
                for size in args.model_size:
                    print(f'predicting test set with training size: {size}')
                    os.system(f'sbatch src/predict/seq2seq_scripts/test/predict_size{size}.sh')
            elif args.align_backoff:
                prediction = args.align_backoff[0].split('/')[-1].replace('.out','')
                setname = args.align_backoff[0].split('/')[-2]
                align_prediction = args.align_backoff[1].split('/')[-1].replace('.out','')

                outpath = f'{args.output}/{setname}'
                Path(outpath).mkdir(parents=True, exist_ok=True)

                if args.dont_backoff:
                    os.system(f'python3 src/predict/ensembles.py {args.align_backoff[0]} {args.align_backoff[1]} {outpath}/{prediction}X{align_prediction}-nullbckf.out -d')
                else:
                    os.system(f'python3 src/predict/ensembles.py {args.align_backoff[0]} {args.align_backoff[1]} {outpath}/{prediction}X{align_prediction}.out ')
       
            
    # evaluate
    if args.command == 'evaluate':
        setname = args.prediction.replace('.out','').split('/')[-2]
        name = args.prediction.replace('.out','').split('/')[-1]
        outpath = f'{args.output}/{setname}'
        Path(f'{project_dir}/{outpath}').mkdir(parents=True, exist_ok=True) 
        os.system(f'python3 {project_dir}/src/evaluation/evaluate.py {args.prediction} {project_dir}/{args.gold_tsv} -o {outpath}/{name}.tsv')

    if args.command == 'score':
        if args.evaluations[0] == 'all':
            eval_paths = get_eval_paths()
            print(score_evals(eval_paths).to_string())
        else:
            print(score_evals(args.evaluations).to_string())

if __name__== "__main__":
    main()