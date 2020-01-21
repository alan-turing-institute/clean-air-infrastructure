"""
Entry point for validation.
"""

import argparse

from validation import util

class ValidationParser(argparse.ArgumentParser):

    def __init__(self):
        super().__init__(description="Run validation")
        self.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
        self.add_argument('-r', '--run', action='store_true', help='train and predict a model')
        self.add_argument('-k', '--check', action='store_true', help='check the status of a cluster')
        self.add_argument('-f', '--force', action='store_true', help='force download data, even it exists')
        self.add_argument('-n', '--name', type=str, help='name of the experiment')
        self.add_argument('-c', '--cluster', type=str, help='name of the cluster')
        self.add_argument('-d', '--home_directory', type=str, help='path to home directory')
        self.add_argument('-e', '--experiments_directory', type=str, help='path to experiments directory')

if __name__=="__main__":
    parser = ValidationParser()
    args = parser.parse_args()
    experiment_class = util.get_experiment_class(args.name)

    if args.setup:
        models = ['svgp']
        exp = experiment_class(args.name, models, args.cluster)
        exp.setup(force_redownload=args.force)
        print(exp.name)

    elif args.run:
        pass

    elif args.check:
        pass
    