# Use an Ubuntu image with GDAL
FROM osgeo/gdal:ubuntu-full-latest

# Install psql, python and pip
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    postgresql \
    python3.7 \
    python3-pip

# Upgrade pip
# RUN pip3 install --upgrade pip

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /tmp/cleanair

# # # Install any needed packages specified in requirements.txt
RUN python3.7 -m pip install /tmp/cleanair

# # # Copy the run script into the container
COPY entrypoints/process_static_dataset.py /app

# # # Run the entrypoint script when the container launches
ENTRYPOINT ["python3.7", "process_static_dataset.py"]
