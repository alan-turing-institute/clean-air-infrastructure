# Use an official tensorflow gpu runtime as a parent image
FROM tensorflow/tensorflow:1.15.0-gpu-py3

# Get the arg value of the git hash
ARG git_hash
ENV GIT_HASH=${git_hash}

# Stop git python errors
ENV GIT_PYTHON_REFRESH=quiet

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages - note tensorflow-gpu 1.15.0 is already installed
RUN pip install gpflow==1.5.1
RUN pip install '/app/cleanair'

# Copy the run script into the container
COPY entrypoints/model_fitting/model_fitting.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "model_fitting.py"]

# To build this entrypoint:
# docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/mf -f containers/dockerfiles/model_fitting.Dockerfile containers

# To run the latest version of this entrypoint:
# docker run -it -e PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv) --rm -v $(pwd)/.secrets:/secrets cleanairdocker.azurecr.io/mf:latest --secretfile /secrets/.db_secrets_ad.json