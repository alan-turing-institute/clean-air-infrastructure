import sys
sys.path.append('../../containers')
sys.path.append('../containers') #for when running on a cluster
import cleanair
from cleanair.models import SVGP_TF1

import numpy as np


def get_config():
    return [
        {
            'name': 'svgp', #unique model name
            'prefix': 'svgp', #used to prefix results and restore files
            'n_inducing_points': 200,
            'max_iter': 10000,
            'refresh': 10,
            'train': True, #flag to turn training on or off. Useful if just want to predict.
            'restore': False, #Restore model before training/predicting.
            'laqn_id': 0
        }        
    ]

def main(config):
    X = np.load('../data/processed_x_train.npy', allow_pickle=True)
    Y = np.load('../data/processed_y_train.npy', allow_pickle=True)

    #make X the correct dimension, add discreitisation column
    X = [X[0][:, None, :]]

    m = SVGP_TF1()

    model_parameters = config

    m.fit(X, Y, max_iter=config['max_iter'], model_params=model_parameters, refresh=config['refresh'])

    ys, ys_var = m.predict(X[config['laqn_id']][:, 0, :])

    pred_y = np.concatenate([ys, ys_var], axis=1)
    # np.save('../results/{prefix}_y'.format(prefix=config['prefix']), pred_y)
    np.save(y_pred_fp, pred_y)


if __name__ == '__main__':
    #default config
    i = 0

    #use command line argument if passed
    if len(sys.argv) == 2:
        i = int(sys.argv[1])

    config = get_config()[i]

    main(config)

