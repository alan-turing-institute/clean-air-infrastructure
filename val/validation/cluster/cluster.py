"""
    Organise the running of experiments
"""

from abc import ABC, abstractmethod
import subprocess
import pathlib

from .. import util
import os

class Cluster(ABC):
    """
        Cluster base class
    """
    def __init__(self, experiment_name='', cluster_config=None, experiment_configs=None,
                 experiment_fp='', cluster_tmp_fp='cluster', home_directory_fp='~/',
                 input_format_fn=lambda x: x, libs=[]):
        """
            experiment_fp: location of the experiment to run
            cluster_tmp_fp: location of tmp folder to store temporal files created in this class
            home_directory_fp: folder path of directory that holds `.ssh` folder
            experiment_configs: an array of dictionaries
        """

        self.root = 'validation/cluster/'
        self.experiment_name = experiment_name
        self.config = cluster_config or {}
        self.experiment_configs = experiment_configs or {}
        self.experiment_fp = experiment_fp
        self.cluster_tmp_fp = cluster_tmp_fp
        self.home_directory_fp = home_directory_fp
        self.input_format_fn = input_format_fn
        self.libs = libs

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
        self.load_template_file()

    @property
    @abstractmethod
    def default_config(self):
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
        pathlib.Path(self.cluster_tmp_fp+'/scripts/').mkdir(exist_ok=True)

    def get_key_order(self, config_dict):
        """
            To store model results we need a way to sort the config parameters. Default is
                to sort the keys in alphabetical order.
        """
        keys = list(config_dict.keys())
        keys.sort()
        return keys

    def create_batch_from_template(self, file_name, file_inputs, job_name, log_name):
        """
            Creates the batch/slurm script that will run the experiments on the cluster
        """

        template = self.template

        template = template.replace('<MODELS_DIR>', self.experiment_name+'/models/')
        template = template.replace('<LOGS_DIR>', self.experiment_name+'/logs')
        template = template.replace('<NODES>', str(self.config['nodes']))
        template = template.replace('<CPUS>', str(self.config['cpus']))
        template = template.replace('<MEMORY>', str(self.config['memory']))
        template = template.replace('<TIME>', str(self.config['time']))
        template = template.replace('<FILE_NAMES>', file_name)
        template = template.replace('<FILE_INPUTS>', file_inputs)
        template = template.replace('<LOG_NAME>', log_name)

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
            ordered_config_keys = self.get_key_order(util.dict_without_key(config, 'filename'))
            inputs = [config[key] for key in ordered_config_keys]

            #convert values to file input format
            model_inputs = ['{file_input}'.format(file_input=_input) for _input in inputs]

            #input format define by the user
            file_inputs = self.input_format_fn(config)

            job_name = model+'_'+'_'.join(model_inputs)
            results_name = model+'_'+'_'.join(model_inputs)+'results.txt'
            logs_name = model+'_'+'_'.join(model_inputs)+'logs.txt'
            batch_name = 'run_'+model+'_'+'_'.join(model_inputs)+'.sh'

            #get batch script
            batch_script = self.create_batch_from_template(
                file_name,
                file_inputs,
                job_name,
                logs_name
            )

            batch_name = batch_name
            batches.append([batch_name, batch_script])

        return batches

    def save_batch(self, file_name, batch_script):
        """
            Save batch script to the tmp cluster folder
        """
        print(self.cluster_tmp_fp+'/scripts/'+file_name)
        with open(self.cluster_tmp_fp+'/scripts/'+file_name, 'w') as f:
            f.write(batch_script)

    def create_batch_scripts(self):
        """
            Generate, save and return the batch scripts to run the experiment
        """

        batches = self.get_batches()
        names = []
        #save to files
        for f_name, script in batches:
            self.save_batch(f_name, script)
            names.append(f_name)

        return names

    def send_files_to_cluster(self, batch_file_names):
        """
            Send
                self.experiment_fp
                cleanair
                batch scripts
            to cluster
        """

        #construct bash script to send files
        call_array = [
            "sudo", 
            "sh", self.root+"scripts/send_to_cluster.sh",
            "--user", self.config['user'],
            "--ip", self.config['ip'],
            "--ssh_key", self.home_directory_fp +  self.config['ssh_key'],
            "--basename", self.experiment_name,
            "--cluster_folder", self.cluster_tmp_fp,
            "--experiments_folder", self.experiment_fp,
        ]


        for f_name in batch_file_names:
            call_array.append("--slurm_file")
            call_array.append('scripts/'+f_name)

        for lib in self.libs:
            call_array.append("--lib")
            call_array.append(lib)

        subprocess.call(call_array)

    def run(self):
        """
            Run experiment.
        """

        batch_file_names = self.create_batch_scripts()
        self.send_files_to_cluster(batch_file_names)

    def get(self):
        """
            Get files from the cluster and store experiment folder.
        """

        call_array = [
            "sudo",
            "sh", self.root+"scripts/get_results.sh",
            "--user", self.config['user'],
            "--ip", self.config['ip'],
            "--ssh_key", self.home_directory_fp +  self.config['ssh_key'],
            "--basename", self.experiment_name,
            "--cluster_folder", self.cluster_tmp_fp,
            "--experiments_folder", self.experiment_fp,
        ]

        subprocess.call(call_array)


    def check(self):
        """
            Print cluster state.
        """
        #TODO: move into script
        script_str = """
ssh  -i "{SSH_KEY}" "{USER}@{IP}" -o StrictHostKeyChecking=no 'bash -s' << HERE
squeue -u {USER}
HERE
        """.format(
            SSH_KEY=self.home_directory_fp +  self.config['ssh_key'],
            USER=self.config['user'],
            IP=self.config['ip'],
        )

        cmd = os.system(script_str)

    def clean(self):
        script_str = """
ssh  -i "{SSH_KEY}" "{USER}@{IP}" -o StrictHostKeyChecking=no 'bash -s' << HERE
rm -rf {name}
HERE
    """.format(
            SSH_KEY=self.home_directory_fp +  self.config['ssh_key'],
            USER=self.config['user'],
            IP=self.config['ip'],
            name=self.experiment_name
        )

        cmd = os.system(script_str)

