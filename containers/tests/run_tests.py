"""
Entrypoint for tests.
"""
from cleanair.models import ModelData
from . import check_training_set
from . import check_test_set

def main():
    """
    Run all tests.
    """
    # ToDo: load a modeldata object from file
    config_dir = './'
    model_data = ModelData(config_dir=config_dir)

    # run tests
    check_training_set(model_data)
    check_test_set(model_data)

if __name__ == "__main__":
    main()
