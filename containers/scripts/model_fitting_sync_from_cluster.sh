#load required variables
source ../../.secrets/model_fitting_settings.sh

#sync folder from cluster to CACHE_FOLDER/results
scp -i $CLUSTER_KEY -C -r $CLUSTER_USER@$CLUSTER_ADDR:cleanair/$CACHE_DIR/result/*.pkl $CACHE_FOLDER/result/

cd ../../

#update clean air server

urbanair init production
urbanair model update results $MODEL $CACHE_FOLDER --cluster-id $CLUSTER_NAME
