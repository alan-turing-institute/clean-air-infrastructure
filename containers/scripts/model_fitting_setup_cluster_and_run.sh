#load required variables
source ../../.secrets/model_fitting_settings.sh

# exit when any command fails
set -e

#default values
DRY=0
NO_SETUP=0
HELP=0

#handle input flags
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --dry)
    DRY=1
    shift # past argument
    ;;
    --no-setup)
    NO_SETUP=1
    shift # past argument
    ;;
    --help)
    HELP=1
    shift # past argument
    ;;
esac
done

if [ "$HELP" == '1' ]; then
    echo 'Help:'
    echo '  --dry : Do not run sbatch on cluster'
    echo '  --no-setup : Do not setup cluster folders and move experiment instances to cluster'
    exit
fi


if [ $USE_GPU == 1 ]; then
    DOCKER_IMAGE='model_fitting_gpu'
    GPU_NUM=$NUM_GPUS
else
    DOCKER_IMAGE='model_fitting'
    GPU_NUM=0
fi

#helper functions

function setup_cluster() {
#does not assume that the cluster is clean. if cleanair already exists it will delete and reset
#setup folder structure on cluster and pull most recent docker file
#we run singularity pull inside a cluster node because pearl sometimes fails on the login node
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    rm -rf cleanair
    mkdir -p logs
    mkdir cleanair
    mkdir cleanair/logs
    cd cleanair
    mkdir containers    
    cd containers
    SINGULARITY_DOCKER_USERNAME=$DOCKER_USERNAME SINGULARITY_DOCKER_PASSWORD=$DOCKER_PASSWORD bash -c 'srun --export=ALL singularity pull -F docker://cleanairdocker.azurecr.io/$DOCKER_IMAGE:$DOCKER_TAG'
HERE
}

function create_sbatch_files() {
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair
    touch sbatch_${1}_$2.sh

    tee sbatch_${1}_$2.sh << END
#!/bin/bash
#SBATCH --job-name=$1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:$GPU_NUM


#SBATCH --output=logs/slurm_%j__$1,order_id-$2.log

#########################
#
# Job: m_shallow_models,order_id-$2
#
#########################

##### Setup Environment

##### Run Command
cd ~/cleanair
# run script with arguments
singularity exec containers/${DOCKER_IMAGE}_$DOCKER_TAG.sif urbanair experiment batch $1 $(($2-1)) 1 --experiment-root $CACHE_DIR/

END

HERE
}

function run_sbatch() {
    ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair
    sbatch sbatch_${1}_$2.sh
HERE
}


if [ "$NO_SETUP" == '0' ]; then 

    echo 'Setting up cluster and pulling docker image'

    setup_cluster

    echo 'Moving datafiles to cluster'

    #for each experiment, get the number of instances and create the relevent sbatch files
    for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
        #TODO: make an urbanair command to return the number of instances
        #Work around for now until urbanair command issue is completed
        NUM_INSTANCES=$(find $CACHE_FOLDER/$EXPERIMENT_NAME -mindepth 1 -maxdepth 1 -type d | wc -l)

        if [ $NUM_INSTANCES == 0 ]; then
            echo "No instances found in $CACHE_FOLDER/$EXPERIMENT_NAME"
        else
            #for every instance create an sbatch file
            #seq generates numbers from 1 to n, and urbanair batch counts from 0 hence we -1
            for i in $(seq $NUM_INSTANCES); do
                create_sbatch_files $EXPERIMENT_NAME $i
            done
        fi
    done

fi

if [ "$DRY" == '0' ]; then 
    echo 'Moving cache dir to cluster'
    scp -i $CLUSTER_KEY -C -r $CACHE_FOLDER $CLUSTER_USER@$CLUSTER_ADDR:cleanair/ 

    for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
        #TODO: make an urbanair command to return the number of instances
        #Work around for now until urbanair command issue is completed
        NUM_INSTANCES=$(find $CACHE_FOLDER/$EXPERIMENT_NAME -mindepth 1 -maxdepth 1 -type d | wc -l)

        if [ $NUM_INSTANCES == 0 ]; then
            echo "No instances found in $CACHE_FOLDER/$EXPERIMENT_NAME"
        else
            echo "Run every instance in $CACHE_FOLDER/$EXPERIMENT_NAME"
            for i in $(seq $NUM_INSTANCES); do
                run_sbatch $EXPERIMENT_NAME $i
            done
        fi

    done
fi



