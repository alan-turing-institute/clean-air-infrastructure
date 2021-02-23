#load required variables
source ../../.secrets/model_fitting_settings.sh

#saving cache in urbanair requires an empty folder
if [ -d "$CACHE_FOLDER" ]; then
  # Take action if $DIR exists. #
  echo "OUTPUT_DIR $CACHE_FOLDER should not already exist"
  exit
fi

cd ../../


#To build docker use --build tag as the first argment
if [ $# -ne 0 ]; then

    if [ "$1" == '--build' ]; then

        if [ -d "$CACHE_FOLDER" ]; then

            #Build and push current model fitting docker image
            docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/model_fitting:latest -f containers/dockerfiles/model_fitting.Dockerfile containers

            docker push cleanairdocker.azurecr.io/model_fitting:latest

        fi
    fi
fi

#Download data for experiment and setup mrdgp 
urbanair init production

for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
    echo "Processing $EXPERIMENT_NAME"
    urbanair experiment setup --experiment-root $CACHE_FOLDER $EXPERIMENT_NAME
done
