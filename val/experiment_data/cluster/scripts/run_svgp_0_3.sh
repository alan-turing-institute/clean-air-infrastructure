#!/bin/bash
#SBATCH --job-name=svgp_0_3logs.txt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=4571
#SBATCH --time=05:00:00

module purge
module load GCCcore/8.2.0 GCC/8.2.0-2.31.1  OpenMPI/3.1.3  scikit-learn/0.20.3 SciPy-bundle/2019.03 matplotlib/3.0.3-Python-3.7.2 Python/3.7.2
module load parallel GCC

#ASSUME MODELS_DIR IS AT proj/models
#parallel --joblog  "/home/dcs/csrcqm/basic/logs/joblog" --link --delay 0.2 -j 1  "cd basic/models/ && python3 {1}.py {2} &> /home/dcs/csrcqm/basic/logs/{1}_{2}.log" ::: m_svgp :::  3 0
cd basic/models/ && python3 m_svgp.py  3 0 &> /home/dcs/csrcqm/basic/logs/svgp_0_3logs.txt.log 

