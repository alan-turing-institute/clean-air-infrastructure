#!/bin/bash

#SBATCH -p pearl #(the queue to run on)
#SBATCH --job-name=traffic_analysis
#SBATCH --output=<LOG_NAME>
#SBATCH --nodes=1
#SBATCH --ntasks=12
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --time=00:02:00
#SBATCH --mem-per-cpu=4

# note the number of weeks is passed as the first parameter
singularity exec ~/containers/traffic/lockdown_coverage.sif sh ~/batch_scripts/inner_coverage.sh $1