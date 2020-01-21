import argparse
import importlib
import sys
import inspect

from validation import experiments, cluster

def load_experiment(file_name, root=''):
    try:
        sys.path.append(root+'experiments/')
        mod = importlib.import_module(file_name)
        return mod
    except:
        print(file_name, ' does not exist')

class ValidationParser(argparse.ArgumentParser):

    def __init__(self):
        super().__init__(description="Run validation")
        self.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
        self.add_argument('-r', '--run', action='store_true', help='train and predict a model')
        self.add_argument('-k', '--check', action='store_true', help='check the status of a cluster')
        self.add_argument('-n', '--name', type=str, help='name of the experiment')
        self.add_argument('-c', '--cluster', type=str, help='name of the cluster')
        self.add_argument('-d', '--home_directory', type=str, help='path to home directory')
        self.add_argument('-e', '--experiments_directory', type=str, help='path to experiments directory')

def get_experiment_class(name):
    """
    Get the class of experiment given the name.

    Parameters
    ___

    name : str
        Name of the experiment.

    Returns
    ___

    class
        A class object that is ready to be initialised.
    """
    mod = importlib.import_module('validation.experiments.{name}'.format(name=args.name), 'validation')
    members = inspect.getmembers(mod, inspect.isclass)

    class_index = -1
    for i in range(len(members)):
        if members[i][0].lower() == '{name}experiment'.format(name=name):
            class_index = i

    if class_index < 0:
        raise FileNotFoundError("Class for {name} does not exist.".format(name=name))

    return members[class_index][1]


if __name__=="__main__":
    parser = ValidationParser()
    args = parser.parse_args()
    experiment_class = get_experiment_class(args.name)

    if args.setup:
        models = ['svgp']
        exp = experiment_class(args.name, models, args.cluster)
        exp.setup()
        print(exp.name)

    elif args.run:
        pass

    elif args.check:
        pass
    