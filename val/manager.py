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
        self.add_argument('-e', '--experiments_directory', type=str, default='experiment_data', help='path to experiments directory')

def main():
    parser = ValidationParser()
    args = parser.parse_args()
    experiment_class = util.get_experiment_class(args.name)

    models = ['svgp']
    print(vars(args))
    exp = experiment_class(args.name, models, args.cluster, directory=args.experiments_directory, **vars(args))

    if args.setup:
        models = ['svgp']
        exp.setup(force_redownload=args.force)
        print(exp.name)

    elif args.run:
        models = ['svgp']
        exp.update_model_data_list(update_train=False, update_test=False)
        for model_data in exp.model_data_list:
            print(model_data.get_training_dicts()['laqn']['Y']['NO2'])
            print(model_data.get_testing_dicts()['laqn']['Y']['NO2'])
            print()

        exp.run()

    elif args.check:
        pass

if __name__ == "__main__":
    main()
    
