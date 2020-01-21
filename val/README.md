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