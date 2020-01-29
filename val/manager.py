"""
Entry point for validation.
"""

import argparse

from validation import util, metrics
from validation.dashboard import dashboard

class ValidationParser(argparse.ArgumentParser):

    def __init__(self):
        super().__init__(description="Run validation")
        self.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
        self.add_argument('-r', '--run', action='store_true', help='train and predict a model')
        self.add_argument('-k', '--check', action='store_true', help='check the status of a cluster')
        self.add_argument('-v', '--validate', action='store_true', help='run validation methods')
        self.add_argument('-f', '--force', action='store_true', help='force download data, even it exists')
        self.add_argument('-dash', '--dashboard', action='store_true', help='show the dashboard')
        self.add_argument('-n', '--name', type=str, help='name of the experiment')
        self.add_argument('-c', '--cluster_name', type=str, help='name of the cluster', default='laptop')
        self.add_argument('-d', '--home_directory', type=str, help='path to home directory', default='~')
        self.add_argument('-e', '--experiments_directory', type=str, default='experiment_data/', help='path to experiments directory')

def main():
    parser = ValidationParser()
    args = parser.parse_args()
    experiment_class = util.get_experiment_class(args.name)

    models = ['svgp']
    print(vars(args))

    if args.setup:
        exp = experiment_class(models=models, **vars(args))
        exp.setup(force_redownload=args.force)

    if args.run:
        exp = experiment_class(models=models, **vars(args))
        exp.run()

    if args.check:
        pass

    if args.validate:
        xp = util.load_experiment_from_directory(**vars(args))
        xp.update_model_data_list(update_train=False, update_test=True)
        sensor_scores_df, temporal_scores_df = metrics.evaluate_experiment(xp, metrics.get_metric_methods(), evaluate_training=True, evaluate_testing=False)
        print(sensor_scores_df)
        print(temporal_scores_df)

    if args.dashboard:
        # update the experiment results
        exp = util.load_experiment_from_directory(**vars(args))
        exp.update_model_data_list(update_train=True, update_test=True)

        # run the dashboard
        dashboard.main(exp)

if __name__ == "__main__":
    main()
