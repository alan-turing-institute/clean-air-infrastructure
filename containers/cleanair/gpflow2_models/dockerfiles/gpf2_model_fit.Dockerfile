# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

RUN pip install azure-mgmt-storage
# Copy the gpflow2_models directory contents into the container
COPY cleanair/gpflow2_models /app/gpflow2_models

# Install any needed packages specified
RUN pip install -e /app/gpflow2_models
RUN pip check
