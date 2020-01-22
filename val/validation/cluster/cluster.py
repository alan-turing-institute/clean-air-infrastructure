"""
    Organise the running of experiments
"""

from abc import ABC, abstractmethod
import subprocess
import pathlib

class Cluster(ABC):
    """
        Cluster base class
    """
    def __init__(self, cluster_config=None, experiment_configs=None,
                 experiment_fp='', cluster_tmp_fp='', home_directory_fp=''):
        """
            experiment_fp: location of the experiment to run
            cluster_tmp_fp: location of tmp folder to store temporal files created in this class
            home_directory_fp: folder path of directory that holds `.ssh` folder
            experiment_configs: an array of dictionaries
        """

        self.config = cluster_config or {}
        self.experiment_configs = experiment_configs or {}
        self.experiment_fp = experiment_fp
        self.cluster_tmp_fp = cluster_tmp_fp
        self.home_directory_fp = home_directory_fp

        self.default_config = {}
        self.max_config = {}

        #store the loaded slurm template here
        self.template = None

    @property
    @abstractmethod
    def slurm_template_fp(self):
        """
            Location of the slurm batch script template
        """

    def setup(self):
        """
            setup cluster object and ensure settings are correct
        """
        self.ensure_config_defaults()
        self.check_config_max_settings()
        self.ensure_folder_structure()

    @abstractmethod
    def get_default_params(self):
        """
            Get default cluster parameters
        """

    def check_config_max_settings(self):
        """
            Make sure current configurations do not exceed the max
        """
        for k in self.config:
            if k in self.max_config:
                if self.config[k] > self.max_config[k]:
                    raise ValueError(
                        "Configuration exceeds max: ",
                        k,
                        self.config[k],
                        self.max_config[k]
                    )

    def ensure_config_defaults(self):
        """
            Fill in missing parameters in config with the default parameters
        """
        for k in self.default_config:
            if k not in self.config:
                self.config[k] = self.default_config[k]

    def load_template_file(self):
        """
            Load the slurm batch template file.
        """
        template = None
        with open(self.slurm_template_fp, 'r') as file_name:
            template = file_name.read()

        self.template = template

    def ensure_folder_structure(self):
        """
            Make sure the folder structure is correct. Assume experiment has already been handled:
                - make sure cluster tmp folder exists
        """
        pathlib.Path(self.cluster_tmp_fp).mkdir(exist_ok=True)

    def get_key_order(self, config_dict):
        """
            To store model results we need a way to sort the config parameters. Default is
                to sort the keys in alphabetical order.
        """
        keys = config_dict.keys().sort()
        return keys

    def create_batch_from_template(self, file_name, file_inputs, job_name, log_name):
        """
            Creates the batch/slurm script that will run the experiments on the cluster
        """

        template = self.template.copy()

        template = template.replace('<MODELS_DIR>', self.base_name+'/models/')
        template = template.replace('<LOGS_DIR>', self.base_name+'/cluster/logs')
        template = template.replace('<NODES>', str(self.config['nodes']))
        template = template.replace('<CPUS>', str(self.config['cpus']))
        template = template.replace('<MEMORY>', str(self.config['memory']))
        template = template.replace('<TIME>', str(self.config['time']))
        template = template.replace('<FILE_NAMES>', file_name)
        template = template.replace('<FILE_INPUTS>', file_inputs)

        return template

    def get_batches(self):
        """
            Each experiment run will have its own batch script, one for each configuration
                inside self.experiment_configs. Experiment configs is an array of dictionaries
                where the keys of the dictionary act as the model parameters allowing the model
                to index the individual experiment runs.
        """
        batches = []
        for config in self.experiment_configs:
            model = config['filename']

            #every model is prefixed with m_
            file_name = 'm_{model}'.format(model=model)

            #get the ordered keys and values
            ordered_config_keys = self.get_order(dict_without_key(config, 'filename'))
            inputs = [config[key] for key in ordered_config_keys]

            #convert values to file input format
            model_inputs = ['{file_input}'.format(file_input=_input) for _input in inputs]

            file_inputs = model_inputs.join(' ')
            job_name = model+'_'+model_inputs.join('_')
            results_name = model+'_'+model_inputs.join('_')+'results.txt'
            logs_name = model+'_'+model_inputs.join('_')+'logs.txt'
            batch_name = 'run_'+model+'_'+model_inputs.join('_')+'.sh'

            #get batch script
            batch_script = self.create_batch_from_template(
                file_name,
                file_inputs,
                job_name,
                logs_name
            )

            batch_name = self.cluster_tmp_fp+'/'+batch_name

            batches.append([batch_name, t])

        return batches

    def create_batch_scripts(self):
        """
            Run experiment.
        """

    def run(self):
        """
            Run experiment.
        """

def dict_without_key(dict_obj, key):
    """
        Return a dictionary with the key removed.
    """
    new_dict_obj = dict_obj.copy()
    new_dict_obj.pop(key)
    return new_dict_obj
