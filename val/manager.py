import argparse

from validation import experiments, cluster

class ValidationParser(argparse.ArgumentParser):

    def __init__(self):
        super().__init__(description="Run validation")
        self.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
        self.add_argument('-r', '--run', action='store_true', help='train and predict a model')
        self.add_argument('-n', '--name', type=str, help='name of the experiment')
        self.add_argument('-c', '--cluster', type=str, help='name of the cluster')
        self.add_argument('-d', '--home_directory', type=str, help='path to home directory')
        self.add_argument('-e', '--experiments_directory', type=str, help='path to experiments directory')


if __name__=="__main__":
    parser = ValidationParser()
    args = parser.parse_args()
    