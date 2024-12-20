# Use an Ubuntu image with GDAL
FROM osgeo/gdal:ubuntu-full-latest

# Install psql, python and pip
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y postgresql python3-pip

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# set the version of cleanair
ARG urbanair_version
ENV SETUPTOOLS_SCM_PRETEND_VERSION ${urbanair_version}

# Install cleanair
RUN python -m pip install "/app/cleanair[geo]"

# Copy the run script into the container
COPY entrypoints/setup/insert_static_datasets.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "insert_static_datasets.py"]
