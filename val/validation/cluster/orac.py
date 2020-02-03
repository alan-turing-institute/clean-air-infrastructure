"""
    Run experiments on Orac
"""

from . import Cluster

class Orac(Cluster):
    """
        Orac Cluster
    """

    def __init__(self, **kwargs):
        Cluster.__init__(self, **kwargs)


    @property
    def slurm_template_fp(self):
        """
            Location of the slurm batch script template
        """

        return 'validation/cluster/batch_files/batch_script_template.sh'

    @property
    def default_config(self):
        """
            Default cluster configs for Pearl
        """

        defaults = {
            'cpus': 12,
            'gpus': 1,
            'nodes': 1,
            'time': '12:00:00',
            'memory': 4571,
            'ip': 'orac.csc.warwick.ac.uk',
            'user': 'csrcqm',
            'ssh_key': '.ssh/ollie_cluster_rsa',
            'libs': [],
        }
        
        return defaults
