Running on a Cluster
===========================

# Layout

## Folder Layout

The experiment must have the following format:

```
    data/
    models/
    models/restore/
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