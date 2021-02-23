#load required variables
source ../../.secrets/model_fitting_settings.sh


#does not assume that the cluster is clean. if cleanair already exists it will delete and reset
#setup folder structure on cluster and pull most recent docker file
#we run singularity pull inside a cluster node because pearl sometimes fails on the login node

echo 'Setting up cluster and pulling docker image'


if [ 1 -ne 0 ]; then
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    rm -rf cleanair
    mkdir -p logs
    mkdir cleanair
    mkdir cleanair/logs
    cd cleanair
    mkdir containers    
    cd containers
    SINGULARITY_DOCKER_USERNAME=$DOCKER_USERNAME SINGULARITY_DOCKER_PASSWORD=$DOCKER_PASSWORD bash -c 'srun --export=ALL singularity pull -F docker://cleanairdocker.azurecr.io/model_fitting:$DOCKER_TAG'

HERE
fi



echo 'Moving datafiles to cluster'


#for each experiment, get the number of instances and create the relevent sbatch files
for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
    #TODO: make an urbanair command to return the number of instances
    #Work around for now until urbanair command issue is completed
    NUM_INSTANCES=$(find $CACHE_FOLDER/$EXPERIMENT_NAME -mindepth 1 -maxdepth 1 -type d | wc -l)

    #for every instance create an sbatch file
    #seq generates numbers from 1 to n, and urbanair batch counts from 0 hence we -1
    for i in $(seq $NUM_INSTANCES); do

ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair
    touch sbatch_${EXPERIMENT_NAME}_$i.sh

    tee sbatch_${EXPERIMENT_NAME}_$i.sh << END
#!/bin/bash
#SBATCH --job-name=mrdgp
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:0
#SBATCH --mem-per-cpu=32000


#SBATCH --output=logs/slurm_%j__mrdgp,order_id-0.log

#########################
#
# Job: m_shallow_models,order_id-$i
#
#########################

##### Setup Environment

##### Run Command
cd ~/cleanair
# run script with arguments
#singularity exec containers/model_fitting_$DOCKER_TAG.sif urbanair model fit $MODEL $CACHE_DIR/
singularity exec containers/model_fitting_$DOCKER_TAG.sif urbanair experiment batch $EXPERIMENT_NAME $(($i-1)) 1 --experiment-root $CACHE_DIR/

END
    
HERE

    done

done

echo 'Moving cache dir to cluster'
scp -i $CLUSTER_KEY -C -r $CACHE_FOLDER $CLUSTER_USER@$CLUSTER_ADDR:cleanair/ 

for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do

    #TODO: make an urbanair command to return the number of instances
    #Work around for now until urbanair command issue is completed
    NUM_INSTANCES=$(find $CACHE_FOLDER/$EXPERIMENT_NAME -mindepth 1 -maxdepth 1 -type d | wc -l)

    echo 'Run every instance'
    for i in $(seq $NUM_INSTANCES); do

ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair
    sbatch sbatch_${EXPERIMENT_NAME}_$i.sh
HERE

    done

done



