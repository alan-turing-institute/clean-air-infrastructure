# Use an official Python runtime as a parent image
FROM cleanairdocker.azurecr.io/tf2_py37_gpu:latest

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair/
COPY odysseus /app/odysseus/

# set the version of cleanair
ARG urbanair_version
ENV SETUPTOOLS_SCM_PRETEND_VERSION ${urbanair_version}

# Install any needed packages specified in requirements.txt
RUN pip install /app/cleanair
RUN pip install /app/odysseus
