"""
    Run experiments locally on Laptop
"""

import os
from . import Cluster

import subprocess

class Laptop(Cluster):
    def setup(self):
        """
            not needed on laptop
        """
        pass

    @property
    def slurm_template_fp(self):
        """
            N/A on laptop
        """

        return None

    @property
    def default_config(self):
        """
            N/A on laptop
        """
    
        return None

    def run(self):
        """
            Run all experiments serially and locally
        """

        current_directory = os.getcwd()
        for config in self.experiment_configs:
            model = config['filename']
            file_name = 'm_{model}'.format(model=model)
            file_inputs = self.input_format_fn(config)
            file_fp = self.experiment_fp+self.experiment_name+'/models'
            file_name=file_name+'.py'

            #construct bash script to send files
            call_array = [
                "cd ",  current_directory + '/' + file_fp, '&&',
                "python", file_name, file_inputs
            ]
            script = ' '.join(call_array)

            os.system(script)



