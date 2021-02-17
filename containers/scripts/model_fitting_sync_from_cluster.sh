#load required variables
source ../../.secrets/model_fitting_settings.sh

#sync folder from cluster to CACHE_FOLDER/results
rsync -ra --relative --progress --compress -e "ssh -i $CLUSTER_KEY" $CLUSTER_USER@$CLUSTER_ADDR:cleanair/$CACHE_DIR $CACHE_FOLDER

cd ../../

#update clean air server
urbanair init production
urbanair model update results $MODEL $CACHE_FOLDER --cluster-id $CLUSTER_NAME
