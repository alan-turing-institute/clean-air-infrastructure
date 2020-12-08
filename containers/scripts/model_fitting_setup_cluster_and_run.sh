#load required variables
source ../../.secrets/model_fitting_settings.sh

#does not assume that the cluster is clean. if cleanair already exists it will delete and reset
#setup folder structure on cluster and pull most recent docker file
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    rm -rf cleanair
    mkdir logs
    mkdir cleanair
    cd cleanair
    mkdir containers    
    cd containers
    #singularity pull --docker-login docker://cleanairdocker.azurecr.io/model_fitting:latest 
    SINGULARITY_DOCKER_USERNAME=$DOCKER_USERNAME SINGULARITY_DOCKER_PASSWORD=$DOCKER_PASSWORD singularity pull docker://cleanairdocker.azurecr.io/model_fitting:latest

    cd ../
    touch sbatch.sh

    tee sbatch.sh << END
#!/bin/bash
#SBATCH --job-name=mrdgp
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
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
singularity exec containers/model_fitting_latest.sif urbanair model fit $MODEL $CACHE_DIR/
END
    
HERE

#move cache dir to cluster
scp -i $CLUSTER_KEY -C -r $CACHE_FOLDER $CLUSTER_USER@$CLUSTER_ADDR:cleanair/ 


#setup folder structure on cluster and pull most recent docker file
ssh -T -i $CLUSTER_KEY $CLUSTER_USER@$CLUSTER_ADDR  << HERE
    cd cleanair
    sbatch sbatch.sh
HERE



