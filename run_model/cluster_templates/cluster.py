"""
    Run experiments on clusters
"""
from abc import ABC, abstractmethod

class Cluster(ABC):
    """
        Organise all available clusters
    """
    def __init__(self):
        self.base_name = None
        self.slurm_template = ""
        self.cluster_config = {}
        self.tmp_folder = 'cluster'
        self.ip = None
        self.user = None
        self.ssh_key = None
        self.defaults = {}
        self.template = None
        self.home_dir = ''

    @abstractmethod
    def get_default_params(self):
        """
            Get default cluster parameters
        """


    @abstractmethod
    def get_max_params(self):
        """
            Each cluster has a maximum on the number of resources available. This returns them.
        """

    def load_template_file(self):
        """
            Load the slurm batch template file.
        """
        template = None

        with open(self.slurm_template, 'r') as file_name:
            template = file_name.read()

        self.template = template

    def ensure_last_backslash(self, dir_str):
        """
            Ensure directory ends in a backslash
        """
        if dir_str[-1] is not '/':
            return dir_str+'/'
        return dir_str

    def list_to_str(self, arr, fill=' '):
        """
            @TODO: there is probably a built in python function for this.
            A: is an array of strings
            returns: a single string with spaces between
        """
        list_str = ""
        for i, elem in enumerate(arr):
            if i == len(arr)-1:
                #No space at end
                list_str += "{a}".format(a=elem)
            else:
                list_str += "{a}{fill}".format(a=elem, fill=fill)
        return list_str

    def ensure_config_defaults(self, config):
        """
            Fill in missing parameters in config with the default parameters
        """
        for k in self.defaults:
            if k not in config:
                config[k] = self.defaults[k]
        return config

    def check_config_max_settings(self):
        """
            Make sure current configurations do not exceed the max
        """
        pass

    def create_batch_from_template(self, file_name, file_inputs, job_name, log_name):
        """
            Creates the batch/slurm script that will run the experiments on the cluster
        """

        template = self.template

        template = template.replace('<MODELS_DIR>', self.base_name+'/models/')
        template = template.replace('<LOGS_DIR>', self.base_name+'/cluster/logs')
        template = template.replace('<NODES>', str(self.cluster_config['nodes']))
        template = template.replace('<CPUS>', str(self.cluster_config['cpus']))
        template = template.replace('<MEMORY>', str(self.cluster_config['memory']))
        template = template.replace('<TIME>', str(self.cluster_config['time']))
        template = template.replace('<FILE_NAMES>', file_name)
        template = template.replace('<FILE_INPUTS>', file_inputs)

        return template

    def get_batches(self, param_configs, data_configs):
        """
            Each experiment run will have its own batch script, one for each combination in param_configs and data_configs.
        """
        batches = []
        for d_id, _ in enumerate(data_configs):
            for model in param_configs:
                for p_id, _ in enumerate(param_configs[model]):
                    #assume model is m_<model>.py
                    file_name = 'm_{model}'.format(model=model)
                    file_inputs = '{data_id} {param_id}'.format(data_id=d_id, param_id=p_id)

                    job_name = model+'_'+'{data_id}_{param_id}'.format(data_id=d_id, param_id=p_id)
                    results_name = model+'_'+'{data_id}_{param_id}_results.txt'.format(data_id=d_id, param_id=p_id)

                    t = self.create_batch_from_template(file_name, file_inputs, job_name, results_name)
                    batch_name = 'run_{model}_{d}_{p}.sh'.format(model=model, d=d_id, p=p_id)
                    batch_name = self.tmp_folder+'/'+batch_name
                    batches.append([batch_name, t])
        return batches

    def save_batch(self, name, script):
        with open(name, 'w') as f:
            f.write(script)

    def create_batch_scripts(self, param_configs, data_configs):
        """
            Generate, save and return the batch scripts to run the experiment
        """
        #get batch scripts
        self.load_template_file()
        batches = self.get_batches(param_configs, data_configs)

        names = []
        #save to files
        for f_name, script in batches:
            self.save_batch(f_name, script)
            names.append(f_name)

        return names

class Orac(Cluster):
    """
        Orac cluster run by Warwick
    """
    def __init__(self):
        Cluster.__init__(self)
        self.slurm_template = 'cluster_templates/batch_script_template.sh'
        self.ip = 'orac.csc.warwick.ac.uk'
        self.user = 'csrcqm'
        self.ssh_key = '.ssh/ollie_rsa'

    def get_default_params(self):
        return {}

    def get_max_params(self):
        return {}

class Pearl(Cluster):
    """
        Pearl Cluster
    """
    def __init__(self):
        Cluster.__init__(self)
        self.slurm_template = 'cluster_templates/batch_script_pearl_template.sh'

        self.ip = 'ui.pearl.scd.stfc.ac.uk'
        self.user = 'pearl023'
        self.ssh_key = '.ssh/patrick-pearl'

        self.defaults = {
            'cpus': 1,
            'gpus': 1,
            'nodes': 1,
            'time': '00:30:00',
            'memory': 4571
        }

        #TODO: fill in max configs
        self.max_configs = {
            'cpus': 1,
            'gpus': 1,
            'nodes': 1,
            'time': '00:10:00',
            'memory': 4571
        }

    def get_default_params(self):
        return self.defaults

    def get_max_params(self):
        return self.max_configs

    def setup(self, base_name, home_dir, cluster_config):
        self.base_name = base_name
        self.home_dir = self.ensure_last_backslash(home_dir)
        print(self.home_dir)

        #fill in missing configs with the defauls
        self.cluster_config = self.ensure_config_defaults(cluster_config)
        self.check_config_max_settings()

    def create_batch_from_template(self, file_name, file_inputs, job_name, log_name, ):
        """
            Creates the batch/slurm script that will run the experiments on the cluster
        """

        template = self.template
        template = template.replace('<MODELS_DIR>', self.base_name+'/models/')
        template = template.replace('<LOGS_DIR>', self.base_name+'/cluster/logs')
        template = template.replace('<NODES>', str(self.cluster_config['nodes']))
        template = template.replace('<CPUS>', str(self.cluster_config['cpus']))
        template = template.replace('<MEMORY>', str(self.cluster_config['memory']))
        template = template.replace('<TIME>', str(self.cluster_config['time']))
        template = template.replace('<FILE_NAMES>', file_name)
        template = template.replace('<FILE_INPUTS>', file_inputs)
        template = template.replace('<JOB_NAME>', job_name)
        template = template.replace('<LOG_NAME>', log_name)

        return template



