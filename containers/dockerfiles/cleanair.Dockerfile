# Use an official Python runtime as a parent image
FROM python:3.10

# Update certificates
RUN apt update \
    && apt install -y \
        build-essential \
        ca-certificates \
        cmake \
        gfortran \
        libeccodes0 \
        libgeos-dev


# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair
COPY scripts/ /app/scripts

# set the version of cleanair
ARG urbanair_version

# Install packages
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CLEANAIR=${urbanair_version} pip install "/app/cleanair" pyopenssl
