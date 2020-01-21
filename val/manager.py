import argparse
import importlib
import sys

from validation import experiments, cluster

AVAILABLE_EXPERIMENTS = {
    'basic':experiments.basic.BasicExperiment
}

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


if __name__=="__main__":
    parser = ValidationParser()
    args = parser.parse_args()

    mod = load_experiment(args.name, root='validation/experiments/')

    if mod is None:
        raise ValueError('Experiment {name} does not exist'.format(name=args.name))

    if args.setup:
        pass

    elif args.run:
        mod.run()

    elif args.check:
        pass


    
