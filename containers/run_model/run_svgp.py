import sys
sys.path.append('../')
import cleanair
from cleanair.models import SVGP_TF1

import numpy as np

X = np.load('data/processed_x_train.npy', allow_pickle=True)
Y = np.load('data/processed_y_train.npy', allow_pickle=True)

m = SVGP_TF1()

model_parameters = {
    'n_inducing_points': 200
}

m.fit(X, Y, max_iter=11, model_params=model_parameters, refresh=10)
ys, ys_var = m.predict(X[1][:, 0, :])
print(ys, ys_var)
