"""
Entry point for validation.
"""

import argparse

from cleanair import metrics
from validation import util
from validation.dashboard import dashboard

class ValidationParser(argparse.ArgumentParser):

    def __init__(self):
        super().__init__(description="Run validation")
        self.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
        self.add_argument('-r', '--run', action='store_true', help='train and predict a model')
        self.add_argument('-k', '--check', action='store_true', help='check the status of a cluster')
        self.add_argument('-cl', '--clean', action='store_true', help='clean up experiment run')
        self.add_argument('-v', '--validate', action='store_true', help='run validation methods')
        self.add_argument('-f', '--force', action='store_true', help='force download data, even it exists')
        self.add_argument('-dash', '--dashboard', action='store_true', help='show the dashboard')
        self.add_argument('-n', '--name', type=str, help='name of the experiment')
        self.add_argument('-c', '--cluster_name', type=str, help='name of the cluster', default='laptop')
        self.add_argument('-d', '--home_directory', type=str, help='path to home directory', default='~')
        self.add_argument('-e', '--experiments_directory', type=str, default='experiment_data/', help='path to experiments directory')
        self.add_argument('-g', '--get_results', action='store_true', help='get results from cluster')

def main():
    parser = ValidationParser()
    args = parser.parse_args()
    experiment_class = util.get_experiment_class(args.name)

    models = ['svgp']

    if args.setup:
        exp = experiment_class(models=models, **vars(args))
        exp.setup(force_redownload=args.force)

    if args.run:
        exp = experiment_class(models=models, **vars(args))
        exp.run()

    if args.check:
        exp = experiment_class(args.name, models, args.cluster, directory=args.experiments_directory, **vars(args))
        exp.check_status()

    if args.clean:
        exp = experiment_class(args.name, models, args.cluster, directory=args.experiments_directory, **vars(args))
        exp.clean()

    if args.get_results:
        exp = experiment_class(args.name, models, args.cluster, directory=args.experiments_directory, **vars(args))
        exp.get()

    if args.validate:
        evaluate_training = True
        evaluate_testing = False
        xp = util.load_experiment_from_directory(**vars(args))
        xp.update_model_data_list(
            update_train=evaluate_training,
            update_test=evaluate_testing
        )
        sensor_scores_df, temporal_scores_df = xp.evaluate(
            metrics.get_metric_methods(),
            evaluate_training=evaluate_training,
            evaluate_testing=evaluate_testing
        )
        print(sensor_scores_df.sample(3))
        print(temporal_scores_df.sample(3))
        util.save_experiment_scores_df(xp, sensor_scores_df, 'sensor_scores.csv')
        util.save_experiment_scores_df(xp, temporal_scores_df, 'temporal_scores.csv')

    if args.dashboard:
        # update the experiment results
        exp = util.load_experiment_from_directory(**vars(args))
        exp.update_model_data_list(update_train=True, update_test=True)

        # run the dashboard
        dashboard.main(exp)

if __name__ == "__main__":
    main()
