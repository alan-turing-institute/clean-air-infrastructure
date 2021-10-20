#load required variables
source ../../.secrets/model_fitting_settings.sh

# exit when any command fails
set -e

#default values
DRY=0
NO_SETUP=0
HELP=0
LOCAL=0

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
    --local)
    LOCAL=1
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
    echo '  --local : Run locally'
    exit
fi


if [ $USE_GPU == 1 ]; then
    DOCKER_IMAGE='model_fitting_gpu_cluster'
    GPU_NUM=$NUM_GPUS
else
    DOCKER_IMAGE='model_fitting'
    GPU_NUM=0
fi

JOBS_PATH=$LOCAL_EXPERIMENT_FOLDER_PATH/jobs


#helper functions

function setup_cluster() {
#does not assume that the cluster is clean. if cleanair already exists it will delete and reset
#setup folder structure on cluster and pull most recent docker file
#we run singularity pull inside a cluster node because pearl sometimes fails on the login node
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    rm -rf cleanair_$TAG
    mkdir -p logs
    mkdir cleanair_$TAG
    mkdir cleanair_$TAG/logs
    cd cleanair_$TAG
    mkdir containers    
    cd containers
    SINGULARITY_DOCKER_USERNAME=$DOCKER_USERNAME SINGULARITY_DOCKER_PASSWORD=$DOCKER_PASSWORD bash -c 'srun --export=ALL singularity pull -F docker://cleanairdocker.azurecr.io/$DOCKER_IMAGE:$DOCKER_TAG'
HERE
}



function create_local_cluster_folder() {
    echo "Jobs path: $JOBS_PATH"
    rm -rf $JOBS_PATH
    mkdir -p $JOBS_PATH
}


function create_sbatch_files() {
    touch $JOBS_PATH/sbatch_${1}_$2.sh
    tee $JOBS_PATH/sbatch_${1}_$2.sh << END
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
cd ~/cleanair_$TAG
# run script with arguments
singularity exec containers/${DOCKER_IMAGE}_$DOCKER_TAG.sif urbanair experiment batch $1 $(($2-1)) 1 --experiment-root $EXPERIMENT_FOLDER_NAME/

END

}

function run_sbatch() {
    ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair_$TAG
    sh ./run_all.sh
HERE
}

function move_sbatch_to_cluster() {
    scp -i $CLUSTER_KEY -C $JOBS_PATH/*.sh $CLUSTER_USER@$CLUSTER_ADDR:cleanair_$TAG/ 
}

function create_sbatch_run_script() {
    touch $JOBS_PATH/run_all.sh
    for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
        #TODO: make an urbanair command to return the number of instances
        #Work around for now until urbanair command issue is completed
        NUM_INSTANCES=$(find $LOCAL_EXPERIMENT_FOLDER_PATH/$EXPERIMENT_NAME -mindepth 1 -maxdepth 1 -type d | wc -l)

        if [ $NUM_INSTANCES == 0 ]; then
            echo "No instances found in $LOCAL_EXPERIMENT_FOLDER_PATH/$EXPERIMENT_NAME"
        else
            #add newline
            for i in $(seq $NUM_INSTANCES); do
                echo "sbatch sbatch_${EXPERIMENT_NAME}_$i.sh" >> $JOBS_PATH/run_all.sh
            done
        fi
    done
}


if [ "$NO_SETUP" == '0' ]; then 

    echo 'Setting up cluster and pulling docker image'

    setup_cluster
    create_local_cluster_folder
    create_sbatch_run_script

    echo 'Moving datafiles to cluster'

    #for each experiment, get the number of instances and create the relevent sbatch files
    for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
        #TODO: make an urbanair command to return the number of instances
        #Work around for now until urbanair command issue is completed
        NUM_INSTANCES=$(find $LOCAL_EXPERIMENT_FOLDER_PATH/$EXPERIMENT_NAME -mindepth 1 -maxdepth 1 -type d | wc -l)

        if [ $NUM_INSTANCES == 0 ]; then
            echo "No instances found in $LOCAL_EXPERIMENT_FOLDER_PATH/$EXPERIMENT_NAME"
        else
            #for every instance create an sbatch file
            #seq generates numbers from 1 to n, and urbanair batch counts from 0 hence we -1
            for i in $(seq $NUM_INSTANCES); do
                create_sbatch_files $EXPERIMENT_NAME $i
            done
        fi
    done

    move_sbatch_to_cluster
fi

if [ "$DRY" == '0' ]; then 
    echo 'Moving cache dir to cluster'
    scp -i $CLUSTER_KEY -C -r $LOCAL_EXPERIMENT_FOLDER_PATH $CLUSTER_USER@$CLUSTER_ADDR:cleanair_$TAG/ 

    run_sbatch

    #clean up
    rm -rf $JOBS_PATH
fi


if [ "$LOCAL" == '1' ]; then 

    for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
        #TODO: make an urbanair command to return the number of instances
        #Work around for now until urbanair command issue is completed
        NUM_INSTANCES=$(find $LOCAL_EXPERIMENT_FOLDER_PATH/$EXPERIMENT_NAME -mindepth 1 -maxdepth 1 -type d | wc -l)

        if [ $NUM_INSTANCES == 0 ]; then
            echo "No instances found in $LOCAL_EXPERIMENT_FOLDER_PATH/$EXPERIMENT_NAME"
        else
            #for every instance create an sbatch file
            #seq generates numbers from 1 to n, and urbanair batch counts from 0 hence we -1
            for i in $(seq $NUM_INSTANCES); do
                echo "Running $EXPERIMENT_NAME instance $i/$NUM_INSTANCES"
                urbanair experiment batch $EXPERIMENT_NAME $(($i-1)) 1 --experiment-root $LOCAL_EXPERIMENT_FOLDER_PATH/
            done
        fi
    
    done
fi



