# Use an Ubuntu image with GDAL
FROM osgeo/gdal:ubuntu-full-latest

# Install psql, python and pip
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    postgresql \
    python3.7 \
    python3-pip

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /tmp/cleanair

# Upgrade cffi as container upgrades from Python3.6 to 3.7
RUN python3.7 -m pip install -U cffi

# Install cleanair
RUN python3.7 -m pip install '/tmp/cleanair[setup]'

# # # Copy the run script into the container
COPY entrypoints/setup/insert_static_datasets.py /app

# # # Run the entrypoint script when the container launches
ENTRYPOINT ["python3.7", "insert_static_datasets.py"]
