#load required variables
source ../../.secrets/model_fitting_settings.sh

# exit when any command fails
set -e

#default values
SYNC=1
PUSH=1
HELP=0

#handle input flags
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --no-sync)
    SYNC=0
    shift # past argument
    ;;
    --no-push)
    PUSH=0
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
    echo '  --no-sync : Do not sync with cluster'
    echo '  --no-push : Do not push results to cleanair database'
    exit
fi

if [ "$SYNC" == '1' ]; then
    echo $LOCAL_EXPERIMENT_FOLDER_PATH
    #sync folder from cluster to LOCAL_EXPERIMENT_FOLDER_PATH/results
    rsync -ra --progress --compress -e "ssh -i $CLUSTER_KEY" $CLUSTER_USER@$CLUSTER_ADDR:cleanair_$TAG/$EXPERIMENT_FOLDER_NAME/ $LOCAL_EXPERIMENT_FOLDER_PATH
fi

cd ../../


#Every instance is acting as a 'mini-cache' folder, we have to push each individually
if [ "$PUSH" == '1' ]; then
    urbanair init production
    for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
        urbanair experiment update EXPERIMENT_NAME --experiment-root $LOCAL_EXPERIMENT_FOLDER_PATH
        urbanair experiment metrics EXPERIMENT_NAME --experiment-root $LOCAL_EXPERIMENT_FOLDER_PATH
    done
fi
