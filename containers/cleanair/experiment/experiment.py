from abc import ABC, abstractmethod
from .instance import Instance
from ..models import ModelData

class Experiment(ABC):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
class TestExperiment(Experiment):
    
    def __init__(self, **kwargs):
        # create one quick to run instance
        instance = Instance(model_name="svgp")
        data = dict(instance.model_data.id)
        super().__init__(**kwargs)
