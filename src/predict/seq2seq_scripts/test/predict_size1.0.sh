#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH -p condo
#SBATCH --mail-type=ALL
#SBATCH --mail-user=fae211
#SBATCH --mem=30000
#SBATCH --time=48:00:00
#SBATCH -o reports/seqpredict_size1.0.%J.out
#SBATCH -e reports/seqpredict_size1.0.%J.err

module purge
module load all
module load miniconda
module load anaconda/2-4.1.1
module load cuda/8.0
module load gcc/4.9.3
source ~/.bashrc
source activate newseqenv


python3 -m ai.tests.seq2seq --train_input=temp_size1.0/line2line_training_train_input --train_output=temp_size1.0/line2line_training_train_output --dev_input=temp_size1.0/line2line_training_dev_input --dev_output=temp_size1.0/line2line_training_dev_output --model_output_dir=output/models/line2line_model_size1.0 --predict_input_file=splits_ldc/test/test-ar-recomposed-lines --output_path=../predictions_out/seq2seq/test/seq2seq_size1.0.out