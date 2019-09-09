# Use an Ubuntu image with GDAL
FROM osgeo/gdal:ubuntu-full-latest

# # Install jq for parsing json files
# ENV DEBIAN_FRONTEND=noninteractive
# RUN apt-get update && apt-get install -y \
#     apt-transport-https \
#     libpq-dev \
#     postgresql \
#     python3 \
#     python3-pip

# Install psql, python and pip
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    postgresql \
    python3 \
    python3-pip

# Upgrade pip
RUN pip3 install --upgrade pip

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container
# -> this reduces rebuilding by separating code changes from dependency changes
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Copy the run script into the container
COPY entrypoints/upload_static_dataset.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python3", "upload_static_dataset.py"]
