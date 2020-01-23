import subprocess
import sys
import argparse

sys.path.append('../validation')
import experiment

from cluster_templates import Cluster, Pearl, Orac

from run_on_cluster import AVAILABLE_CLUSTERS

def main(home_dir=None, exp=None):
    experiments_folder = 'experiments'
    experiment_to_run = exp.name
    cluster = AVAILABLE_CLUSTERS[exp.cluster]()
    cluster.setup(exp.name, home_dir, {})

    call_array = [
        "sudo",
        "sh", "cluster_templates/get_results.sh",
        "--user", cluster.user,
        "--ip", cluster.ip,
        "--ssh_key", cluster.home_dir + cluster.ssh_key,
        "--basename", experiment_to_run,
        "--cluster_folder", cluster.tmp_folder,
    ]

    subprocess.call(call_array)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Model on Cluster")
    parser.add_argument('-d', '--dir_home', type=str, help='Home Directory')
    parser.add_argument('-e', '--experiment', type=str, help='Experiment file name')
    args = parser.parse_args()

    exp = experiment.load_experiment(args.experiment, root='../validation/').get_experiment()

    main(home_dir=args.dir_home, exp=exp)
