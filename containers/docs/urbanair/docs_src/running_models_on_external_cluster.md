# Running AQ Models on an External Cluster



The external cluster is only used to run the actual model and perform predictions. All of the data setup, processing and prediction upload is done locally. 

## Build Docker Image

Build the latest docker image:

```bash
docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/mf -f containers/dockerfiles/model_fitting.Dockerfile containers

docker push cleanairdocker.azurecr.io/mf:latest
```



## Setting up Cluster

We now set up docker/singularity and the required folder structure on the external cluster. `ssh` into the cluster and run:

```bash
mkdir cleanair
cd cleanair/
mkdir containers
cd containers

singularity pull --docker-login docker://cleanairdocker.azurecr.io/mf:latest
```

This will prompt for a docker username and password. Please contact the `cleanair` owners for access. 

Building the `.sif` file:

```bash
cd ../
singularity build --docker-login containers/mf_latest.sif docker://cleanairdocker.azurecr.io/mf:latest	
```

which again will ask for a username and password prompt.

To run the models we will use slurm. An example sbatch file is:

```
touch sbatch.sh
```



```
#!/bin/bash
#SBATCH --job-name=mrdgp
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=12
#SBATCH --mem-per-cpu=4571
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:0

#SBATCH --output=logs/slurm_%j__mrdgp,order_id-0.log

#########################
#
# Job: m_shallow_models,order_id-0
#
#########################

##### Setup Environment

##### Run Command
cd ~/cleanair
# run script with arguments
singularity run containers/model_fitting_latest.sif run.sh
```

where run.sh is

```bash
urbanair model run mrdgp example_dir/
```



### Setting Up Data - On Local Machine

Make sure you are in the project directory `clean-air-infrastructure/`. We use the `urbanair` CLI to download and process the required training and prediction data. 

```bash
urbanair init production

urbanair model data generate-config \
    --trainupto yesterday \
    --traindays 1 \
    --preddays 1 \
    --train-source laqn \
    --train-source satellite \
    --pred-source laqn \
    --species NO2 \
    --overwrite
    
    
urbanair model data generate-full-config
# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

urbanair model setup mrdgp --maxiter 10 --num-inducing-points 100
```

This saves the experiment data in the `urbanair` cache. To copy this to another folder run

```bash
urbanair model data save-cache ~/Documents/example_dir
```

replacing `example_dir` with the required directory.



### Setting Up Data - On Cluster

Move the saved cache folder to `cleanair/` on the external cluster, e.g:

```
scp -i ~/.ssh/ollie-pearl -C -r ~/Documents/example_dir pearl053@ui.pearl.scd.stfc.ac.uk:~/cleanair/

scp -i ~/.ssh/ollie_cluster_rsa -C -r ~/Documents/example_dir csrcqm@orac.csc.warwick.ac.uk:cleanair/
```

## Running the Model - On Cluster

`ssh` on to the cluster and run

```bash
cd cleanair
sh ./run.sh
```

