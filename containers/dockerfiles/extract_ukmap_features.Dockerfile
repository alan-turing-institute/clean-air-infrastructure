# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages specified in requirements.txt
RUN pip install /app/cleanair

# Copy the run script into the container
COPY entrypoints/feature_processing/extract_ukmap_features.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "extract_ukmap_features.py"]
