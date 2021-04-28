# Use an official Python runtime as a parent image
FROM python:3.7

# Update certificates
RUN apt-get update \
    && apt-get install openssl \
    && apt-get install ca-certificates  cmake build-essential gfortran -y

# Dependencies for satellite processing
RUN apt-get install libeccodes0 -y

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair
COPY scripts/ /app/scripts

# set the version of cleanair
ARG urbanair_version
ENV SETUPTOOLS_SCM_PRETEND_VERSION ${urbanair_version}

# Install any needed packages specified in requirements.txt
RUN pip install '/app/cleanair[models,traffic]' pyopenssl
