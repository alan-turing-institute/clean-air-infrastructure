# Validation

## Entry point

To create, run or check an experiment use the command line interface of manager.py.
To see available options, use the `-h` argument.

```bash
python manager.py -h
```

To setup an experiment use the `-s` tag then specify the experiment parameters:

```bash
python manager.py -s -n basic -c laptop
```

To run an experiment, use the `-r` tag with the parameters of an experiment that has already been setup:
```bash
python manager.py -r -n basic -c laptop
```

## Folder structure of an experiment

This directory structure is created by the `setup()` function of an experiment object.

```
name/
    data/
        data0/
            config.json
            normalised_pred_data.csv
            normalised_training_data.csv
            test.pickle
            train.pickle
        ...
    meta/
        experiment.csv
        model_params.json
        data.json
    models/
        m_svgp.py
        m_dgp.py
        restore/
    results/
        svgp_param0_data0/
            train_pred.pickle
            test_pred.pickle
            elbo.pickle
        ...
```

## File structure of pickles

Both `data/ID/train.pickle` and `data/ID/test.pickle` are formatted as follows.
Here 'src' is a string representing the source, e.g. 'laqn', 'aqe', 'sat':

```
{
    'src' : {
        'index': np.array,
        'X': np.array,
        'Y': {
            'NO2':np.array,
            'PM10':np.array,
            'PM25':np.array
        }
}
```

`results/ID/train_pred.pickle` and `results/ID/test_pred.pickle`:
```
{
    'laqn' : {
        'NO2' : {
            'mean' : np.array,
            'var' : np.array
        },
        'PM10' : {
            'mean' : np.array,
            'var' : np.array
        }
    }
}
```

To retrieve info about a prediction of NO2 for laqn in `results/ID/test_pred.pickle`, you would need to look that info up by finding the index in `results/ID/test.pickle`.