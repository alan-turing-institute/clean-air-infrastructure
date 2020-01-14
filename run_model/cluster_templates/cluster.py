class Cluster(object):
    def __init__(self):
        self.slurm_template = ""
        self.cluster_config = None
        self.tmp_folder = 'cluster'

    def get_default_params(self):
        pass

    def get_max_params(self):
        pass

    def load_template_file(self):
        template = None

        with open(self.slurm_template, 'r') as f:
            template = f.read()
        
        return template

    def ensure_last_backslash(self, s):
        if s[-1] is not '/':
            return s+'/'
        return s

    def list_to_str(self, A):
        """
            @TODO: there is probably a built in python function for this.
            A: is an array of strings
            returns: a single string with spaces between
        """
        s = ""
        for i in range(len(A)):
            a = A[i]
            if i == len(A)-1:
                #No space at end
                s += "{a}".format(a=a)
            else:
                s += "{a} ".format(a=a)
        return s

    def ensure_config_defaults(self, config):
        for k in self.defaults:
            if k not in config:
                config[k] = self.defaults[k]
        return config

    def check_config_max_settings(self):
        pass

    def get_template(self, home_dir, parallel_args_names, parallel_args_ids, _configs):
        pass

    def create_batch_from_template(self, template, base_name, file_name, file_inputs):
        """
            Creates the batch/slurm script that will run the experiments on the cluster
        """

        template = template.replace('<MODELS_DIR>', base_name+'/models/')
        template = template.replace('<LOGS_DIR>', base_name+'/cluster/logs')
        template = template.replace('<NODES>', str(self.cluster_config['nodes']))
        template = template.replace('<CPUS>', str(self.cluster_config['cpus']))
        template = template.replace('<MEMORY>', str(self.cluster_config['memory']))
        template = template.replace('<TIME>', str(self.cluster_config['time']))
        template = template.replace('<FILE_NAMES>', file_name)
        template = template.replace('<FILE_INPUTS>', file_inputs)

        return template

    def get_batches(self, template, param_configs, data_configs):
        batches = []
        for d_id, d_config in enumerate(data_configs):
            for model in param_configs:
                for p_id, p_config in enumerate(param_configs[model]):
                    #assume model is m_<model>.py
                    model_dir = ''
                    base_name = ''
                    file_name = 'm_{model}'.format(model=model)
                    file_inputs = '{data_id} {param_id}'.format(data_id=d_id, param_id=p_id)

                    t = self.create_batch_from_template(template, base_name, file_name, file_inputs)
                    batch_name = 'run_{model}_{d}_{p}.sh'.format(model=model, d=d_id, p=p_id)
                    batches.append([batch_name, t])
        return batches

    def save_batch(self, name, script):
        with open(self.tmp_folder+'/'+name, 'w') as f:
            f.write(script)




class Orac(Cluster):
    def __init__(self):
        super(Orac).__init__()
        self.slurm_template = 'cluster_templates/batch_script_template.sh'

    def get_default_params(self):
        pass

    def get_max_params(self):
        pass

class Pearl(Cluster):
    def __init__(self):
        Cluster.__init__(self)
        self.slurm_template = 'cluster_templates/batch_script_pearl_template.sh'
        self.defaults = {
            'cpus': 1,
            'gpus': 1,
            'nodes': 1,
            'time': '00:10:00',
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

    def setup(self, home_dir, cluster_config):
        self.home_dir = self.ensure_last_backslash(home_dir)
        print(self.home_dir)

        #fill in missing configs with the defauls
        self.cluster_config = self.ensure_config_defaults(cluster_config)
        self.check_config_max_settings()

    def create_batch_scripts(self, param_configs, data_configs):
        #get batch scripts
        template = self.load_template_file()
        batches = self.get_batches(template, param_configs, data_configs)

        #save to files
        for f_name, script in batches:
            self.save_batch(f_name, script)

