import subprocess
import os
import argparse
import sys

sys.path.append('../validation')
import experiment

from cluster_templates import Cluster, Pearl, Orac
from run_on_cluster import AVAILABLE_CLUSTERS

def main(home_dir=None, exp=None):
    experiments_folder = 'experiments'
    experiment_to_run = exp.name
    cluster = AVAILABLE_CLUSTERS[exp.cluster]()
    cluster.setup(exp.name, home_dir, {})

    script_str = """
    ssh  -i "{SSH_KEY}" "{USER}@{IP}" -o StrictHostKeyChecking=no 'bash -s' << HERE
squeue -u {USER}
HERE
    """.format(
        SSH_KEY=cluster.home_dir + cluster.ssh_key,
        USER=cluster.user,
        IP=cluster.ip,
    )

    cmd = os.system(script_str)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Check Cluster")
    parser.add_argument('-d', '--dir_home', type=str, help='Home Directory')
    args = parser.parse_args()

    exp = experiment.SVGPExperiment('svgp_test', 'pearl')
    main(home_dir=args.dir_home, exp=exp)

