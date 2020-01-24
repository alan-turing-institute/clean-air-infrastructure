#!/bin/bash
#SBATCH --job-name=<LOG_NAME>
#SBATCH --nodes=<NODES>
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=<CPUS>
#SBATCH --mem-per-cpu=<MEMORY>
#SBATCH --time=<TIME>

module purge
module load GCCcore/8.2.0 GCC/8.2.0-2.31.1  OpenMPI/3.1.3  scikit-learn/0.20.3 SciPy-bundle/2019.03 matplotlib/3.0.3-Python-3.7.2 Python/3.7.2
module load parallel GCC

#ASSUME MODELS_DIR IS AT proj/models
#parallel --joblog  "/home/dcs/csrcqm/<LOGS_DIR>/joblog" --link --delay 0.2 -j <NODES>  "cd <MODELS_DIR> && python3 {1}.py {2} &> /home/dcs/csrcqm/<LOGS_DIR>/{1}_{2}.log" ::: <FILE_NAMES> ::: <FILE_INPUTS>
cd <MODELS_DIR> && python3 <FILE_NAMES>.py <FILE_INPUTS> &> /home/dcs/csrcqm/<LOGS_DIR>/<LOG_NAME>.log 

