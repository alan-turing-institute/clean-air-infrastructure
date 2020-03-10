# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages specified in requirements.txt
RUN pip install '/app/cleanair[dashboard]'

# Copy the run script into the container
COPY entrypoints/run_dashboard.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "run_dashboard.py"]