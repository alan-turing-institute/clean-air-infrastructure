# # Use an Ubuntu image with GDAL
# FROM osgeo/gdal:ubuntu-full-latest

# # Install psql, python and pip
# ENV DEBIAN_FRONTEND=noninteractive
# RUN apt-get update && apt-get install -y \
#     postgresql \
#     python3 \
#     python3-pip

# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages specified in requirements.txt
RUN pip install /app/cleanair

# Copy the run script into the container
COPY entrypoints/setup/process_rectgrid.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python3", "process_rectgrid.py"]
