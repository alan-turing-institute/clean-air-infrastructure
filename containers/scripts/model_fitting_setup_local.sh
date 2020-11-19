#load required variables
source ../../.secrets/model_fitting_settings.sh

#saving cache in urbanair requires an empty folder
if [ -d "$CACHE_FOLDER" ]; then
  # Take action if $DIR exists. #
  echo "OUTPUT_DIR $CACHE_FOLDER should not already exist"
  exit
fi

cd ../../

#Build and push current model fitting docker image
docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/model_fitting:latest -f containers/dockerfiles/model_fitting.Dockerfile containers

docker push cleanairdocker.azurecr.io/model_fitting:latest

#Download data for experiment and setup mrdgp 

urbanair init production

urbanair model data generate-config \
    --trainupto yesterday \
    --traindays 1 \
    --preddays 1 \
    --train-source laqn \
    --train-source satellite \
    --pred-source laqn \
    --species NO2 \
    --overwrite
    
    
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

urbanair model setup $MODEL --maxiter 10 --num-inducing-points 100

urbanair model data save-cache $CACHE_FOLDER
