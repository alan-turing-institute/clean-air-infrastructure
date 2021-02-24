#load required variables
source ../../.secrets/model_fitting_settings.sh

# exit when any command fails
set -e

#default values
BUILD=0
SETUP=0
HELP=0

#handle input flags
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -b|--build)
    BUILD=1
    shift # past argument
    ;;
    -s|--setup)
    SETUP=1
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
    echo '  -b|--build : build and push docker file'
    echo '  -s|--setup : setup  and download all data for experiment instances'
    exit
fi

cd ../../

if [ "$BUILD" == '1' ]; then
    if [ $USE_GPU == 1 ]; then
        DOCKER_IMAGE='model_fitting_gpu'
    else
        DOCKER_IMAGE='model_fitting'
    fi

    echo "Building docker file $DOCKER_IMAGE.Dockerfile -> $DOCKER_IMAGE:$DOCKER_TAG"

    #Build and push current model fitting docker image
    docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/$DOCKER_IMAGE:$DOCKER_TAG -f containers/dockerfiles/$DOCKER_IMAGE.Dockerfile containers
    docker push cleanairdocker.azurecr.io/$DOCKER_IMAGE:$DOCKER_TAG
fi


if [ "$SETUP" == '1' ]; then
    echo 'Setting up experiment'
    #saving cache in urbanair requires an empty folder
    if [ -d "$CACHE_FOLDER" ]; then
      # Take action if $DIR exists. #
      echo "OUTPUT_DIR $CACHE_FOLDER should not already exist"
      exit
    fi

    #Download data for experiment and setup mrdgp 
    urbanair init production

    for EXPERIMENT_NAME in ${EXPERIMENT_NAMES[@]}; do
        echo "Processing $EXPERIMENT_NAME"
        urbanair experiment setup --experiment-root $CACHE_FOLDER $EXPERIMENT_NAME
    done
fi
