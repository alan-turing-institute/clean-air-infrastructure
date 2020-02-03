"""
    Run experiments on Pearl
"""

from . import Cluster

class Pearl(Cluster):
    """
        Pearl Cluster
    """
    def __init__(self, **kwargs):
        Cluster.__init__(self, **kwargs)


    @property
    def slurm_template_fp(self):
        """
            Location of the slurm batch script template
        """

        return self.root+'batch_files/batch_script_pearl_template.sh'

    @property
    def default_config(self):
        """
            Default cluster configs for Pearl
        """
        defaults = {
            'cpus': 1,
            'gpus': 1,
            'nodes': 1,
            'time': '05:00:00',
            'memory': 4571,
            'ip': 'ui.pearl.scd.stfc.ac.uk',
            'user': 'pearl023',
            'ssh_key': '.ssh/patrick-pearl',
            'libs': ['libs/'],
        }
        
        return defaults



    def create_batch_from_template(self, file_name, file_inputs, job_name, log_name):
        """
            Creates the batch/slurm script that will run the experiments on the cluster
        """

        template = self.template
        print(self.config)
        template = template.replace('<MODELS_DIR>', self.experiment_name+'/models/')
        template = template.replace('<LOGS_DIR>', self.experiment_name+'/cluster/logs')
        template = template.replace('<NODES>', str(self.config['nodes']))
        template = template.replace('<CPUS>', str(self.config['cpus']))
        template = template.replace('<MEMORY>', str(self.config['memory']))
        template = template.replace('<TIME>', str(self.config['time']))
        template = template.replace('<FILE_NAMES>', file_name)
        template = template.replace('<FILE_INPUTS>', file_inputs)
        template = template.replace('<JOB_NAME>', job_name)
        template = template.replace('<LOG_NAME>', log_name)

        return template
