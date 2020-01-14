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

#=========================================== SETTINGS ===========================================
if len(sys.argv) == 2:
    HOME_ROOT = str(sys.argv[1])
else:
    #HOME_ROOT = '/Users/ohamelijnck/'
    HOME_ROOT = '~/'
    # HOME_ROOT = '/Users/pohara/'

#Every cluster has its own maximum allocations. 
max_settings = {
    'tinis': {
        'time': '48:00:00',
        'memory': 4571,
        'ssh_key': HOME_ROOT+'.ssh/ollie_rsa',
        'user': 'csrcqm',
        'ip': 'tinis.csc.warwick.ac.uk',
        'slurm_template': 'cluster_templates/batch_script_tinis_template.sh'
    },
    'orac': {
        'time': '48:00:00',
        'memory': 4571,
        'ssh_key': HOME_ROOT+'.ssh/ollie_rsa',
        'user': 'csrcqm',
        'ip': 'orac.csc.warwick.ac.uk',
        'slurm_template': 'cluster_templates/batch_script_template.sh'
    },
    'pearl': {
        'time': '48:00:00',
        'memory': 32768,
        'cpus': 28,
        'ssh_key': HOME_ROOT+'.ssh/patrick-pearl',
        'user': 'pearl023',
        'ip': 'ui.pearl.scd.stfc.ac.uk',
        'slurm_template': 'cluster_templates/batch_script_pearl_template.sh'
    },
}

#TODO: define default configs for the clusters
#Config to run
if False:
    cluster_config = {
        'cluster': 'orac',
        'cluster_tmp_folder': 'cluster',
        'slurm_file': 'run.sh',
        'base_name': 'test', #folder to store models/results on cluster
        'models_root': 'models',
        'nodes': 1,
        'cpus': 1,
        'time': '01:00:00', 
        'memory': 4571,
        #array of files/folders to send to cluster
        'libraries': [
            '../containers/cleanair',
        ] 
    }
else:
    cluster_config = {
        'cluster': 'pearl',
        'cluster_tmp_folder': 'cluster',
        'slurm_file': 'run.sh',
        'base_name': 'test', #folder to store models/results on cluster
        'models_root': 'models',
        'nodes': 1,
        'cpus': 1,
        'time': '01:00:00', 
        'memory': 4571,
        #array of files/folders to send to cluster
        'libraries': [
            '../containers/cleanair/',
        ] 
    }

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

    cluster = AVAILABLE_CLUSTERS[exp.cluster]()
    cluster.setup(home_dir, {})

    #each experiment is defined by a batch of model parameters and a set of validation folds

    param_configs = exp.model_params
    #hack to get working with future experiment file
    param_configs = {'svgp': param_configs}

    data_configs = exp.data_config

    #ensure folder for storing cluster files exists
    subprocess.call(['mkdir', '-p', cluster_config['cluster_tmp_folder']])

    cluster.create_batch_scripts(param_configs, data_configs)
    exit()

    #=========================================== SEND FILES TO CLUSTER ===========================================

    #cmd = subprocess.call('cluster_templates/send_to_cluster.sh')

    cluster_settings = max_settings[cluster_config['cluster']]

    call_array = [
        "sudo", 
        "sh", "cluster_templates/send_to_cluster.sh",
        "--user", cluster_settings['user'],
        "--ip", cluster_settings['ip'],
        "--ssh_key", cluster_settings['ssh_key'],
        "--basename", cluster_config['base_name'],
        "--cluster_folder",cluster_config['cluster_tmp_folder'],
        "--slurm_file",cluster_config['slurm_file'],
    ]
    for lib in cluster_config['libraries']:
        call_array.append("--lib")
        call_array.append(lib)

    subprocess.call(call_array)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Model on Cluster")
    parser.add_argument('-d', '--dir_home', type=str, help='Home Directory')
    args = parser.parse_args()


    exp = experiment.SVGPExperiment('svgp', 'pearl')
    main(home_dir = args.dir_home, exp = exp)

