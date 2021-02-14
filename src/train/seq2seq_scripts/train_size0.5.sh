#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH -p condo
#SBATCH --mail-type=ALL
#SBATCH --mail-user=fae211
#SBATCH --mem=30000
#SBATCH --time=48:00:00
#SBATCH -o reports/seqtrain_size0.5.%J.out
#SBATCH -e reports/seqtrain_size0.5.%J.err

module purge
module load all
module load miniconda
module load anaconda/2-4.1.1
module load cuda/8.0
module load gcc/4.9.3
source ~/.bashrc
source activate newseqenv

cd seq2seq

python3 transliterate.py --train_size_ratio=0.5 --model_name=line2line --model_python_script=ai/tests/seq2seq.py --alignment=line --model_output_path=output/models/line2line_model_size0.5 --predict_input_file=splits_ldc/dev/dev-ar-recomposed-lines --predict_output_file=../predictions_out/seq2seq/dev/seq2seq_size0.5.out --predict_output_sentence_aligned_gold=splits_ldc/dev/dev-rom-clean-lines --evaluation_results_file=output/evaluations/line2line_dev_evaluation_results.txt --preprocess=False --input_writing_system=arabic --output_language=latin --train_source_file=splits_ldc/train/train-ar-recomposed-lines_size0.5 --train_target_file=splits_ldc/train/train-rom-clean-lines_size0.5 --dev_source_file=splits_ldc/dev/dev-ar-recomposed-lines --dev_target_file=splits_ldc/dev/dev-rom-clean-lines --test_source_file=splits_ldc/test/test-ar-recomposed-lines --prediction_loaded_model_training_train_input=temp_size0.5/line2line_training_train_input --prediction_loaded_model_training_train_output=temp_size0.5/line2line_training_train_output --prediction_loaded_model_training_dev_input=temp_size0.5/line2line_training_dev_input --prediction_loaded_model_training_dev_output=temp_size0.5/line2line_training_dev_output --include_fasttext=False --evaluate_accuracy=False --evaluate_bleu=False --predict=True
