#!/bin/bash
#
#SBATCH --job-name=<JOB_NAME>
#SBATCH --output=<LOG_NAME>
#
#SBATCH --nodes=<NODES>
#SBATCH --ntasks=<CPUS>
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --time=<TIME>
#SBATCH --mem-per-cpu=<MEMORY>

module purge
module load Python/3.7.4-GCCcore-8.3.0

cd <MODELS_DIR> && python <FILE_NAMES>.py <FILE_INPUTS>
