"""
Entry point for validation.
"""

import argparse

from validation import util, metrics

class ValidationParser(argparse.ArgumentParser):

    def __init__(self):
        super().__init__(description="Run validation")
        self.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
        self.add_argument('-r', '--run', action='store_true', help='train and predict a model')
        self.add_argument('-k', '--check', action='store_true', help='check the status of a cluster')
        self.add_argument('-v', '--validate', action='store_true', help='run validation methods')
        self.add_argument('-f', '--force', action='store_true', help='force download data, even it exists')
        self.add_argument('-n', '--name', type=str, help='name of the experiment')
        self.add_argument('-c', '--cluster', type=str, help='name of the cluster')
        self.add_argument('-d', '--home_directory', type=str, help='path to home directory')
        self.add_argument('-e', '--experiments_directory', type=str, default='experiment_data/', help='path to experiments directory')

def main():
    parser = ValidationParser()
    args = parser.parse_args()
    experiment_class = util.get_experiment_class(args.name)

    models = ['svgp']
    print(vars(args))

    if args.setup:
        exp = experiment_class(args.name, models, args.cluster, directory=args.experiments_directory, **vars(args))
        exp.setup(force_redownload=args.force)

    if args.run:
        exp = experiment_class(args.name, models, args.cluster, directory=args.experiments_directory, **vars(args))
        exp.run()

    if args.check:
        pass

    if args.validate:
        exp = util.load_experiment_from_directory(args.name, experiment_data=args.experiments_directory)
        exp.update_model_data_list(update_train=False, update_test=True)
        for model_data in exp.model_data_list:
            print(metrics.measure_scores_by_sensor(model_data.normalised_pred_data_df, metrics.get_metric_methods()))
            print()

if __name__ == "__main__":
    main()
