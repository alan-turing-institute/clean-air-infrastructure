# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair/
COPY odysseus /app/odysseus/

# Install any needed packages specified in requirements.txt
RUN pip install /app/cleanair
RUN pip install /app/odysseus

# Copy the run script into the container
COPY entrypoints/odysseus/lockdown_baseline_comparison.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "lockdown_baseline_comparison.py"]