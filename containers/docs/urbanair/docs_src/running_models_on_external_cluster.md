# Running AQ Models on an External Cluster



The external cluster is only used to run the actual model and perform predictions. All of the data setup, processing and prediction upload is done locally.  This is organised into 3 sections: Setting up locally, Running on cluster, Updating Results and correspond to `containers/scripts`, ``containers/scripts`, `containers/scripts` that complete each of these steps automatically. 



## 1 ) Local Setup

Setting up locally consists of building and pushing the docker image that computes model fitting, and downloading and setting up the experiment data.

### Build Docker Image

Build the latest docker image:

```bash
docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/mf -f containers/dockerfiles/model_fitting.Dockerfile containers

docker push cleanairdocker.azurecr.io/model_fitting:latest
```

### Data setup

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
urbanair model data save-cache example_dir
```

replacing `example_dir` with the required directory.

## 2) Running on cluster

To run on the cluster we use singularity. We first have to setup the folder structure on the cluster, setup the singularity image, move the required data over and then run models.

### Setting up Cluster

We now set up docker/singularity and the required folder structure on the external cluster. `ssh` into the cluster and run:

```bash
mkdir cleanair
cd cleanair/
mkdir containers
cd containers

singularity pull --docker-login docker://cleanairdocker.azurecr.io/model_fitting:latest
```

This will prompt for a docker username and password. Please contact the `cleanair` owners for access. 

To run the models we will use slurm. Create a batch file:

```
touch sbatch.sh
```

and copy in:

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
singularity exec containers/model_fitting_latest.sif urbanair model fit mrdgp example_dir/
```

### Moving Data to the cluster

Move the saved cache folder to `cleanair/` on the external cluster, e.g:

```bash
scp -i $CLUSTER_KEY -C -r example_dir $CLUSTER_USER@$CLUSTER_ADDR:cleanair/
```

### Running the models

To run the model fitting simply execute

```bash
sbatch sbatch.sh
```

## 3) Updating Results

To update the results in the cleanair database we need to move the results from the external cluster to the experiment directory and then push the results:

```bash
#sync folder from cluster to CACHE_FOLDER/results
scp -i $CLUSTER_KEY -C -r $CLUSTER_USER@$CLUSTER_ADDR:cleanair/example_dir/result/*.pkl example_dir/result/

cd ../../

#update clean air server

urbanair init production
urbanair model update results mrdgp example_dir
```



## Using script to run the above Automatically

The above steps can be run automatically using `scripts/model_fitting_setup_local.sh`,  `scripts/model_fitting_setup_cluster_and_run.sh`, `scripts/model_fitting_sync_from_cluster.sh`.

Before running create a file called `.secrets/model_fitting_settings.sh` and place in the following:

```bash
#setup variables
CACHE_DIR='<CACHE_DIR>'
CACHE_FOLDER="<FULL_PATH_TO_FOLDER>/$CACHE_DIR"
CLUSTER_USER='<CLUSTER_USERNAME>'
CLUSTER_KEY='<CLUSTER_KEY>'
CLUSTER_ADDR='<CLUSTER_IP>'
MODEL='<MODEL_NAME (mrdgp|svgp)>'
CLUSTER_NAME='<CLUSTER_NAME_ID_USED_TO_TAG_PREDICTIONS (orac|pearl)>'

DOCKER_PASSWORD='<DOCKER_PASSWORD>'
DOCKER_USERNAME='<DOCKER_USERNAME>'
```

And then run the following. To complete step 1 and 2:

```
cd scripts
sh ./model_fitting_setup_local.sh
sh ./model_fitting_setup_cluster_and_run.sh
```

once the model has completed run

```
model_fitting_sync_from_cluster.sh
```

which will automatically push the results to the server.

