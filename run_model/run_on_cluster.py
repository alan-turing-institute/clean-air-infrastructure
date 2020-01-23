import os
import numpy
import sys
sys.path.append('../containers/') #allow cleanair to be imported
import importlib
import subprocess
import argparse

sys.path.append('../validation')
import experiment

from cluster_templates import Cluster, Pearl, Orac

#=========================================== MAIN ===========================================
AVAILABLE_CLUSTERS = {
    'pearl': Pearl,
    'orac': Orac
}
def main(home_dir="", exp=None):
    if exp is None:
        print('Experiment needed')
        return

    if home_dir is None:
        print("using default home directory")

    if exp.cluster not in AVAILABLE_CLUSTERS:
        print(exp.cluster, "not available")
        return

    experiments_folder = 'experiments'
    experiment_to_run = exp.name
    libraries = ['../containers/cleanair']
    cluster = AVAILABLE_CLUSTERS[exp.cluster]()
    cluster.setup(exp.name, home_dir, {})

    #each experiment is defined by a batch of model parameters and a set of validation folds

    param_configs = exp.model_params
    data_configs = exp.data_config

    #ensure folder for storing cluster files exists
    subprocess.call(['mkdir', '-p', cluster.tmp_folder])

    f_names = cluster.create_batch_scripts(param_configs, data_configs)

    #=========================================== SEND FILES TO CLUSTER ===========================================

    #cmd = subprocess.call('cluster_templates/send_to_cluster.sh')

    call_array = [
        "sudo", 
        "sh", "cluster_templates/send_to_cluster.sh",
        "--user", cluster.user,
        "--ip", cluster.ip,
        "--ssh_key", cluster.home_dir +  cluster.ssh_key,
        "--basename", cluster.base_name,
        "--cluster_folder", cluster.tmp_folder,
        "--experiments_folder", experiments_folder,
    ]

    for f_name in f_names:
        call_array.append("--slurm_file")
        call_array.append(f_name)

    for lib in libraries:
        call_array.append("--lib")
        call_array.append(lib)

    subprocess.call(call_array)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Model on Cluster")
    parser.add_argument('-d', '--dir_home', type=str, help='Home Directory')
    parser.add_argument('-e', '--experiment', type=str, help='Experiment file name')
    args = parser.parse_args()

    exp = experiment.load_experiment(args.experiment, root='../validation/').get_experiment()

    #exp.setup(base_dir='experiments/')
    main(home_dir=args.dir_home, exp=exp)
