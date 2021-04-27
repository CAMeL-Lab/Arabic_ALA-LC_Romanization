import os
from pathlib import Path
import argparse

project_dir = Path(__file__).resolve().parents[2]

def create_predict_script(size,split='test'):
    script=f"""#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH -p condo
#SBATCH --mail-type=ALL
#SBATCH --mail-user=fae211
#SBATCH --mem=30000
#SBATCH --time=48:00:00
#SBATCH -o reports/seqpredict_size{size}.%J.out
#SBATCH -e reports/seqpredict_size{size}.%J.err

module purge
module load all
module load miniconda
module load anaconda/2-4.1.1
module load cuda/8.0
module load gcc/4.9.3
source ~/.bashrc
source activate newseqenv


python3 -m ai.tests.seq2seq --train_input=temp_size{size}/line2line_training_train_input --train_output=temp_size{size}/line2line_training_train_output --dev_input=temp_size{size}/line2line_training_dev_input --dev_output=temp_size{size}/line2line_training_dev_output --model_output_dir=output/models/line2line_model_size{size} --predict_input_file=splits_ldc/{split}/{split}-ar-recomposed-lines --output_path=../predictions_out/seq2seq/{split}/seq2seq_size{size}.out"""

    return script


def create_train_script(size):
    script =f"""#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH -p condo
#SBATCH --mail-type=ALL
#SBATCH --mail-user=fae211
#SBATCH --mem=30000
#SBATCH --time=48:00:00
#SBATCH -o reports/seqtrain_size{size}.%J.out
#SBATCH -e reports/seqtrain_size{size}.%J.err

module purge
module load all
module load miniconda
module load anaconda/2-4.1.1
module load cuda/8.0
module load gcc/4.9.3
source ~/.bashrc
source activate newseqenv

cd seq2seq

python3 transliterate.py --train_size_ratio={size} --model_name=line2line --model_python_script=ai/tests/seq2seq.py --alignment=line --model_output_path=output/models/line2line_model_size{size} --predict_input_file=splits_ldc/dev/dev-ar-recomposed-lines --predict_output_file=../predictions_out/seq2seq/dev/seq2seq_size{size}.out --predict_output_sentence_aligned_gold=splits_ldc/dev/dev-rom-clean-lines --evaluation_results_file=output/evaluations/line2line_dev_evaluation_results.txt --preprocess=False --input_writing_system=arabic --output_language=latin --train_source_file=splits_ldc/train/train-ar-recomposed-lines_size{size} --train_target_file=splits_ldc/train/train-rom-clean-lines_size{size} --dev_source_file=splits_ldc/dev/dev-ar-recomposed-lines --dev_target_file=splits_ldc/dev/dev-rom-clean-lines --test_source_file=splits_ldc/test/test-ar-recomposed-lines --prediction_loaded_model_training_train_input=temp_size{size}/line2line_training_train_input --prediction_loaded_model_training_train_output=temp_size{size}/line2line_training_train_output --prediction_loaded_model_training_dev_input=temp_size{size}/line2line_training_dev_input --prediction_loaded_model_training_dev_output=temp_size{size}/line2line_training_dev_output --include_fasttext=False --evaluate_accuracy=False --evaluate_bleu=False --predict=True
"""

    return script


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--sizes',nargs='+',default=[1],type=float,help='Specify train sizes to create scripts for')
    parser.add_argument('-o','--output',default='predictions_out/seq2seq',help='Output directory')
    args = parser.parse_args()
    
    Path(f'{args.output}/dev').mkdir(parents=True, exist_ok=True)
    Path(f'{args.output}/test').mkdir(parents=True, exist_ok=True)
    
    for size in args.sizes:
        train_script_path = f'{project_dir}/src/train/seq2seq_scripts'
        train_script = create_train_script(size=size) 
        Path(train_script_path).mkdir(parents=True, exist_ok=True)
        with open(f'{train_script_path}/train_size{size}.sh','w') as o:
            o.writelines(train_script)

        # predict script is for test prediction.  dev prediction is done with training
        predict_script_path = f'{project_dir}/src/predict/seq2seq_scripts/test'
        predict_script = create_predict_script(size=size,split='test') 
        Path(predict_script_path).mkdir(parents=True, exist_ok=True)
        with open(f'{predict_script_path}/predict_size{size}.sh','w') as o:
            o.writelines(predict_script)            


if __name__=="__main__":
    main()