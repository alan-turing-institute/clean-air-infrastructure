class Model(object):
    def __init__(self):
        raise NotImplementedError

    def fit(self, X, Y, **kwargs):
            raise NotImplementedError

    def predict(self, X, **kwargs):
            raise NotImplementedError
