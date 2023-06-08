# Use custom tensorflow gpu runtime as a parent image
FROM cleanairdocker.azurecr.io/tf1_py37_gpu:latest

# Get the arg value of the git hash
ARG git_hash
ENV GIT_HASH=${git_hash}

# Stop git python errors
ENV GIT_PYTHON_REFRESH=quiet

RUN apt-get update
RUN apt-get -y install gcc g++

# Set the working directory to /app
WORKDIR /app

# set the version of cleanair
ARG urbanair_version
ENV SETUPTOOLS_SCM_PRETEND_VERSION ${urbanair_version}

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair
COPY scripts/ /app/scripts

# Install cleanair
RUN pip install '/app/cleanair[traffic, models]'
