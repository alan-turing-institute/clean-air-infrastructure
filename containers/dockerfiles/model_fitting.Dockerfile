# Use custom tensorflow runtime as a parent image
FROM --platform=linux/amd64 cleanairdocker.azurecr.io/tf1_py37:latest

# Get the arg value of the git hash
ARG git_hash
ENV GIT_HASH=${git_hash}

# Stop git python errors
ENV GIT_PYTHON_REFRESH=quiet

RUN apt-get -y install gcc g++

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY /containers/cleanair /app/cleanair
COPY /containers/scripts/ /app/scripts

# helps prevent this issue when running tensorflow:
# https://developers.google.com/protocol-buffers/docs/news/2022-05-06#python-updates
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python


# Install cleanair
RUN pip install  --no-cache-dir '/app/cleanair'