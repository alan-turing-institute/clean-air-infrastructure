"""
Given a model data object, check that the data matches the config.
"""

def check_training_set(model_data):
    """
    Check the shape of all the numpy arrays are correct.
    """
    # load the dicts from modeldata
    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    x_train = training_data_dict['X']
    y_train = training_data_dict['Y']
    
    # checks for satellite
    assert not model_data.config['include_satellite'] or 'satellite' in x_train
    assert not model_data.config['include_satellite'] or 'satellite' in y_train

    # checks that each pollutant has a key in y_train for each source
    all_train_sources = model_data.config['train_sources'] if not model_data.config['include_satellite'] else model_data.config['train_sources'] + ['satellite']
    for source in all_train_sources:
        # check all training sources exist in the dicts
        assert source in x_train
        assert source in y_train

        # check the shape of x_train
        if source == "satellite":
            assert len(x_train[source].shape) == 3
        else:
            assert len(x_train[source].shape) == 2

        # check y_train
        for pollutant in model_data.config['species']:
            assert pollutant in y_train[source]

            # check the shapes of y_train
            assert y_train[source][pollutant].shape[1] == 1     # shape should be (N, 1)
            assert y_train[source][pollutant].shape[0] == x_train[source].shape[0]

def check_test_set(model_data):
    """
    Check the test set is in the right format.
    """
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False, return_y=True)
    x_test = predict_data_dict['X']
    assert 'satellite' not in x_test


    for source in model_data.config['pred_sources']:
        assert source in x_test
        assert len(x_test[source]) == 2
