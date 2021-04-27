#!/bin/bash
# condo for camel lab computing
#SBATCH -p condo
# Set number of tasks to run
#SBATCH --ntasks=1
# Set number of cores per task (default is 1)
#SBATCH --cpus-per-task=1
# Walltime format hh:mm:ss
#SBATCH --time=24:00:00
# Output and error files
#SBATCH -o reports/collect_arabic_job/%J.log
#SBATCH -e reports/collect_arabic_job/%J.log
# commented mail
# SBATCH --mail-type=begin
# SBATCH --mail-type=end
#SBATCH --mail-user=fae211@nyu.edu
#SBATCH --mem=10GB
#SBATCH -J extract
# **** Put all #SBATCH directives above this line! ****
# **** Otherwise they will not be in effective! ****
#
# **** Actual commands start here ****
# Load modules here (safety measure)
# You may need to load gcc here .. This is application specific
# module load gcc

#Activating conda environment and loading other modules
module load miniconda
source ~/.bashrc
conda activate LOC_transcribe


python3 src/data/collect_job.py