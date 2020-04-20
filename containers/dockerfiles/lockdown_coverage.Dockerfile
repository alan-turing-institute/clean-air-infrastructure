# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair/
COPY uatraffic /app/uatraffic/

# Install any needed packages specified in requirements.txt
RUN pip install '/app/cleanair'
RUN pip install '/app/uatraffic'

# Create directory for storing models
RUN mkdir /experiments

# Copy the run script into the container
COPY entrypoints/lockdown_coverage.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "/app/lockdown_coverage.py"]