#!/bin/bash
#
#SBATCH --job-name=svgp_0_0
#SBATCH --output=svgp_0_0logs.txt
#
#SBATCH --nodes=1
#SBATCH --ntasks=12
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --time=15:00:00
#SBATCH --mem-per-cpu=4571

module purge
module load Python/3.7.4-GCCcore-8.3.0

cd satellite/models/ && python m_svgp.py  0 0
