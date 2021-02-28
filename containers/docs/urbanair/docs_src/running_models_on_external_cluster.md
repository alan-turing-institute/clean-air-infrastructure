# Running AQ Models on an External Cluster



The external cluster is only used to run the actual model and perform predictions. All of the data setup, processing and prediction upload is done locally.  

We first show how to run setup, run and push experiments using the following scripts `containers/scripts/model_fitting_setup_local.sh`, ``containers/scripts/model_fitting_setup_cluster_and_run.sh`, `containers/scripts/model_fitting_sync_from_cluster.sh` and then we describe the steps to achieve the same, but manually.



## Using script to run experiments

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
EXPERIMENT_NAME='<dgp_vary_static_features|svgp_vary_static_features>'

DOCKER_TAG='<eg ollie|patrick>'
EXPERIMENT_NAMES=('dgp_vary_static_features' 'svgp_vary_static_features')
MODELS=('mrdgp' 'svgp')
USE_GPU=<0|1>
NUM_GPU=1

DOCKER_PASSWORD='<DOCKER_PASSWORD>'
DOCKER_USERNAME='<DOCKER_USERNAME>'
```

replacing the values with the relevant values, and cd to the scripts folder

```bash
cd scripts
```

### 1 ) Local Setup

To build and push the model run docker file and setup all experiment instances into <CACHE_FOLDER> run:

```bash
sh ./model_fitting_setup_local.sh --build --setup
```

If the docker file is already built that step can be skipped by not passing the `--build` tag. If the experiment instances are already setup then that step can also be skipped by on passing the `--setup` tag.

### 2) Running on cluster

To setup the cluster folder, build the singularity images and run the instances run:

```bash
sh ./model_fitting_setup_cluster_and_run.sh
```

To skip the setup step (ie the cluster folder already exists) pass a `--no-setup` tag, and so not submit jobs to sbatch pass a `--dry tag`. 

### 3) Updating results

To download results and push to the cleanair database run:

```bash
sh ./model_fitting_sync_from_cluster.sh
```

To skip downloading from the cluster (eg it is already downloaded) pass a `--no-sync` tag and to not push results to the cleanair database pass a `--no-push` tag.

## Manual Experiment runs

The below scripts have to be configured for each user. For simplicity we use the same variables defined in `.secrets/model_fitting_settings.sh` above.

### 1) Local Setup

Setting up locally consists of building and pushing the docker image that computes model fitting, and downloading and setting up the experiment data.

#### Build Docker Image

Build the latest docker image:

```bash
docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/model_fitting:$DOCKER_TAG -f containers/dockerfiles/model_fitting.Dockerfile containers
docker push cleanairdocker.azurecr.io/model_fitting:$DOCKER_TAG
```

#### Data setup

Make sure you are in the project directory `clean-air-infrastructure/`. We use the `urbanair` CLI to download and process the required training and prediction data. 

```bash
urbanair init production

urbanair experiment setup --experiment-root $CACHE_FOLDER $EXPERIMENT_NAME
```

Where `$EXPERIMENT_NAME` is a value from `$EXPERIMENT_NAMES`. This downloads and sets up the relevant infrastructure in `$CACHE_FOLDER`.

### 2) Running on cluster

To run on the cluster we use singularity. We first have to setup the folder structure on the cluster, setup the singularity image, move the required data over and then run models.

#### Setting up Cluster

We now set up docker/singularity and the required folder structure on the external cluster. `ssh` into the cluster and run:

```bash
mkdir cleanair
cd cleanair/
mkdir containers
cd containers

singularity pull --docker-login docker://cleanairdocker.azurecr.io/model_fitting:$DOCKER_TAG
```

This will prompt for a docker username and password. Please contact the `cleanair` owners for access. 

To run the models we will use slurm. Each experiment instance requires a separate batch file. For one instance:

```
touch sbatch_1.sh
```

and copy in:

```
#!/bin/bash
#SBATCH --job-name=mrdgp
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:0
#SBATCH --mem-per-cpu=32000


#SBATCH --output=logs/slurm_%j_,order_id-0.log

#########################
#
# Job: m_shallow_models,order_id-$i
#
#########################

##### Setup Environment

##### Run Command
cd ~/cleanair
# run script with arguments
singularity exec containers/model_fitting_$DOCKER_TAG.sif urbanair experiment batch $EXPERIMENT_NAME 0 1 --experiment-root <MODEL_FOLDER>
```

The last line will need to be updated for each instance that is being run. For example:

```
singularity exec containers/model_fitting_$DOCKER_TAG.sif urbanair experiment batch $EXPERIMENT_NAME 0 1 --experiment-root <MODEL_FOLDER>

singularity exec containers/model_fitting_$DOCKER_TAG.sif urbanair experiment batch $EXPERIMENT_NAME 1 1 --experiment-root <MODEL_FOLDER>

singularity exec containers/model_fitting_$DOCKER_TAG.sif urbanair experiment batch $EXPERIMENT_NAME 2 1 --experiment-root <MODEL_FOLDER>
```

etc.

#### Moving Data to the cluster

Move the model cache folder to `cleanair/` on the external cluster, e.g:

```bash
scp -i $CLUSTER_KEY -C -r $CACHE_FOLDER $CLUSTER_USER@$CLUSTER_ADDR:cleanair/
```

#### Running the models

To run the model fitting simply execute

```bash
sbatch sbatch_1.sh
```

and the appropriate command for each instance.

### 3) Updating Results

To update the results in the cleanair database we need to first move the results from the external cluster to the experiment directory:

```bash
#sync folder from cluster to CACHE_FOLDER/results
rsync -ra --relative --progress --compress -e "ssh -i $CLUSTER_KEY"  $CLUSTER_USER@$CLUSTER_ADDR:cleanair/$CACHE_DIR $CACHE_FOLDER
```

To push to the clean air cluster we need to run the below script for each instance:

```bash
cd ../../

#update clean air server
urbanair init production
urbanair model update results $MODEL $INSTANCE_FOLDER --cluster-id $CLUSTER_NAME
```

where `$INSTANCE_FOLDER` is the path to the instance folder and `$MODEL` is the model that was run by that instance.

