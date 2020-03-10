# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages specified in requirements.txt
RUN pip install '/app/cleanair[traffic]' 

# Copy the run script into the container
COPY entrypoints/features_scoot_readings.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "features_scoot_readings.py"]
