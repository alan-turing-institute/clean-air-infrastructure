import os
import numpy
import sys
sys.path.append('../containers/') #allow cleanair to be imported
import importlib

#=========================================== SETTINGS ===========================================
#Every cluster has its own maximum allocations. 
max_settings = {
    'tinis': {
        'time': '48:00:00',
        'memory': 4571,
        'shh_key': '~/.ssh/ollie_rsa',
        'user': 'csrcqm',
        'ip': 'tinis.csc.warwick.ac.uk',
        'slurm_template': 'cluster_templates/batch_script_tinis_template.sh'
    },
    'orac': {
        'time': '48:00:00',
        'memory': 4571,
        'shh_key': '~/.ssh/ollie_rsa',
        'user': 'csrcqm',
        'ip': 'orac.csc.warwick.ac.uk'
    },
    'pearl': {
        'time': '48:00:00',
        'memory': 4571,
        'shh_key': '~/.ssh/patrick-pearl',
        'user': 'pearl023',
        'ip': 'ui.pearl.scd.stfc.ac.uk'
    },
}

#Config to run
cluster_config = {
    'cluster': 'tinis',
    'base_name': 'test', #folder to store models/results on cluster
    'models_root': 'models',
    'nodes': 1,
    'cpus': 1,
    'time': '01:00:00', 
    'memory': 4571
}


#=========================================== METHODS ===========================================

def get_configurations(cluster_config):
    MODELS_ROOT = cluster_config['models_root']
    #get all files  MODELS_ROOT/m_*
    experiment_files = [filename for filename in os.listdir(MODELS_ROOT) if filename.startswith("m_")]

    def load_mod(root):
        #load model file
        spec = importlib.util.spec_from_file_location("", root)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        return foo

    #list of file names to run
    parallel_args_names = []
    #list of corresponding config ids to run
    parallel_args_ids = []

    for f in experiment_files:
        m = load_mod(MODELS_ROOT+'/'+f)
        #each model has a list of different configurations to run
        _configs = m.get_config()

        if type(_configs) is not list:
                _configs = [_configs]

        i = 0
        for c in _configs:
            #ignore if ignore flag is True
            if 'ignore' in c and c['ignore'] is True: continue

            #remove file ending
            f = f.split('.')[0] 

            #store models to run
            parallel_args_names.append(f)
            parallel_args_ids.append(i)
            i+=1

    return parallel_args_names, parallel_args_ids, _configs

def list_to_str(A):
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

def load_template_file(template_file):
    template = None

    with open(template_file, 'r') as f:
        template = f.read()
    
    return template

def get_template(parallel_args_names, parallel_args_ids, _configs, cluster_config):
    """
        Creates the batch/slurm script that will run the experiments on the cluster
    """
    cluster_settings = max_settings[cluster_config['cluster']]
    template = load_template_file(cluster_settings['slurm_template'])

    FILE_NAMES = list_to_str(parallel_args_names)
    FILE_INPUTS = list_to_str(parallel_args_ids)


    template = template.replace('<MODELS_DIR>', cluster_config['base_name']+'/'+cluster_config['models_root'])
    template = template.replace('<LOGS_DIR>', cluster_config['base_name']+'/cluster/logs')
    template = template.replace('<NODES>', str(cluster_config['nodes']))
    template = template.replace('<CPUS>', str(cluster_config['cpus']))
    template = template.replace('<MEMORY>', str(cluster_config['memory']))
    template = template.replace('<TIME>', str(cluster_config['time']))
    template = template.replace('<FILE_NAMES>', FILE_NAMES)
    template = template.replace('<FILE_INPUTS>', FILE_INPUTS)

    return template
    



#=========================================== MAIN ===========================================
parallel_args_names, parallel_args_ids, _configs = get_configurations(cluster_config)
template = get_template(parallel_args_names, parallel_args_ids, _configs, cluster_config)
print(template)

