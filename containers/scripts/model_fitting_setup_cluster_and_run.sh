#load required variables
source ../../.secrets/model_fitting_settings.sh

echo $CACHE_DIR
exit()

#does not assume that the cluster is clean. if cleanair already exists it will delete and reset
#setup folder structure on cluster and pull most recent docker file
#we run singularity pull inside a cluster node because pearl sometimes fails on the login node
echo 'Setting up cluster and pulling docker image'
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    rm -rf cleanair
    mkdir -p logs
    mkdir cleanair
    mkdir cleanair/logs
    cd cleanair
    mkdir containers    
    cd containers
    SINGULARITY_DOCKER_USERNAME=$DOCKER_USERNAME SINGULARITY_DOCKER_PASSWORD=$DOCKER_PASSWORD bash -c 'srun -n 1 --gres=gpu:0 --export=ALL singularity pull -F docker://cleanairdocker.azurecr.io/model_fitting:latest'

HERE

NUM_INSTANCES=1


echo 'Moving datafiles to cluster'

for i in $(seq $NUM_INSTANCES);
do

ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair
    touch sbatch_$i.sh

    tee sbatch_$i.sh << END
#!/bin/bash
#SBATCH --job-name=mrdgp
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:0


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
#singularity exec containers/model_fitting_latest.sif urbanair model fit $MODEL $CACHE_DIR/
singularity exec containers/model_fitting_latest.sif urbanair experiment batch dgp_vary_static_feature $i 1 --experiment-root $CACHE_DIR/

END
    
HERE

done


echo 'Moving cache dir to cluster'
#move cache dir to cluster
scp -i $CLUSTER_KEY -C -r $CACHE_FOLDER $CLUSTER_USER@$CLUSTER_ADDR:cleanair/ 

echo 'Runnign experiments'
for i in $(seq $NUM_INSTANCES);
do

#setup folder structure on cluster and pull most recent docker file
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair
    sbatch sbatch_$i.sh
HERE

done



