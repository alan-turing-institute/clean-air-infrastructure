Running on a Cluster
===========================

# Layout

## Folder Layout

The experiment must have the following format:

```
run_model/
    experiments/
        experiment1/
            data/
                data0_x_test.npy
                data0_y_test.npy
                data0_x_train.npy
                data0_y_train.npy
                data1_x_test.npy
                ...
            meta/
                experiment.csv
                svgp_params.json
                dgp_params.json
                data.json
                meta.json
            models/
                m_svgp.py
                m_dgp.py
                restore/
            results/
                svgp_param0_data0_y_pred.npy
                dgp_param1_data0_y_pred.npy
                ...

        experiment2/
            data/
            meta/
            models/
            results/
```

## Data

All data must be placed in `data/`.

## Models

All models are placed in `models/`. The file names must be prepended with `m_` (for example `m_svgp.py`). Within the file the follow template must be used:

```py
def get_config():
    return [
        {
            'name': '<insert>', #unique model name
            'prefix': '<insert>', #used to prefix results and restore files
            'ignore': False
        }        
    ]

def main(config):
    pass


if __name__ == '__main__':
    #default config
    i = 0

    #use command line argument if passed
    if len(sys.argv) == 2:
        i = int(sys.argv[1])

    config = get_config()[i]

    main(config)
```

# Run on cluster

To run models on the cluster run `sudo python run_on_cluster.py`. 

@TODO: sudo is required on my machine, check why.

## Configurations

Within `run_on_cluster.py` there are two configuration dicts. In here the desired cluster, number of cores, cpus, walltime etc can be defined. 


# Check status

Run `sudo python check_cluster.py`. This will use the same configs as defined in `run_on_cluster.py`. 


# Get results

Run `sudo python get_cluster_results.py.py`. This will use the same configs as defined in `run_on_cluster.py` and will store the results in `cluster/` with the current datetime prefixed.